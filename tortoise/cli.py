"""The tortoise command line: init, decide, page, stage, approve, gate, board and html.

Every command works on the project in the current folder. A problem the user
can fix prints one plain line to standard error and exits with code 1.
"""

import argparse
import datetime
import json
import sys
from pathlib import Path

from tortoise.board import BoardError, sync_board
from tortoise.decisions import add_decision, question_of, settle_decision
from tortoise.gate import run_gate
from tortoise.page import build_diagram_pages, build_document_page, build_page
from tortoise.plan import read_milestones
from tortoise.project import init_project, load_state
from tortoise.stages import advance, approve, committed_files, describe, stage_name


class UserError(Exception):
    """A problem the user can fix; shown as a message, never a traceback."""


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="tortoise")
    commands = parser.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init", help="start a project here, never overwriting a file")
    init.add_argument("--name", required=True)
    init.add_argument("--test-command", required=True, help="the command that runs the project's tests")

    decide = commands.add_parser("decide", help="propose, settle or replace a decision")
    action = decide.add_mutually_exclusive_group(required=True)
    action.add_argument("--from", dest="form", type=Path, help="a JSON file holding the decision's fields")
    action.add_argument("--settle", metavar="NUMBER", help="mark a decision settled (the author only)")
    decide.add_argument("--replaces", metavar="NUMBER", help="the decision the new one replaces")

    commands.add_parser("page", help="build docs/project.html")

    stage = commands.add_parser("stage", help="show the current stage, or move to the next one")
    stage.add_argument("move", nargs="?", choices=["next"])

    approve_command = commands.add_parser("approve", help="record your approval of the current stage, then commit and tag it")
    approve_command.add_argument("--despite-failing-tests", metavar="REASON",
                                 help="approve a gate whose tests failed, recording why")
    commands.add_parser("gate", help="run the milestone gate: tests, requirement coverage, page")
    html_command = commands.add_parser("html", help="write a Markdown file as a page beside it, with its diagrams drawn")
    html_command.add_argument("files", nargs="+", type=Path)
    commands.add_parser("board", help="copy the plan's tasks onto the project's GitHub progress board")

    arguments = parser.parse_args(argv)
    try:
        for line in _run(arguments, Path.cwd()):
            print(line)
    except UserError as error:
        print(f"tortoise: {error}", file=sys.stderr)
        sys.exit(1)


def _run(arguments: argparse.Namespace, root: Path) -> list[str]:
    if arguments.command == "init":
        result = init_project(root, arguments.name, arguments.test_command)
        return [f"created {name}" for name in result["created"]] + [
            f"kept {name} (already exists)" for name in result["kept"]
        ]

    if arguments.command == "html":
        # Works on any Markdown file, in a Tortoise project or not.
        for source in arguments.files:
            if not source.exists():
                raise UserError(f"{source} does not exist")
            if source.suffix != ".md":
                raise UserError(f"{source} is not a Markdown (.md) file")
        return [f"wrote {_shown(build_document_page(root / source), root)}" for source in arguments.files]

    if not (root / "tortoise.json").exists():
        raise UserError("no tortoise.json here; run tortoise init first")

    if arguments.command == "decide":
        log = root / "docs" / "DECISIONS.md"
        try:
            if arguments.settle:
                settle_decision(log, arguments.settle)
                return [f'settled "{question_of(log, arguments.settle)}" ({arguments.settle})']
            fields = _read_form(arguments.form)
            number = add_decision(log, fields, datetime.date.today().isoformat(), replaces=arguments.replaces)
        except ValueError as error:
            raise UserError(str(error)) from error
        replacing = (f', replacing "{question_of(log, arguments.replaces)}" ({arguments.replaces})'
                     if arguments.replaces else "")
        return [f'added "{fields["question"]}" ({number}), proposed{replacing}']

    try:
        if arguments.command == "board":
            try:
                return sync_board(root)
            except BoardError as error:
                # The board is a convenience; a GitHub problem must never stop the project's stages.
                print(f"tortoise: warning: the progress board was not updated ({error}); "
                      "run tortoise board again later", file=sys.stderr)
                return []
        if arguments.command == "stage":
            if arguments.move:
                return [f"Now at: {describe(advance(root))}"]
            state = load_state(root)
            lines = [f"Current stage: {describe(state)}"]
            if state["stage"] in ("build", "gate"):
                plan = (root / "docs" / "PLAN.md").read_text() if (root / "docs" / "PLAN.md").exists() else ""
                milestone = next((m for m in read_milestones(plan) if m.number == state["milestone"]), None)
                if milestone:
                    lines.append(f"Tasks ticked: {milestone.done} of {milestone.total}")
            return lines
        if arguments.command == "approve":
            approved = stage_name(load_state(root))
            reason = arguments.despite_failing_tests
            approval = approve(root, datetime.date.today().isoformat(), despite_failing_tests=reason)
            despite = f" despite failing tests ({approval['despite_failing_tests']})" if reason else ""
            files = ", ".join(committed_files(root, approval["tag"])) or "nothing new"
            return [f"approved {approved}{despite}; committed and tagged {approval['tag']}", f"committed: {files}"]
        if arguments.command == "gate":
            result = run_gate(root)
            verdict = "passed" if result["passed"] else "FAILED"
            return [
                f"tests {verdict} (exit code {result['exit_code']})",
                f"results in {result['path'].relative_to(root)}; reviews compare against {result['review_base']}",
                "page rebuilt: docs/project.html",
            ]
    except ValueError as error:
        raise UserError(str(error)) from error

    paths = [build_page(root), *build_diagram_pages(root / "docs")]
    return [f"wrote {path.relative_to(root)}" for path in paths]


def _shown(path: Path, root: Path) -> Path:
    """A path relative to the current folder when it is inside it, otherwise as given."""
    return path.relative_to(root) if path.is_relative_to(root) else path


def _read_form(path: Path) -> dict:
    try:
        fields = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise UserError(f"could not read the decision form {path}: {error}") from error
    if not isinstance(fields, dict):
        raise UserError(f"the decision form {path} must hold a JSON object")
    return fields
