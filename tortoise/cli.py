"""The tortoise command line: tortoise init, tortoise decide and tortoise page.

Every command works on the project in the current folder. A problem the user
can fix prints one plain line to standard error and exits with code 1.
"""

import argparse
import datetime
import json
import sys
from pathlib import Path

from tortoise.decisions import add_decision, settle_decision
from tortoise.page import build_page
from tortoise.project import init_project


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

    if not (root / "tortoise.json").exists():
        raise UserError("no tortoise.json here; run tortoise init first")

    if arguments.command == "decide":
        log = root / "docs" / "DECISIONS.md"
        try:
            if arguments.settle:
                settle_decision(log, arguments.settle)
                return [f"settled {arguments.settle}"]
            fields = _read_form(arguments.form)
            number = add_decision(log, fields, datetime.date.today().isoformat(), replaces=arguments.replaces)
        except ValueError as error:
            raise UserError(str(error)) from error
        replacing = f", replacing {arguments.replaces}" if arguments.replaces else ""
        return [f"added {number} (proposed){replacing}"]

    path = build_page(root)
    return [f"wrote {path.relative_to(root)}"]


def _read_form(path: Path) -> dict:
    try:
        fields = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise UserError(f"could not read the decision form {path}: {error}") from error
    if not isinstance(fields, dict):
        raise UserError(f"the decision form {path} must hold a JSON object")
    return fields
