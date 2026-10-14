"""The milestone gate: run the tests, check requirement coverage, record the results, rebuild the page.

Results go in docs/gates/milestone-N.md. The tool writes the test and coverage
sections; the skill fills in the architecture check, the reviews and the
author's choices. Re-running the gate after fixes replaces only the tool's part.
"""

import re
import subprocess
from pathlib import Path

from tortoise.page import build_page
from tortoise.plan import read_milestones
from tortoise.project import load_state, save_state, write_safely
from tortoise.stages import code_fingerprint

OUTPUT_LINES_KEPT = 30
REQUIREMENT = re.compile(r"\bR(\d+)\b")
SKILL_SECTIONS = "## Architecture check\n\nNot recorded yet.\n\n## Reviews\n\nNot recorded yet.\n\n## Author's choices\n\nNot recorded yet.\n"


def run_gate(root: Path) -> dict:
    state = load_state(root)
    if state["stage"] != "gate":
        raise ValueError("tortoise gate only runs at a milestone gate; finish the build and run tortoise stage next")
    milestone = state["milestone"]
    review_base = state["approvals"][-1]["tag"]

    command = state["test_command"]
    # The test command is the author's own, set once in tortoise.json, so it runs through the shell
    # from the project folder, just as the author would type it.
    run = subprocess.run(command, shell=True, cwd=root, capture_output=True, text=True)
    passed = run.returncode == 0
    output = "\n".join((run.stdout + run.stderr).rstrip("\n").split("\n")[-OUTPUT_LINES_KEPT:])
    verdict = "**Passed:**" if passed else "**Failed:**"

    tool_part = (
        f"# Milestone {milestone} gate\n\n"
        f"Reviews of this milestone compare against `{review_base}`, the last approval.\n\n"
        f"## Tests\n\n{verdict} `{command}` finished with exit code {run.returncode}.\n\n"
        f"```\n{output}\n```\n\n"
        f"## Requirement coverage\n\n{_coverage(root)}\n"
        f"## Tasks\n\n{_unticked_tasks(root, milestone)}\n"
    )
    path = root / "docs" / "gates" / f"milestone-{milestone}.md"
    path.parent.mkdir(exist_ok=True)
    previous = path.read_text() if path.exists() else ""
    kept = previous[previous.index("## Architecture check"):] if "## Architecture check" in previous else SKILL_SECTIONS
    write_safely(path, tool_part + kept)
    state["last_gate"] = {"milestone": milestone, "passed": passed, "fingerprint": code_fingerprint(root)}
    save_state(root, state)
    build_page(root)
    return {"passed": passed, "exit_code": run.returncode, "review_base": review_base, "path": path}


def _coverage(root: Path) -> str:
    """Requirements in the spec that no task names, and requirements tasks name that the spec lacks."""
    spec = _read(root / "docs" / "SPEC.md")
    plan = _read(root / "docs" / "PLAN.md")
    in_spec = {int(number) for number in REQUIREMENT.findall(spec)}
    named = set()
    for line in plan.split("\n"):
        if "Requirements:" in line:
            named.update(int(number) for number in REQUIREMENT.findall(line.split("Requirements:", 1)[1]))
    gaps = [f"- R{number} is in SPEC.md but no task in PLAN.md names it." for number in sorted(in_spec - named)]
    gaps += [f"- R{number} is named by a task in PLAN.md but is not in SPEC.md." for number in sorted(named - in_spec)]
    if not gaps:
        return "Every requirement in SPEC.md is named by a task in PLAN.md.\n"
    return "\n".join(gaps) + "\n"


def _unticked_tasks(root: Path, number: int) -> str:
    """Which of this milestone's tasks in PLAN.md are not ticked yet."""
    milestone = next((m for m in read_milestones(_read(root / "docs" / "PLAN.md")) if m.number == number), None)
    if milestone is None:
        return f"PLAN.md has no milestone {number}.\n"
    unticked = [text for ticked, text in milestone.tasks if not ticked]
    if not unticked:
        return f"Every task in milestone {number} is ticked ({milestone.done} of {milestone.total}).\n"
    listed = "\n".join(f"- {text}" for text in unticked)
    return f"{milestone.done} of {milestone.total} tasks in milestone {number} are ticked. Not ticked:\n\n{listed}\n"


def _read(path: Path) -> str:
    return path.read_text() if path.exists() else ""
