import json

from tortoise.project import init_project


def test_init_creates_state_file_and_empty_decision_log(tmp_path):
    init_project(tmp_path, name="Lab tracker", test_command="pytest -q")

    state = json.loads((tmp_path / "tortoise.json").read_text())
    assert state == {
        "name": "Lab tracker",
        "stage": "prd-review",
        "test_command": "pytest -q",
        "approvals": [],
    }
    log = (tmp_path / "docs" / "DECISIONS.md").read_text()
    assert log.startswith("# Decisions\n")
    assert "## D" not in log
    assert log.rstrip().endswith("## Glossary")


def test_init_keeps_existing_files_and_reports_them(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "DECISIONS.md").write_text("# Decisions\n\n## D1: keep me\n")
    (tmp_path / "tortoise.json").write_text('{"name": "Old"}\n')

    result = init_project(tmp_path, name="New", test_command="pytest")

    assert (tmp_path / "docs" / "DECISIONS.md").read_text() == "# Decisions\n\n## D1: keep me\n"
    assert (tmp_path / "tortoise.json").read_text() == '{"name": "Old"}\n'
    assert result == {"created": [], "kept": ["tortoise.json", "docs/DECISIONS.md"]}


def test_init_reports_created_files(tmp_path):
    result = init_project(tmp_path, name="New", test_command="pytest")

    assert result == {"created": ["tortoise.json", "docs/DECISIONS.md"], "kept": []}
