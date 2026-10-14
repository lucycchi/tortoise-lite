import json
import subprocess

import pytest

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
            approve(root, today="2026-10-14")
            advance(root)


def test_stages_without_an_approval_move_straight_on(project):
    advance(project)
    advance(project)

    assert state(project)["stage"] == "spec"
    assert describe(state(project)) == "Spec (needs your approval before moving on)"


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

    assert state(project)["approvals"] == [{"stage": "spec", "date": "2026-10-14", "tag": "tortoise/spec"}]
    committed = git(project, "show", "--name-only", "--format=", "tortoise/spec").split("\n")
    assert sorted(committed) == ["docs/DECISIONS.md", "docs/SPEC.md", "tortoise.json"]
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
    assert [approval["stage"] for approval in state(project)["approvals"]] == ["spec", "architecture", "plan"]


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
