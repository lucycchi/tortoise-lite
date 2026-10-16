import json
import subprocess

import pytest

from tortoise.board import BoardError, plan_cards, sync_board
from tortoise.project import init_project, load_state, save_state

PLAN = """# Plan

## Milestone 1: Records

- [x] Task 1: store lab results. Requirements: R1
- [x] Task 2: list them by date. Requirements: R1

## Milestone 2: Charts

- [x] Task 3: chart the results. Requirements: R2
- [ ] Task 4: label the chart axes. Requirements: R2
- [ ] tidy the styles

## Milestone 3: Export

- [ ] Task 5: export a PDF. Requirements: R3

### Task 3: chart the results

Details the board ignores.
"""

GATE_1_APPROVED = {"stage": "gate", "date": "2026-10-15", "tag": "tortoise/milestone-1", "milestone": 1}


def statuses(cards):
    return {card.task: card.status for card in cards}


def test_cards_follow_the_gate():
    state = {"stage": "build", "milestone": 2, "milestones": 3, "approvals": [GATE_1_APPROVED]}

    cards = plan_cards(PLAN, state)

    assert statuses(cards) == {1: "Done", 2: "Done", 3: "Awaiting gate", 4: "In progress", 5: "To do"}


def test_cards_are_titled_by_what_the_task_is_with_its_number_after():
    cards = plan_cards(PLAN, {"stage": "plan", "approvals": []})

    assert [card.title for card in cards[:3]] == [
        "Store lab results (Task 1)", "List them by date (Task 2)", "Chart the results (Task 3)"]
    assert cards[0].milestone_title == "Records (Milestone 1)"


def test_before_the_build_every_unticked_task_is_to_do():
    cards = plan_cards(PLAN.replace("[x]", "[ ]"), {"stage": "plan", "approvals": []})

    assert set(statuses(cards).values()) == {"To do"}


def test_tasks_without_a_number_are_left_off_the_board():
    cards = plan_cards(PLAN, {"stage": "plan", "approvals": []})

    assert [card.task for card in cards] == [1, 2, 3, 4, 5]


class FakeGitHub:
    """Answers the gh commands the board uses, and records each one."""

    def __init__(self, fail_on=None):
        self.calls = []
        self.fail_on = fail_on
        self.issues = 0

    def __call__(self, arguments):
        self.calls.append(arguments)
        command = " ".join(arguments[:2])
        if self.fail_on and self.fail_on(arguments):
            raise BoardError("gh: network unreachable")
        if command == "project create":
            return json.dumps({"number": 7, "id": "PVT_7", "url": "https://github.com/users/lucy/projects/7"})
        if command == "project field-list":
            return json.dumps({"fields": [{"id": "F_1", "name": "Progress", "options": [
                {"id": "O_todo", "name": "To do"}, {"id": "O_doing", "name": "In progress"},
                {"id": "O_waiting", "name": "Awaiting gate"}, {"id": "O_done", "name": "Done"}]}]})
        if command == "issue create":
            self.issues += 1
            return f"https://github.com/lucy/lab-tracker/issues/{self.issues}\n"
        if command == "project item-add":
            return json.dumps({"id": f"ITEM_{arguments[-3].rsplit('/', 1)[1]}"})
        if command == "api" and "milestones" in arguments[1] and "-f" not in arguments:
            return "[]"
        return "{}"

    def made(self, *prefix):
        return [call for call in self.calls if call[:len(prefix)] == list(prefix)]


def git(root, *arguments):
    subprocess.run(["git", *arguments], cwd=root, capture_output=True, text=True, check=True)


@pytest.fixture
def project(tmp_path):
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "remote", "add", "origin", "git@github.com:lucy/lab-tracker.git")
    init_project(tmp_path, name="Lab tracker", test_command="true")
    state = load_state(tmp_path)
    state.update(stage="build", milestone=2, milestones=3, approvals=[GATE_1_APPROVED])
    save_state(tmp_path, state)
    (tmp_path / "docs" / "PLAN.md").write_text(PLAN)
    return tmp_path


