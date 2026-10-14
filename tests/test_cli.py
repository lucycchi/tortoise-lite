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

    assert (added.returncode, added.stdout) == (0, "added D1 (proposed)\n")
    assert (settled.returncode, settled.stdout) == (0, "settled D1\n")
    assert (replaced.returncode, replaced.stdout) == (0, "added D2 (proposed), replacing D1\n")
    log = (tmp_path / "docs" / "DECISIONS.md").read_text()
    assert "- **Status:** replaced by D2\n" in log


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
