import json

import pytest

from tortoise.gate import run_gate
from tortoise.project import init_project

SPEC = "# Spec\n\n- R1: store lab results\n- R2: chart them\n- R3: export a PDF\n"
PLAN = """# Plan

## Milestone 1: Records

- Task 1: store lab results. Requirements: R1
- Task 2: chart them. Requirements: R2, R9

## Milestone 2: Export

- Task 3: nothing yet.
"""


def project_at_gate(root, test_command="true", milestone=1, approvals=None):
    init_project(root, name="Lab tracker", test_command=test_command)
    state = json.loads((root / "tortoise.json").read_text())
    state.update(stage="gate", milestone=milestone, milestones=2,
                 approvals=approvals or [{"stage": "plan", "date": "2026-10-14", "tag": "tortoise/plan"}])
    (root / "tortoise.json").write_text(json.dumps(state))
    (root / "docs" / "SPEC.md").write_text(SPEC)
    (root / "docs" / "PLAN.md").write_text(PLAN)
    return root / "docs" / "gates" / f"milestone-{milestone}.md"


def test_gate_refuses_to_run_outside_a_gate_stage(tmp_path):
    init_project(tmp_path, name="Lab tracker", test_command="true")

    with pytest.raises(ValueError, match="only runs at a milestone gate"):
        run_gate(tmp_path)


def test_passing_tests_are_recorded(tmp_path):
    gate = project_at_gate(tmp_path, test_command="echo all 12 passed")

    result = run_gate(tmp_path)

    text = gate.read_text()
    assert result["passed"] is True
    assert "**Passed:** `echo all 12 passed` finished with exit code 0." in text
    assert "all 12 passed" in text.split("## Tests")[1]


def test_failing_tests_are_recorded_with_the_end_of_the_output(tmp_path):
    lines = "; ".join(f"echo line {number}" for number in range(1, 51))
    gate = project_at_gate(tmp_path, test_command=f"{lines}; exit 3")

    result = run_gate(tmp_path)

    text = gate.read_text()
    assert result["passed"] is False
    assert "**Failed:**" in text and "finished with exit code 3." in text
    assert "line 50" in text
    assert "line 21\n" in text
    assert "line 20\n" not in text


def test_requirement_coverage_lists_both_kinds_of_gap(tmp_path):
    gate = project_at_gate(tmp_path)

    run_gate(tmp_path)

    coverage = gate.read_text().split("## Requirement coverage")[1].split("## ")[0]
    assert coverage == (
        "\n\n"
        "- \"export a PDF\" (R3) is in SPEC.md but no task in PLAN.md names it.\n"
        "- An unknown requirement (R9) is named by \"Task 2: chart them\" in PLAN.md but is not in SPEC.md.\n"
        "\n"
    )


def test_full_coverage_says_so(tmp_path):
    gate = project_at_gate(tmp_path)
    (tmp_path / "docs" / "PLAN.md").write_text(PLAN.replace("R2, R9", "R2").replace("nothing yet.", "export. Requirements: R3"))

    run_gate(tmp_path)

    assert "Every requirement in SPEC.md is named by a task in PLAN.md." in gate.read_text()


def test_rerunning_replaces_results_but_keeps_what_the_skill_recorded(tmp_path):
    gate = project_at_gate(tmp_path, test_command="exit 1")
    run_gate(tmp_path)
    gate.write_text(gate.read_text().replace(
        "## Reviews\n\nNot recorded yet.", "## Reviews\n\n- Codex: the export button has no error message."))
    data = json.loads((tmp_path / "tortoise.json").read_text())
    data["test_command"] = "echo fixed"
    (tmp_path / "tortoise.json").write_text(json.dumps(data))

    run_gate(tmp_path)

    text = gate.read_text()
    assert "**Passed:** `echo fixed`" in text
    assert "**Failed:**" not in text
    assert "- Codex: the export button has no error message." in text


def test_reviews_compare_against_the_last_approval(tmp_path):
    approvals = [
        {"stage": "plan", "date": "2026-10-14", "tag": "tortoise/plan"},
        {"stage": "gate", "milestone": 1, "date": "2026-10-15", "tag": "tortoise/milestone-1"},
    ]
    gate = project_at_gate(tmp_path, milestone=2, approvals=approvals)

    result = run_gate(tmp_path)

    assert result["review_base"] == "tortoise/milestone-1"
    assert "compare against `tortoise/milestone-1`" in gate.read_text()


def test_gate_rebuilds_the_page(tmp_path):
    project_at_gate(tmp_path, test_command="echo all good")

    run_gate(tmp_path)

    assert "Milestone 1 gate" in (tmp_path / "docs" / "project.html").read_text()


def test_gate_lists_the_milestones_unticked_tasks(tmp_path):
    gate = project_at_gate(tmp_path)
    (tmp_path / "docs" / "PLAN.md").write_text(
        "# Plan\n\n## Milestone 1: Records\n\n- [x] Task 1: store. Requirements: R1\n- [ ] Task 2: list. Requirements: R2\n"
        "\n## Milestone 2: Export\n\n- [ ] Task 3: export. Requirements: R3\n"
    )

    run_gate(tmp_path)

    tasks = gate.read_text().split("## Tasks")[1].split("## ")[0]
    assert tasks == "\n\n1 of 2 tasks in milestone 1 are ticked. Not ticked:\n\n- Task 2: list. Requirements: R2\n\n"


def test_gate_says_when_every_task_is_ticked(tmp_path):
    gate = project_at_gate(tmp_path)
    (tmp_path / "docs" / "PLAN.md").write_text("# Plan\n\n## Milestone 1: Records\n\n- [x] Task 1: store. Requirements: R1\n")

    run_gate(tmp_path)

    assert "Every task in milestone 1 is ticked (1 of 1)." in gate.read_text()