def test_first_sync_creates_the_board_issues_and_statuses(project):
    github = FakeGitHub()

    messages = sync_board(project, github)

    assert github.made("project", "create")[0][-4:] == ["--title", "Lab tracker", "--format", "json"]
    assert github.made("project", "link") and github.made("project", "field-create")
    assert len(github.made("issue", "create")) == 5
    assert [call[-1] for call in github.made("project", "item-edit")] == [
        "O_done", "O_done", "O_waiting", "O_doing", "O_todo"]
    assert len(github.made("issue", "close")) == 2
    board = load_state(project)["board"]
    assert board["number"] == 7 and board["repo"] == "lucy/lab-tracker"
    assert board["cards"]["4"] == {"issue": 4, "item": "ITEM_4", "title": "Label the chart axes (Task 4)",
                                   "status": "In progress"}
    assert messages[0] == "created the progress board https://github.com/users/lucy/projects/7"
    assert "add a board view grouped by Progress" in messages[1]
    assert messages[-1] == "board up to date: 5 tasks (2 done, 1 awaiting gate, 1 in progress, 1 to do)"
    assert any("1 task without a number" in message for message in messages)


def test_a_second_sync_with_no_changes_writes_nothing(project):
    sync_board(project, FakeGitHub())
    github = FakeGitHub()

    sync_board(project, github)

    assert github.made("issue", "create") == []
    assert github.made("project", "item-edit") == []
    assert github.made("project", "create") == []


def test_a_ticked_task_moves_to_awaiting_gate_and_a_renamed_task_is_retitled(project):
    sync_board(project, FakeGitHub())
    plan = PLAN.replace("- [ ] Task 4: label the chart axes", "- [x] Task 4: label both chart axes")
    (project / "docs" / "PLAN.md").write_text(plan)
    github = FakeGitHub()

    sync_board(project, github)

    assert github.made("project", "item-edit")[0][-1] == "O_waiting"
    assert github.made("issue", "edit")[0][-2:] == ["--title", "Label both chart axes (Task 4)"]


def test_a_failure_part_way_keeps_what_was_made_so_a_rerun_does_not_duplicate_issues(project):
    with pytest.raises(BoardError, match="network unreachable"):
        sync_board(project, FakeGitHub(fail_on=lambda call: call[:2] == ["issue", "create"] and "Task 3" in " ".join(call)))
    github = FakeGitHub()
    github.issues = 2

    sync_board(project, github)

    assert len(github.made("issue", "create")) == 3
    assert github.made("project", "create") == []
    assert set(load_state(project)["board"]["cards"]) == {"1", "2", "3", "4", "5"}


def test_a_plan_without_milestones_is_refused(project):
    (project / "docs" / "PLAN.md").write_text("# Plan\n")

    with pytest.raises(ValueError, match="no milestones"):
        sync_board(project, FakeGitHub())


@pytest.mark.parametrize("remotes", [[], [("origin", "git@gitlab.com:lucy/lab-tracker.git")]])
def test_without_a_github_repository_there_is_no_board_and_github_is_never_called(project, remotes):
    git(project, "remote", "remove", "origin")
    for name, url in remotes:
        git(project, "remote", "add", name, url)
    github = FakeGitHub()

    messages = sync_board(project, github)

    assert messages == ["no GitHub repository for this project, so no progress board"]
    assert github.calls == []
    assert "board" not in load_state(project)


def test_the_board_follows_the_github_remote_even_when_another_remote_comes_first(project):
    git(project, "remote", "remove", "origin")
    git(project, "remote", "add", "origin", "git@gitlab.com:lucy/lab-tracker.git")
    git(project, "remote", "add", "github", "https://github.com/lucy/lab-tracker-mirror.git")
    github = FakeGitHub()

    sync_board(project, github)

    assert load_state(project)["board"]["repo"] == "lucy/lab-tracker-mirror"
    assert all(call[2:4] == ["-R", "lucy/lab-tracker-mirror"] for call in github.made("issue"))
