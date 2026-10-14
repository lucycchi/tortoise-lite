import pytest

from tortoise.decisions import add_decision, settle_decision
from tortoise.page import build_page
from tortoise.project import init_project

ARCHITECTURE = """# Architecture

## Summary

Clinicians lose time finding lab trends. A single page charts each patient's labs.

## Main parts

```mermaid
graph TD
  A[Browser] -->|sends the patient's ID| B[API server]
```

The browser asks the API server for one patient's labs.

## Glossary

- **API:** the part other programs call.
"""


def decision(question, choice):
    return {
        "question": question,
        "options": [choice, "something else"],
        "choice": choice,
        "reason": "it fits",
        "proposed_by": "the author",
    }


@pytest.fixture
def project(tmp_path):
    init_project(tmp_path, name="Lab <tracker>", test_command="pytest")
    return tmp_path


def test_page_is_written_to_docs_and_shows_name_and_stage(project):
    path = build_page(project)

    page = path.read_text()
    assert path == project / "docs" / "project.html"
    assert "<title>Lab &lt;tracker&gt;</title>" in page
    assert "<h1>Lab &lt;tracker&gt;</h1>" in page
    assert "Current stage: PRD review" in page


def test_page_with_no_records_says_what_is_missing(project):
    page = build_page(project).read_text()

    assert "The summary is not written yet." in page
    assert "The architecture is not written yet." in page
    assert "No milestone gates yet." in page


def test_summary_comes_from_the_architecture_summary_section(project):
    (project / "docs" / "ARCHITECTURE.md").write_text(ARCHITECTURE)

    page = build_page(project).read_text()

    summary, rest = page.split('<section id="architecture">')
    assert "Clinicians lose time finding lab trends." in summary
    assert "Clinicians lose time finding lab trends." not in rest
    assert '<pre class="mermaid">graph TD\n  A[Browser] --&gt;|sends the patient\'s ID| B[API server]</pre>' in rest
    assert "<h3>Main parts</h3>" in rest


def test_key_decisions_list_settled_decisions_only(project):
    log = project / "docs" / "DECISIONS.md"
    add_decision(log, decision("Which database?", "SQLite"), today="2026-10-14")
    add_decision(log, decision("Which chart library?", "Chart.js"), today="2026-10-14")
    settle_decision(log, "D1")

    page = build_page(project).read_text()

    summary = page.split('<section id="architecture">')[0]
    assert "Which database? SQLite" in summary
    assert "Which chart library?" not in summary
    assert "Which chart library?" in page


def test_gates_appear_in_milestone_order(project):
    gates = project / "docs" / "gates"
    gates.mkdir()
    for number in (10, 2, 1):
        (gates / f"milestone-{number}.md").write_text(f"# Milestone {number} gate\n\nTests passed.\n")

    page = build_page(project).read_text()

    assert page.index("Milestone 1 gate") < page.index("Milestone 2 gate") < page.index("Milestone 10 gate")


def test_research_links_are_clickable(project):
    log = project / "docs" / "DECISIONS.md"
    fields = {**decision("Which database?", "SQLite"),
              "research": [{"link": "https://sqlite.org/whentouse.html", "summary": "SQLite suits one server."}]}
    add_decision(log, fields, today="2026-10-14")

    page = build_page(project).read_text()

    assert '<a href="https://sqlite.org/whentouse.html">https://sqlite.org/whentouse.html</a>: SQLite suits one server.' in page


def test_page_loads_a_mermaid_release_without_the_known_label_injection_flaw():
    # GHSA-7rqq-prvp-x9jh: Mermaid before 11.10.0 lets a sequence-diagram label run script.
    from tortoise.page import MERMAID_URL

    version = tuple(int(part) for part in MERMAID_URL.split("mermaid@")[1].split("/")[0].split("."))
    assert version >= (11, 10, 0)
