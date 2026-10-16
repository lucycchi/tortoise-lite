"""The progress board: copies the plan's tasks onto a GitHub Project, one way.

Every project whose repository is on GitHub gets one; a project without a GitHub remote is
skipped. docs/PLAN.md stays the only source of truth. Each numbered task becomes an issue in the
project's own repository, and a "Progress" field on the board shows where it stands. Every
GitHub call goes through the gh command-line tool, and tortoise.json remembers the board and
which issue is which task, so a run that fails part way can be repeated without duplicates.
"""

import json
import re
import subprocess
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from tortoise.plan import read_milestones
from tortoise.project import load_state, save_state

FIELD = "Progress"
STATUSES = ("To do", "In progress", "Awaiting gate", "Done")
NUMBERED_TASK = re.compile(r"^Task (\d+):\s*(.*)$")
GITHUB_REMOTE = re.compile(r"github\.com[:/]([^/\s]+)/([^/\s]+?)(?:\.git)?/?$")


class BoardError(Exception):
    """GitHub could not be reached or refused a change; the board is left part way and a rerun resumes."""


@dataclass
class Card:
    task: int
    title: str
    milestone: int
    milestone_title: str
    status: str


def plan_cards(plan: str, state: dict) -> list[Card]:
    """One card per numbered task in the plan, with the status the milestone gate gives it."""
    approved = {approval["milestone"] for approval in state["approvals"] if approval["stage"] == "gate"}
    current = state.get("milestone") if state["stage"] in ("build", "gate") else None
    cards = []
    for milestone in read_milestones(plan):
        for ticked, text in milestone.tasks:
            numbered = NUMBERED_TASK.match(text)
            if not numbered:
                continue
            if milestone.number in approved:
                status = "Done"
            elif ticked:
                status = "Awaiting gate"
            elif milestone.number == current:
                status = "In progress"
            else:
                status = "To do"
            what = numbered.group(2).split("Requirements:")[0].strip().rstrip(".")
            cards.append(Card(
                task=int(numbered.group(1)),
                title=f"{what[:1].upper()}{what[1:]} (Task {numbered.group(1)})",
                milestone=milestone.number,
                milestone_title=f"{milestone.name} (Milestone {milestone.number})",
                status=status,
            ))
    return cards


def sync_board(root: Path, gh: Callable[[list[str]], str] | None = None) -> list[str]:
    """Bring the board in line with the plan, creating it on the first run. Returns what it did."""
    repo = github_repository(root)
    if repo is None:
        return ["no GitHub repository for this project, so no progress board"]
    gh = gh or _gh_in(root)
    plan_path = root / "docs" / "PLAN.md"
    plan = plan_path.read_text() if plan_path.exists() else ""
    milestones = read_milestones(plan)
    if not milestones:
        raise ValueError('PLAN.md has no milestones; add headings such as "## Milestone 1: Records"')
    state = load_state(root)
    cards = plan_cards(plan, state)
    messages = []

    board = state.get("board")
    if not board:
        owner = repo.split("/")[0]
        created = json.loads(gh(["project", "create", "--owner", owner, "--title", state["name"], "--format", "json"]))
        board = {"number": created["number"], "id": created["id"], "url": created["url"], "owner": owner,
                 "repo": repo, "milestones": [], "cards": {}}
        gh(["project", "link", str(board["number"]), "--owner", owner, "--repo", board["repo"]])
        state["board"] = board
        save_state(root, state)
        messages += [f"created the progress board {board['url']}",
                     f"add a board view grouped by {FIELD}: open the board, choose New view, then Board, and "
                     f"group it by the {FIELD} field (GitHub cannot do this for a tool)"]
    if "field" not in board:
        number, owner = str(board["number"]), board["owner"]
        gh(["project", "field-create", number, "--owner", owner, "--name", FIELD,
            "--data-type", "SINGLE_SELECT", "--single-select-options", ",".join(STATUSES)])
        fields = json.loads(gh(["project", "field-list", number, "--owner", owner, "--format", "json"]))["fields"]
        progress = next(field for field in fields if field["name"] == FIELD)
        board["field"] = progress["id"]
        board["options"] = {option["name"]: option["id"] for option in progress["options"]}
        save_state(root, state)

    unnumbered = sum(milestone.total for milestone in milestones) - len(cards)
    if unnumbered:
        tasks = "task" if unnumbered == 1 else "tasks"
        messages.append(f'left off the board {unnumbered} {tasks} without a number (write each as "Task 6: ...")')

    known_milestones = None
    for card in cards:
        saved = board["cards"].get(str(card.task))
        if saved is None:
            if card.milestone_title not in board["milestones"]:
                if known_milestones is None:
                    listed = json.loads(gh(["api", f"repos/{board['repo']}/milestones?state=all&per_page=100"]))
                    known_milestones = {milestone["title"] for milestone in listed}
                if card.milestone_title not in known_milestones:
                    gh(["api", f"repos/{board['repo']}/milestones", "-f", f"title={card.milestone_title}"])
                board["milestones"].append(card.milestone_title)
            url = gh(["issue", "create", "-R", board["repo"], "--title", card.title, "--body", _body(card),
                      "--milestone", card.milestone_title]).strip()
            item = json.loads(gh(["project", "item-add", str(board["number"]), "--owner", board["owner"],
                                  "--url", url, "--format", "json"]))
            saved = {"issue": int(url.rsplit("/", 1)[1]), "item": item["id"], "title": card.title, "status": None}
            board["cards"][str(card.task)] = saved
            save_state(root, state)
        if saved["title"] != card.title:
            gh(["issue", "edit", "-R", board["repo"], str(saved["issue"]), "--title", card.title])
            saved["title"] = card.title
        if saved["status"] != card.status:
            gh(["project", "item-edit", "--id", saved["item"], "--project-id", board["id"],
                "--field-id", board["field"], "--single-select-option-id", board["options"][card.status]])
            if card.status == "Done":
                gh(["issue", "close", "-R", board["repo"], str(saved["issue"])])
            elif saved["status"] == "Done":
                gh(["issue", "reopen", "-R", board["repo"], str(saved["issue"])])
            saved["status"] = card.status
        save_state(root, state)

    counts = Counter(card.status for card in cards)
    summary = ", ".join(f"{counts[status]} {status.lower()}" for status in reversed(STATUSES) if counts[status])
    messages.append(f"board up to date: {len(cards)} tasks ({summary})")
    return messages


def github_repository(root: Path) -> str | None:
    """The project's GitHub repository as "owner/name", from its git remotes: origin first, then any other."""
    run = subprocess.run(["git", "remote", "-v"], cwd=root, capture_output=True, text=True)
    remotes = {}
    for line in run.stdout.splitlines() if run.returncode == 0 else []:
        name, url = line.split()[:2]
        if found := GITHUB_REMOTE.search(url):
            remotes.setdefault(name, f"{found.group(1)}/{found.group(2)}")
    return remotes.get("origin") or next(iter(remotes.values()), None)


def _body(card: Card) -> str:
    return (f"Task {card.task} in milestone {card.milestone} of docs/PLAN.md. Tortoise Lite keeps this card "
            "in step with the plan, so change the plan, not the card.")


def _gh_in(root: Path) -> Callable[[list[str]], str]:
    def gh(arguments: list[str]) -> str:
        try:
            run = subprocess.run(["gh", *arguments], cwd=root, capture_output=True, text=True)
        except FileNotFoundError as error:
            raise BoardError("the gh command-line tool is not installed") from error
        if run.returncode != 0:
            raise BoardError(run.stderr.strip() or f"gh {' '.join(arguments[:2])} failed")
        return run.stdout
    return gh
