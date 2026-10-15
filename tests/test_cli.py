import json
import os
import subprocess
import sys
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parent.parent


def tortoise(folder, *arguments):
    """Run the real tortoise command from a project folder."""
    return subprocess.run(
        [str(REPOSITORY / "bin" / "tortoise"), *arguments],
        cwd=folder,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHON": sys.executable},
    )


def test_init_reports_what_it_created_then_what_it_kept(tmp_path):
    first = tortoise(tmp_path, "init", "--name", "Lab tracker", "--test-command", "pytest -q")
    second = tortoise(tmp_path, "init", "--name", "Lab tracker", "--test-command", "pytest -q")

    assert first.returncode == 0
    assert first.stdout == "created tortoise.json\ncreated docs/DECISIONS.md\n"
    assert second.returncode == 0
    assert second.stdout == "kept tortoise.json (already exists)\nkept docs/DECISIONS.md (already exists)\n"


def test_decide_adds_settles_and_replaces(tmp_path):
    tortoise(tmp_path, "init", "--name", "Lab tracker", "--test-command", "pytest")
    form = tmp_path / "decision.json"
    form.write_text(json.dumps({
        "question": "Which database?",
        "options": ["SQLite", "PostgreSQL"],
        "choice": "SQLite",
        "reason": "One user.",
        "proposed_by": "Claude (claude-opus-5-5)",
    }))

    added = tortoise(tmp_path, "decide", "--from", str(form))
    settled = tortoise(tmp_path, "decide", "--settle", "D1")
    replaced = tortoise(tmp_path, "decide", "--from", str(form), "--replaces", "D1")

    assert (added.returncode, added.stdout) == (0, 'added "Which database?" (D1), proposed\n')
    assert (settled.returncode, settled.stdout) == (0, 'settled "Which database?" (D1)\n')
    assert (replaced.returncode, replaced.stdout) == (
        0, 'added "Which database?" (D2), proposed, replacing "Which database?" (D1)\n')
    log = (tmp_path / "docs" / "DECISIONS.md").read_text()
    assert '- **Status:** replaced by "Which database?" (D2)\n' in log


def test_errors_are_plain_messages_with_exit_code_1(tmp_path):
    tortoise(tmp_path, "init", "--name", "Lab tracker", "--test-command", "pytest")
    form = tmp_path / "decision.json"
    form.write_text(json.dumps({"question": "Which database?"}))

    missing_fields = tortoise(tmp_path, "decide", "--from", str(form))
    unknown = tortoise(tmp_path, "decide", "--settle", "D4")
    not_a_project = tortoise(tmp_path / "docs", "page")

    assert missing_fields.returncode == 1
    assert missing_fields.stderr == "tortoise: decision is missing: options, choice, reason, proposed_by\n"
    assert unknown.returncode == 1
    assert unknown.stderr == "tortoise: no decision D4 in the log\n"
    assert not_a_project.returncode == 1
    assert not_a_project.stderr == "tortoise: no tortoise.json here; run tortoise init first\n"


def test_page_prints_where_it_wrote_the_page(tmp_path):
    tortoise(tmp_path, "init", "--name", "Lab tracker", "--test-command", "pytest")

    result = tortoise(tmp_path, "page")

    assert (result.returncode, result.stdout) == (0, "wrote docs/project.html\n")
    assert (tmp_path / "docs" / "project.html").exists()


def test_page_also_writes_a_page_for_each_record_with_diagrams(tmp_path):
    tortoise(tmp_path, "init", "--name", "Lab tracker", "--test-command", "pytest")
    (tmp_path / "docs" / "ARCHITECTURE.md").write_text("# Architecture\n\n```mermaid\ngraph TD\n  A --> B\n```\n")

    result = tortoise(tmp_path, "page")

    assert (result.returncode, result.stdout) == (0, "wrote docs/project.html\nwrote docs/ARCHITECTURE.html\n")


def test_html_renders_any_markdown_file_without_a_tortoise_project(tmp_path):
    (tmp_path / "THREAT_MODEL.md").write_text("# Threat model\n\n```mermaid\ngraph TD\n  A --> B\n```\n")
    (tmp_path / "notes").mkdir()
    (tmp_path / "notes" / "flows.md").write_text("# Flows\n")

    result = tortoise(tmp_path, "html", "THREAT_MODEL.md", "notes/flows.md")

    assert (result.returncode, result.stdout) == (0, "wrote THREAT_MODEL.html\nwrote notes/flows.html\n")
    assert (tmp_path / "notes" / "flows.html").exists()


def test_html_refuses_a_missing_or_non_markdown_file(tmp_path):
    (tmp_path / "page.txt").write_text("hello")

    missing = tortoise(tmp_path, "html", "nowhere.md")
    not_markdown = tortoise(tmp_path, "html", "page.txt")

    assert (missing.returncode, missing.stderr) == (1, "tortoise: nowhere.md does not exist\n")
    assert (not_markdown.returncode, not_markdown.stderr) == (1, "tortoise: page.txt is not a Markdown (.md) file\n")


