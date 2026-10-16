import json
import re
import subprocess

import pytest

from tortoise.decisions import add_decision, settle_decision
from tortoise.gate import run_gate
from tortoise.project import init_project
from tortoise.stages import advance, approve, describe

PLAN = """# Plan

## Milestone 1: Records

- Task 1: store lab results. Requirements: R1

## Milestone 2: Charts

- Task 2: draw the chart. Requirements: R2
"""


def git(root, *arguments):
    return subprocess.run(["git", *arguments], cwd=root, capture_output=True, text=True, check=True).stdout.strip()


@pytest.fixture
def project(tmp_path):
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "config", "user.name", "Test Author")
    git(tmp_path, "config", "user.email", "author@example.com")
    init_project(tmp_path, name="Lab tracker", test_command="true")
    return tmp_path


def state(root):
    return json.loads((root / "tortoise.json").read_text())


def move_to(root, stage):
    """Walk the project forward to a stage, approving whatever needs it on the way."""
    while state(root)["stage"] != stage:
        try:
            advance(root)
        except ValueError:
            if state(root)["stage"] == "plan":
                (root / "docs" / "PLAN.md").write_text(PLAN)
            if state(root)["stage"] == "gate":
                run_gate(root)
            approve(root, today="2026-10-14")
            advance(root)


def test_stages_without_an_approval_move_straight_on(project):
    advance(project)

    assert state(project)["stage"] == "ideas"
    assert describe(state(project)) == "Ideas (needs your approval before moving on)"


def test_approving_the_ideas_fixes_the_intent_once_every_decision_is_settled(project):
    advance(project)
    log = project / "docs" / "DECISIONS.md"
    add_decision(log, {"question": "Which approach?", "options": ["one page", "an app"], "choice": "one page",
                       "reason": "one user", "proposed_by": "Claude (claude-opus-5-5)"}, today="2026-10-16")

    with pytest.raises(ValueError, match='"Which approach\\?" \\(D1\\) is still proposed'):
        approve(project, today="2026-10-16")
    assert state(project)["approvals"] == []
    settle_decision(log, "D1")
    approval = approve(project, today="2026-10-16")
    advance(project)

    assert approval["tag"] == "tortoise/ideas"
    assert git(project, "tag") == "tortoise/ideas"
    assert state(project)["stage"] == "spec"


def test_a_stage_needing_approval_refuses_to_move_until_approved(project):
    move_to(project, "spec")

    with pytest.raises(ValueError, match="Spec needs your approval"):
        advance(project)
    approve(project, today="2026-10-14")
    advance(project)

    assert state(project)["stage"] == "architecture"


def test_approving_records_the_approval_and_commits_and_tags_the_documents(project):
    move_to(project, "spec")
    (project / "docs" / "SPEC.md").write_text("# Spec\n\n- R1: store lab results\n")
    (project / "notes.txt").write_text("not part of the spec")

    approve(project, today="2026-10-14")

    assert state(project)["approvals"][-1] == {"stage": "spec", "date": "2026-10-14", "tag": "tortoise/spec"}
    committed = git(project, "show", "--name-only", "--format=", "tortoise/spec").split("\n")
    assert sorted(committed) == ["docs/SPEC.md", "tortoise.json"]
    assert git(project, "status", "--porcelain") == "?? notes.txt"


def test_approving_a_stage_that_needs_no_approval_is_refused(project):
    with pytest.raises(ValueError, match="PRD review does not need approval"):
        approve(project, today="2026-10-14")


def test_approving_twice_is_refused(project):
    move_to(project, "spec")
    approve(project, today="2026-10-14")

    with pytest.raises(ValueError, match="already approved"):
        approve(project, today="2026-10-14")


def test_moving_past_the_plan_needs_milestones_in_the_plan(project):
    move_to(project, "plan")
    (project / "docs" / "PLAN.md").write_text("# Plan\n\nNo milestones yet.\n")
    approve(project, today="2026-10-14")

    with pytest.raises(ValueError, match="PLAN.md has no milestones"):
        advance(project)


