"""Moving a project through its stages and recording the author's approvals.

Build and the milestone gate repeat once per milestone in docs/PLAN.md. Each
approval commits the approved work and tags the commit, so later reviews can
compare against it.
"""

import fnmatch
import os
import re
import subprocess
import tempfile
from pathlib import Path

from tortoise.plan import read_milestones
from tortoise.project import STAGES, load_state, save_state, write_safely

NEEDS_APPROVAL = {"spec", "architecture", "plan", "gate", "final-checks"}
ORDER = list(STAGES)
# File names that usually hold secrets; approving never commits one of these for the first time.
SECRET_NAMES = (".env", ".env.*", "*.pem", "*.key", "*.p12", "*.pfx", "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519")
SAFE_NAMES = (".env.example", ".env.sample", ".env.template")


def stage_name(state: dict) -> str:
    """The current stage in plain words, such as "Build, milestone 1 of 3"."""
    stage = state["stage"]
    if stage in ("build", "gate"):
        return f"{STAGES[stage]}, milestone {state['milestone']} of {state['milestones']}"
    return STAGES[stage]


def describe(state: dict) -> str:
    """The stage name, plus a note when the stage still needs the author's approval."""
    text = stage_name(state)
    if state["stage"] in NEEDS_APPROVAL and not _approved(state):
        text += " (needs your approval before moving on)"
    return text


def advance(root: Path) -> dict:
    """Move to the next stage, refusing when the current stage still needs the author's approval."""
    state = load_state(root)
    stage = state["stage"]
    if stage == "done":
        raise ValueError("The project is done; there is no next stage")
    if stage in NEEDS_APPROVAL and not _approved(state):
        raise ValueError(f"{STAGES[stage]} needs your approval first: run tortoise approve")

    if stage == "plan":
        milestones = read_milestones(_read(root / "docs" / "PLAN.md"))
        if not milestones:
            raise ValueError('PLAN.md has no milestones; add headings such as "## Milestone 1: Records"')
        state.update(stage="build", milestone=1, milestones=len(milestones))
    elif stage == "gate" and state["milestone"] < state["milestones"]:
        state.update(stage="build", milestone=state["milestone"] + 1)
    else:
        state["stage"] = ORDER[ORDER.index(stage) + 1]
    save_state(root, state)
    return state


def approve(root: Path, today: str, despite_failing_tests: str | None = None) -> dict:
    """Record the author's approval of the current stage, then commit and tag the approved work.

    Gate and final-checks approvals commit every changed file; the others commit only docs/ and
    tortoise.json.
    """
    state = load_state(root)
    stage = state["stage"]
    if stage not in NEEDS_APPROVAL:
        raise ValueError(f"{STAGES[stage]} does not need approval")
    if _approved(state):
        raise ValueError(f"{stage_name(state)} is already approved")
    if stage == "gate":
        _check_gate(state, despite_failing_tests)
        if state["last_gate"].get("fingerprint") != code_fingerprint(root):
            raise ValueError("the code has changed since the gate ran; run tortoise gate again")

    # Gates and final checks commit all the work (code, tests, the README); the document stages commit
    # only docs/ and tortoise.json, so unrelated work in progress is left alone.
    paths = [] if stage in ("gate", "final-checks") else ["docs", "tortoise.json"]
    _refuse_new_secret_files(root, paths)

    tag = f"tortoise/milestone-{state['milestone']}" if stage == "gate" else f"tortoise/{stage}"
    if _git_succeeds(root, "rev-parse", "--quiet", "--verify", f"refs/tags/{tag}"):
        raise ValueError(f"the tag {tag} already exists; delete it or ask why it is there before approving")
    approval = {"stage": stage, "date": today, "tag": tag}
    if stage == "gate":
        approval["milestone"] = state["milestone"]
        if despite_failing_tests:
            approval["despite_failing_tests"] = despite_failing_tests.strip()
    before = (root / "tortoise.json").read_text()
    gate_file = root / "docs" / "gates" / f"milestone-{state.get('milestone')}.md"
    gate_before = gate_file.read_text() if despite_failing_tests else None
    if despite_failing_tests:
        _record_override(gate_file, approval["despite_failing_tests"])
    state["approvals"].append(approval)
    if stage == "final-checks":
        # Nothing follows final checks, so approving them finishes the project in the same commit.
        state["stage"] = "done"
    save_state(root, state)
    try:
        _git(root, "add", "--all", *paths)
        # A document approval names its paths, so files the author staged elsewhere stay out of the commit.
        _git(root, "commit", "--quiet", "-m", f"chore(tortoise): approve {tag.split('/')[1]}", "--", *paths)
    except ValueError:
        # Undo the staging and the recorded approval, so a refused commit leaves things as they were.
        _git_succeeds(root, "reset", "--quiet", "--", *(paths or ["."]))
        write_safely(root / "tortoise.json", before)
        if gate_before is not None:
            write_safely(gate_file, gate_before)
        raise
    try:
        _git(root, "tag", tag)
    except ValueError as error:
        raise ValueError(f"the approval is committed but tagging failed ({error}); run: git tag {tag}") from error
    return approval


