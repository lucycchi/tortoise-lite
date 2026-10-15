import pytest

from tortoise.decisions import add_decision, settle_decision
from tortoise.page import build_diagram_pages, build_document_page, build_page
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


def test_page_shows_progress_requirements_and_final_checks_in_order(project):
    docs = project / "docs"
    (docs / "SPEC.md").write_text("# Spec\n\n- R1: store lab results\n- R2: chart them\n")
    (docs / "PLAN.md").write_text(
        "# Plan\n\n## Milestone 1: Records\n\n- [x] Task 1: store. Requirements: R1\n- [ ] Task 2: list. Requirements: R1\n"
        "\n## Milestone 2: Charts\n\n- [ ] Task 3: chart. Requirements: R2\n"
    )
    (docs / "FINAL_CHECKS.md").write_text("# Final checks\n\n- QA: no bugs found.\n")

    page = build_page(project).read_text()

    assert page.index('id="summary"') < page.index('id="progress"') < page.index('id="requirements"') \
        < page.index('id="architecture"') < page.index('id="decisions"') < page.index('id="gates"') \
        < page.index('id="final-checks"')
    progress = page.split('<section id="progress">')[1].split("</section>")[0]
    assert "<h3>Milestone 1: Records (1 of 2 done)</h3>" in progress
    assert '<li class="task done"><span class="box" aria-label="done">✓</span><span>Task 1: store. Requirements: R1</span></li>' in progress
    assert "<h3>Milestone 2: Charts (0 of 1 done)</h3>" in progress
    assert "R2: chart them" in page.split('<section id="requirements">')[1]
    assert "QA: no bugs found." in page.split('<section id="final-checks">')[1]


def test_page_without_a_plan_says_so(project):
    page = build_page(project).read_text()

    assert "The plan is not written yet." in page
    assert "The requirements are not written yet." in page
    assert "Final checks have not run yet." in page


def test_a_document_page_is_written_beside_its_source_with_diagrams_drawn(tmp_path):
    source = tmp_path / "ARCHITECTURE.md"
    source.write_text(ARCHITECTURE.replace("# Architecture", "# Lab <tracker> architecture"))

    path = build_document_page(source)

    page = path.read_text()
    assert path == tmp_path / "ARCHITECTURE.html"
    assert "<title>Lab &lt;tracker&gt; architecture</title>" in page
    assert '<pre class="mermaid">graph TD' in page
    assert "Clinicians lose time finding lab trends." in page
    assert 'securityLevel: "strict"' in page


def test_a_document_without_a_heading_is_titled_by_its_file_name(tmp_path):
    source = tmp_path / "flows.md"
    source.write_text("```mermaid\ngraph TD\n  A --> B\n```\n")

    assert "<title>flows</title>" in build_document_page(source).read_text()


def test_every_record_with_diagrams_gets_its_own_page_and_the_rest_do_not(project):
    docs = project / "docs"
    (docs / "ARCHITECTURE.md").write_text(ARCHITECTURE)
    (docs / "SPEC.md").write_text("# Spec\n\n- R1: store lab results\n")

    written = build_diagram_pages(docs)

    assert written == [docs / "ARCHITECTURE.html"]
    assert not (docs / "SPEC.html").exists()