def test_build_and_gate_repeat_once_per_milestone(project):
    move_to(project, "build")
    assert state(project)["milestone"] == 1
    assert describe(state(project)) == "Build, milestone 1 of 2"

    advance(project)
    assert describe(state(project)) == "Milestone gate, milestone 1 of 2 (needs your approval before moving on)"
    (project / "app.py").write_text("print('labs')\n")
    run_gate(project)
    approve(project, today="2026-10-15")
    advance(project)
    assert (state(project)["stage"], state(project)["milestone"]) == ("build", 2)
    assert "app.py" in git(project, "show", "--name-only", "--format=", "tortoise/milestone-1")

    advance(project)
    run_gate(project)
    approve(project, today="2026-10-16")
    advance(project)
    assert state(project)["stage"] == "final-checks"

    approve(project, today="2026-10-17")
    assert describe(state(project)) == "Done"
    assert git(project, "status", "--porcelain") == ""
    with pytest.raises(ValueError, match="The project is done"):
        advance(project)


def test_a_gate_cannot_be_approved_before_it_has_run(project):
    move_to(project, "build")
    advance(project)

    with pytest.raises(ValueError, match="run tortoise gate first"):
        approve(project, today="2026-10-15")


def test_approving_outside_a_git_repository_is_refused_and_records_nothing(tmp_path):
    init_project(tmp_path, name="Lab tracker", test_command="true")
    advance(tmp_path)

    with pytest.raises(ValueError, match="must be a git repository"):
        approve(tmp_path, today="2026-10-14")
    assert state(tmp_path)["approvals"] == []


def at_gate_with_tests(root, test_command):
    data = state(root)
    data["test_command"] = test_command
    (root / "tortoise.json").write_text(json.dumps(data))
    move_to(root, "build")
    advance(root)
    run_gate(root)


def test_a_gate_whose_tests_failed_cannot_be_approved(project):
    at_gate_with_tests(project, "exit 1")

    with pytest.raises(ValueError, match="tests failed at the last gate run"):
        approve(project, today="2026-10-15")
    assert [approval["stage"] for approval in state(project)["approvals"]] == ["ideas", "spec", "architecture", "plan"]


def test_a_passing_rerun_allows_the_approval(project):
    at_gate_with_tests(project, "exit 1")
    data = state(project)
    data["test_command"] = "true"
    (project / "tortoise.json").write_text(json.dumps(data))
    run_gate(project)

    approval = approve(project, today="2026-10-15")

    assert approval["tag"] == "tortoise/milestone-1"


def test_approving_despite_failing_tests_records_the_reason(project):
    at_gate_with_tests(project, "exit 1")

    approval = approve(project, today="2026-10-15", despite_failing_tests="the lab system's test server is down")

    assert approval["despite_failing_tests"] == "the lab system's test server is down"
    gate = (project / "docs" / "gates" / "milestone-1.md").read_text()
    assert gate.endswith("## Author's choices\n\n- Approved despite failing tests: the lab system's test server is down\n")
    assert git(project, "status", "--porcelain") == ""


def test_an_override_needs_a_reason_and_failing_tests(project):
    at_gate_with_tests(project, "exit 1")
    with pytest.raises(ValueError, match="needs a reason"):
        approve(project, today="2026-10-15", despite_failing_tests="  ")

    data = state(project)
    data["test_command"] = "true"
    (project / "tortoise.json").write_text(json.dumps(data))
    run_gate(project)
    with pytest.raises(ValueError, match="tests passed"):
        approve(project, today="2026-10-15", despite_failing_tests="just in case")


@pytest.mark.parametrize("name", [".env", ".env.local", "server.pem", "deploy.key", "id_ed25519"])
def test_approving_refuses_to_commit_a_new_secret_file(project, name):
    (project / name).write_text("SECRET=1\n")
    at_gate_with_tests(project, "true")

    with pytest.raises(ValueError, match=re.escape(name)):
        approve(project, today="2026-10-15")
    assert "tortoise/milestone-1" not in git(project, "tag")
    assert [approval["stage"] for approval in state(project)["approvals"]] == ["ideas", "spec", "architecture", "plan"]


def test_example_files_and_secrets_already_committed_are_allowed(project):
    (project / "settings.key").write_text("old\n")
    git(project, "add", "settings.key")
    git(project, "commit", "-q", "-m", "the author committed this on purpose")
    (project / ".env.example").write_text("SECRET=\n")
    (project / "settings.key").write_text("changed\n")
    at_gate_with_tests(project, "true")

    approve(project, today="2026-10-15")

    committed = git(project, "show", "--name-only", "--format=", "tortoise/milestone-1").split("\n")
    assert ".env.example" in committed and "settings.key" in committed


