import pytest

from tortoise.decisions import add_decision, settle_decision
from tortoise.project import init_project

DATABASE_DECISION = {
    "question": "Which database should the lab tracker use?",
    "options": ["SQLite", "PostgreSQL"],
    "research": [
        {
            "link": "https://sqlite.org/whentouse.html",
            "summary": "SQLite suits one-server apps with modest write traffic.",
        }
    ],
    "choice": "SQLite",
    "reason": "One user on one machine; no server to run.",
    "proposed_by": "Claude (claude-opus-5-5)",
}


@pytest.fixture
def log(tmp_path):
    init_project(tmp_path, name="Lab tracker", test_command="pytest")
    return tmp_path / "docs" / "DECISIONS.md"


def test_add_decision_writes_a_proposed_entry_before_the_glossary(log):
    number = add_decision(log, DATABASE_DECISION, today="2026-10-14")

    assert number == "D1"
    assert log.read_text().endswith(
        "## D1: Which database should the lab tracker use?\n"
        "\n"
        "- **Status:** proposed\n"
        "- **Proposed by:** Claude (claude-opus-5-5) on 2026-10-14\n"
        "- **Options:**\n"
        "  - SQLite\n"
        "  - PostgreSQL\n"
        "- **Research:**\n"
        "  - [https://sqlite.org/whentouse.html](https://sqlite.org/whentouse.html): SQLite suits one-server apps with modest write traffic.\n"
        "- **Choice:** SQLite\n"
        "- **Reason:** One user on one machine; no server to run.\n"
        "\n"
        "## Glossary\n"
    )


def test_add_decision_numbers_entries_in_order(log):
    add_decision(log, DATABASE_DECISION, today="2026-10-14")
    second = add_decision(log, {**DATABASE_DECISION, "question": "Which web framework?"}, today="2026-10-15")

    assert second == "D2"
    text = log.read_text()
    assert text.index("## D1: Which database") < text.index("## D2: Which web framework?") < text.index("## Glossary")


def test_add_decision_with_no_research_says_none(log):
    add_decision(log, {**DATABASE_DECISION, "research": []}, today="2026-10-14")

    assert "- **Research:** none\n" in log.read_text()


@pytest.mark.parametrize("missing", ["question", "options", "choice", "reason", "proposed_by"])
def test_add_decision_refuses_a_missing_field(log, missing):
    fields = {key: value for key, value in DATABASE_DECISION.items() if key != missing}
    before = log.read_text()

    with pytest.raises(ValueError, match=missing):
        add_decision(log, fields, today="2026-10-14")
    assert log.read_text() == before


def test_settle_changes_only_that_entrys_status(log):
    add_decision(log, DATABASE_DECISION, today="2026-10-14")
    add_decision(log, {**DATABASE_DECISION, "question": "Which web framework?"}, today="2026-10-14")

    settle_decision(log, "D2")

    text = log.read_text()
    d1, d2 = text.split("## D2: ")
    assert "- **Status:** proposed\n" in d1
    assert "- **Status:** settled\n" in d2


def test_settle_refuses_an_unknown_number(log):
    add_decision(log, DATABASE_DECISION, today="2026-10-14")
    before = log.read_text()

    with pytest.raises(ValueError, match="D7"):
        settle_decision(log, "D7")
    assert log.read_text() == before


def test_replacing_marks_the_old_entry_and_links_the_new_one(log):
    add_decision(log, DATABASE_DECISION, today="2026-10-14")

    number = add_decision(log, {**DATABASE_DECISION, "choice": "PostgreSQL"}, today="2026-10-20", replaces="D1")

    text = log.read_text()
    old, new = text.split("## D2: ")
    assert number == "D2"
    assert "- **Status:** replaced by D2\n" in old
    assert "- **Status:** proposed\n- **Replaces:** D1\n" in new


def test_replacing_an_unknown_number_changes_nothing(log):
    add_decision(log, DATABASE_DECISION, today="2026-10-14")
    before = log.read_text()

    with pytest.raises(ValueError, match="D9"):
        add_decision(log, DATABASE_DECISION, today="2026-10-14", replaces="D9")
    assert log.read_text() == before


def test_settling_a_replaced_entry_is_refused(log):
    add_decision(log, DATABASE_DECISION, today="2026-10-14")
    add_decision(log, DATABASE_DECISION, today="2026-10-20", replaces="D1")

    with pytest.raises(ValueError, match="replaced"):
        settle_decision(log, "D1")


def test_a_failed_write_leaves_the_log_untouched(log, monkeypatch):
    add_decision(log, DATABASE_DECISION, today="2026-10-14")
    before = log.read_text()

    def disk_fails(source, target):
        raise OSError("disk full")

    monkeypatch.setattr("os.replace", disk_fails)
    with pytest.raises(OSError):
        add_decision(log, DATABASE_DECISION, today="2026-10-15")

    assert log.read_text() == before
    assert sorted(path.name for path in log.parent.iterdir()) == ["DECISIONS.md"]


def test_glossary_terms_go_into_the_logs_glossary(log):
    add_decision(log, {**DATABASE_DECISION, "glossary": {"SQLite": "a database kept in one file on disk"}}, today="2026-10-14")

    assert log.read_text().endswith("## Glossary\n\n- **SQLite:** a database kept in one file on disk\n")


def test_glossary_stays_alphabetical_without_duplicates(log):
    add_decision(log, {**DATABASE_DECISION, "glossary": {"WAL": "write-ahead log", "SQLite": "a file database"}}, today="2026-10-14")
    add_decision(log, {**DATABASE_DECISION, "glossary": {"sqlite": "said again", "API": "the part other programs call"}}, today="2026-10-14")

    glossary = log.read_text().split("## Glossary\n")[1]
    assert glossary == (
        "\n"
        "- **API:** the part other programs call\n"
        "- **SQLite:** a file database\n"
        "- **WAL:** write-ahead log\n"
    )


def test_a_glossary_that_is_not_terms_and_meanings_is_refused(log):
    before = log.read_text()

    with pytest.raises(ValueError, match="glossary"):
        add_decision(log, {**DATABASE_DECISION, "glossary": ["SQLite"]}, today="2026-10-14")
    assert log.read_text() == before


@pytest.mark.parametrize(
    "bad_fields, problem",
    [
        ({"options": "SQLite or PostgreSQL"}, "options"),
        ({"options": ["SQLite", ""]}, "options"),
        ({"question": ["Which database?"]}, "question"),
        ({"research": [{"link": "https://sqlite.org"}]}, "research"),
        ({"research": "https://sqlite.org"}, "research"),
        ({"question": "Which database?\n\n## D999: fake heading"}, "question"),
        ({"glossary": {"SQLite": "a file\n## D998: fake"}}, "glossary"),
    ],
    ids=["options as text", "an empty option", "question as a list", "research without a summary",
         "research as text", "line break in the question", "line break in a glossary meaning"],
)
def test_add_decision_refuses_malformed_fields(log, bad_fields, problem):
    before = log.read_text()

    with pytest.raises(ValueError, match=problem):
        add_decision(log, {**DATABASE_DECISION, **bad_fields}, today="2026-10-14")
    assert log.read_text() == before