def test_an_unreadable_decision_form_is_a_plain_error(tmp_path):
    tortoise(tmp_path, "init", "--name", "Lab tracker", "--test-command", "pytest")
    (tmp_path / "broken.json").write_text("{not json")
    (tmp_path / "list.json").write_text('["SQLite"]')

    broken = tortoise(tmp_path, "decide", "--from", "broken.json")
    not_an_object = tortoise(tmp_path, "decide", "--from", "list.json")
    absent = tortoise(tmp_path, "decide", "--from", "absent.json")

    assert broken.returncode == 1
    assert broken.stderr.startswith("tortoise: could not read the decision form broken.json:")
    assert not_an_object.returncode == 1
    assert not_an_object.stderr == "tortoise: the decision form list.json must hold a JSON object\n"
    assert absent.returncode == 1
    assert absent.stderr.startswith("tortoise: could not read the decision form absent.json:")


def git(folder, *arguments):
    subprocess.run(["git", *arguments], cwd=folder, capture_output=True, check=True)


def test_stage_approve_and_gate_from_the_command_line(tmp_path):
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "config", "user.name", "Test Author")
    git(tmp_path, "config", "user.email", "author@example.com")
    tortoise(tmp_path, "init", "--name", "Lab tracker", "--test-command", "echo 3 passed")

    shown = tortoise(tmp_path, "stage")
    moved = [tortoise(tmp_path, "stage", "next").stdout for _ in range(2)]
    blocked = tortoise(tmp_path, "stage", "next")
    approved = tortoise(tmp_path, "approve")

    assert shown.stdout == "Current stage: PRD review\n"
    assert moved == ["Now at: Ideas\n", "Now at: Spec (needs your approval before moving on)\n"]
    assert (blocked.returncode, blocked.stderr) == (1, "tortoise: Spec needs your approval first: run tortoise approve\n")
    assert approved.stdout == (
        "approved Spec; committed and tagged tortoise/spec\n"
        "committed: docs/DECISIONS.md, tortoise.json\n"
    )

    tortoise(tmp_path, "stage", "next")
    tortoise(tmp_path, "approve")
    tortoise(tmp_path, "stage", "next")
    (tmp_path / "docs" / "PLAN.md").write_text("# Plan\n\n## Milestone 1: Records\n")
    tortoise(tmp_path, "approve")
    tortoise(tmp_path, "stage", "next")
    building = tortoise(tmp_path, "stage")
    tortoise(tmp_path, "stage", "next")
    gate = tortoise(tmp_path, "gate")

    assert building.stdout == "Current stage: Build, milestone 1 of 1\nTasks ticked: 0 of 0\n"

    assert gate.returncode == 0
    assert gate.stdout == (
        "tests passed (exit code 0)\n"
        "results in docs/gates/milestone-1.md; reviews compare against tortoise/plan\n"
        "page rebuilt: docs/project.html\n"
    )


def test_approve_despite_failing_tests_from_the_command_line(tmp_path):
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "config", "user.name", "Test Author")
    git(tmp_path, "config", "user.email", "author@example.com")
    tortoise(tmp_path, "init", "--name", "Lab tracker", "--test-command", "exit 1")
    for _ in range(4):
        tortoise(tmp_path, "stage", "next")
        if _ == 3:
            (tmp_path / "docs" / "PLAN.md").write_text("# Plan\n\n## Milestone 1: Records\n")
        tortoise(tmp_path, "approve")
    tortoise(tmp_path, "stage", "next")
    tortoise(tmp_path, "stage", "next")
    tortoise(tmp_path, "gate")

    blocked = tortoise(tmp_path, "approve")
    allowed = tortoise(tmp_path, "approve", "--despite-failing-tests", "test server down")

    assert blocked.returncode == 1
    assert blocked.stderr.startswith("tortoise: the tests failed at the last gate run.")
    assert allowed.returncode == 0
    assert allowed.stdout == (
        "approved Milestone gate, milestone 1 of 1 despite failing tests (test server down); "
        "committed and tagged tortoise/milestone-1\n"
        "committed: docs/gates/milestone-1.md, docs/project.html, tortoise.json\n"
    )


def test_board_warns_and_exits_cleanly_when_github_cannot_be_reached(tmp_path):
    tortoise(tmp_path, "init", "--name", "Lab tracker", "--test-command", "pytest")
    (tmp_path / "docs" / "PLAN.md").write_text("# Plan\n\n## Milestone 1: Records\n\n- [ ] Task 1: store results\n")
    offline = tmp_path / "offline"
    offline.mkdir()
    (offline / "gh").write_text("#!/bin/sh\necho 'error connecting to api.github.com' >&2\nexit 1\n")
    (offline / "gh").chmod(0o755)

    result = subprocess.run(
        [str(REPOSITORY / "bin" / "tortoise"), "board"],
        cwd=tmp_path, capture_output=True, text=True,
        env={**os.environ, "PYTHON": sys.executable, "PATH": f"{offline}{os.pathsep}{os.environ['PATH']}"},
    )

    assert result.returncode == 0
    assert result.stderr.startswith("tortoise: warning: the progress board was not updated")
    assert "error connecting to api.github.com" in result.stderr