def test_changing_code_after_a_passing_gate_blocks_the_approval(project):
    at_gate_with_tests(project, "true")
    (project / "app.py").write_text("print('changed after the gate')\n")

    with pytest.raises(ValueError, match="code has changed since the gate ran"):
        approve(project, today="2026-10-15")
    run_gate(project)
    assert approve(project, today="2026-10-15")["tag"] == "tortoise/milestone-1"


def test_recording_reviews_in_docs_after_the_gate_does_not_block_the_approval(project):
    at_gate_with_tests(project, "true")
    gate = project / "docs" / "gates" / "milestone-1.md"
    gate.write_text(gate.read_text().replace("## Reviews\n\nNot recorded yet.", "## Reviews\n\n- No findings."))

    assert approve(project, today="2026-10-15")["tag"] == "tortoise/milestone-1"


def test_an_existing_tag_is_refused_before_anything_changes(project):
    move_to(project, "spec")
    git(project, "commit", "-q", "--allow-empty", "-m", "someone else's commit")
    git(project, "tag", "tortoise/spec")
    head = git(project, "rev-parse", "HEAD")

    with pytest.raises(ValueError, match="tag tortoise/spec already exists"):
        approve(project, today="2026-10-14")
    assert git(project, "rev-parse", "HEAD") == head
    assert [approval["stage"] for approval in state(project)["approvals"]] == ["ideas"]


def test_a_rejected_commit_leaves_nothing_staged_and_nothing_recorded(project):
    move_to(project, "spec")
    (project / "docs" / "SPEC.md").write_text("# Spec\n")
    hook = project / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh\necho 'hook says no' >&2\nexit 1\n")
    hook.chmod(0o755)

    with pytest.raises(ValueError, match="hook says no"):
        approve(project, today="2026-10-14")
    assert git(project, "diff", "--cached", "--name-only") == ""
    assert [approval["stage"] for approval in state(project)["approvals"]] == ["ideas"]


def test_a_document_approval_leaves_files_the_author_staged_alone(project):
    move_to(project, "spec")
    (project / "notes.txt").write_text("my own work in progress\n")
    git(project, "add", "notes.txt")

    approve(project, today="2026-10-14")

    assert "notes.txt" not in git(project, "show", "--name-only", "--format=", "tortoise/spec")
    assert git(project, "diff", "--cached", "--name-only") == "notes.txt"


def test_the_gate_makes_new_files_visible_to_reviews_but_never_secret_files(project):
    move_to(project, "build")
    advance(project)
    (project / "app.py").write_text("print('new code')\n")
    (project / ".env").write_text("SECRET=1\n")

    run_gate(project)

    in_review = git(project, "diff", "--name-only", "tortoise/plan")
    assert "app.py" in in_review.split("\n")
    assert ".env" not in in_review.split("\n")
    assert git(project, "diff", "--cached", "--name-only", "--diff-filter=AM", "--", "app.py") == ""


def test_approving_final_checks_commits_the_readme_and_bug_fixes(project):
    move_to(project, "final-checks")
    (project / "README.md").write_text("# Lab tracker\n")
    (project / "app.py").write_text("print('fixed after QA')\n")

    approve(project, today="2026-10-20")

    committed = git(project, "show", "--name-only", "--format=", "tortoise/final-checks").split("\n")
    assert "README.md" in committed and "app.py" in committed
    assert git(project, "status", "--porcelain") == ""


@pytest.mark.parametrize("plan, named", [
    ("# Plan\n\n## Milestone 1: Records\n\n- [ ] Task 1: store results\n- [ ] tidy the styles\n", '"tidy the styles"'),
    ("# Plan\n\n## Milestone 1: Records\n\n- [ ] Task 1: store results\n- [ ] Task 1: list results\n",
     '"Task 1: list results"'),
])
def test_moving_past_the_plan_needs_every_task_to_have_its_own_number(project, plan, named):
    move_to(project, "plan")
    (project / "docs" / "PLAN.md").write_text(plan)
    approve(project, today="2026-10-14")

    with pytest.raises(ValueError, match=re.escape(named)):
        advance(project)
    assert state(project)["stage"] == "plan"
