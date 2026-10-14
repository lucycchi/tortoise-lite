from tortoise.plan import read_milestones

PLAN = """# Plan

Intro text with - [ ] something that is not under a milestone.

## Milestone 1: Records

- [x] Task 1: store lab results. Requirements: R1
- [X] Task 2: list them. Requirements: R1
- [ ] Task 3: delete one. Requirements: R4

Notes: not a task.

## Milestone 2: Charts

* [ ] Task 4: draw the chart. Requirements: R2

## Glossary

- [ ] not a task either
"""


def test_reads_each_milestone_with_its_tasks_and_ticks():
    milestones = read_milestones(PLAN)

    assert [(m.number, m.name) for m in milestones] == [(1, "Records"), (2, "Charts")]
    assert milestones[0].tasks == [
        (True, "Task 1: store lab results. Requirements: R1"),
        (True, "Task 2: list them. Requirements: R1"),
        (False, "Task 3: delete one. Requirements: R4"),
    ]
    assert (milestones[0].done, milestones[0].total) == (2, 3)
    assert milestones[1].tasks == [(False, "Task 4: draw the chart. Requirements: R2")]


def test_a_plan_without_milestones_has_none():
    assert read_milestones("# Plan\n\n- [ ] Task 1\n") == []