def code_fingerprint(root: Path) -> str | None:
    """A fingerprint of every file except docs/ and tortoise.json, which the gate and the skill write.

    Built in a throwaway git index, so the author's staging area is untouched. None outside git.
    """
    with tempfile.TemporaryDirectory() as folder:
        environment = {**os.environ, "GIT_INDEX_FILE": os.path.join(folder, "index")}
        add = subprocess.run(
            ["git", "add", "--all", "--", ".", ":(exclude)docs", ":(exclude)tortoise.json"],
            cwd=root, env=environment, capture_output=True, text=True,
        )
        if add.returncode != 0:
            return None
        tree = subprocess.run(["git", "write-tree"], cwd=root, env=environment, capture_output=True, text=True)
        return tree.stdout.strip() or None


def _check_gate(state: dict, despite_failing_tests: str | None) -> None:
    """A gate is approved only after it has run, and only with passing tests unless the author gives a reason."""
    last = state.get("last_gate")
    if not last or last["milestone"] != state["milestone"]:
        raise ValueError("this milestone's gate has not run yet; run tortoise gate first")
    if despite_failing_tests is not None:
        if not despite_failing_tests.strip():
            raise ValueError("approving despite failing tests needs a reason")
        if last["passed"]:
            raise ValueError("the tests passed at the last gate run, so no override is needed")
    elif not last["passed"]:
        raise ValueError(
            "the tests failed at the last gate run. Fix the code, or with your agreement the test, then run "
            'tortoise gate again; or approve with --despite-failing-tests "reason"'
        )


def _record_override(gate_file: Path, reason: str) -> None:
    """Note the author's reason in the gate file's "Author's choices" section."""
    text = gate_file.read_text()
    line = f"- Approved despite failing tests: {reason}\n"
    placeholder = "## Author's choices\n\nNot recorded yet.\n"
    if placeholder in text:
        text = text.replace(placeholder, "## Author's choices\n\n" + line)
    else:
        text = text.rstrip("\n") + "\n" + line
    write_safely(gate_file, text)


def _approved(state: dict) -> bool:
    for approval in state["approvals"]:
        if approval["stage"] == state["stage"] and approval.get("milestone") == (
            state.get("milestone") if state["stage"] == "gate" else None
        ):
            return True
    return False


def committed_files(root: Path, tag: str) -> list[str]:
    """The files an approval's commit changed, so the author can see exactly what went in."""
    return sorted(filter(None, _git(root, "show", "--name-only", "--format=", tag).split("\n")))


def mark_new_files_for_review(root: Path) -> list[str]:
    """Mark new files as intended to add, so `git diff <review base>` shows them to reviewers.

    Their contents are not staged. Secret-looking files are never marked, so a reviewer never reads them.
    Outside git there is nothing to mark.
    """
    if not _git_succeeds(root, "rev-parse", "--git-dir"):
        return []
    new = [path for path in _git(root, "ls-files", "--others", "--exclude-standard").split("\n")
           if path and not _looks_secret(path)]
    if new:
        _git(root, "add", "--intent-to-add", "--", *new)
    return new


def _looks_secret(path: str) -> bool:
    name = Path(path).name
    return name not in SAFE_NAMES and any(fnmatch.fnmatch(name, pattern) for pattern in SECRET_NAMES)


def _refuse_new_secret_files(root: Path, paths: list[str]) -> None:
    """Refuse when the approval would commit a secret-looking file git is not already tracking."""
    untracked = _git(root, "ls-files", "--others", "--exclude-standard", "--", *paths).split("\n")
    secrets = [path for path in untracked if path and _looks_secret(path)]
    if secrets:
        raise ValueError(
            f"these look like secret files and would be committed: {', '.join(secrets)}. "
            "Add them to .gitignore, or commit them yourself if they are safe to share"
        )


def _git_succeeds(root: Path, *arguments: str) -> bool:
    return subprocess.run(["git", *arguments], cwd=root, capture_output=True).returncode == 0


def _git(root: Path, *arguments: str) -> str:
    try:
        return subprocess.run(["git", *arguments], cwd=root, capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError as error:
        if "not a git repository" in error.stderr:
            raise ValueError("approving commits your work, so the project must be a git repository") from error
        raise ValueError(f"git {arguments[0]} failed: {error.stderr.strip()}") from error


def _read(path: Path) -> str:
    return path.read_text() if path.exists() else ""


