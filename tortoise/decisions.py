"""The decision log, docs/DECISIONS.md: adding, settling and replacing entries."""

import re
from pathlib import Path

from tortoise.project import write_safely

REQUIRED_FIELDS = ("question", "options", "choice", "reason", "proposed_by")
GLOSSARY_HEADING = "## Glossary\n"
ENTRY_HEADING = re.compile(r"^## D(\d+): ", re.MULTILINE)


def add_decision(log: Path, fields: dict, today: str, replaces: str | None = None) -> str:
    """Add a proposed decision just before the glossary and return its number, such as "D3"."""
    missing = [name for name in REQUIRED_FIELDS if not fields.get(name)]
    if missing:
        raise ValueError(f"decision is missing: {', '.join(missing)}")
    _check_shapes(fields)
    terms = fields.get("glossary") or {}

    text = log.read_text()
    numbers = [int(found) for found in ENTRY_HEADING.findall(text)]
    number = f"D{max(numbers, default=0) + 1}"
    entry = _format_entry(number, fields, today, replaces)
    if replaces:
        text = _set_status(text, replaces, f"replaced by {number}")

    glossary_at = text.rindex(GLOSSARY_HEADING)
    glossary = _merge_glossary(text[glossary_at + len(GLOSSARY_HEADING):], terms)
    write_safely(log, text[:glossary_at] + entry + "\n" + GLOSSARY_HEADING + glossary)
    return number


def _merge_glossary(existing: str, terms: dict[str, str]) -> str:
    """Add new terms to the glossary, A to Z. A term already defined (in any letter case) keeps its first meaning."""
    entries = dict(re.findall(r"^- \*\*(.+?):\*\* (.*)$", existing, re.MULTILINE))
    known = {term.lower() for term in entries}
    for term, meaning in terms.items():
        if term.lower() not in known:
            entries[term] = meaning
            known.add(term.lower())
    if not entries:
        return existing
    lines = [f"- **{term}:** {entries[term]}" for term in sorted(entries, key=str.lower)]
    return "\n" + "\n".join(lines) + "\n"


def _check_shapes(fields: dict) -> None:
    """Refuse fields of the wrong type, or with line breaks that could fake a heading in the log."""
    def is_line(value) -> bool:
        return isinstance(value, str) and bool(value.strip()) and "\n" not in value and "\r" not in value

    for name in ("question", "choice", "reason", "proposed_by"):
        if not is_line(fields[name]):
            raise ValueError(f"{name} must be one line of text")
    options = fields["options"]
    if not isinstance(options, list) or not all(is_line(option) for option in options):
        raise ValueError("options must be a list of one-line choices")
    research = fields.get("research") or []
    if not isinstance(research, list) or not all(
        isinstance(source, dict) and is_line(source.get("link")) and is_line(source.get("summary"))
        for source in research
    ):
        raise ValueError("research must be a list of sources, each with a one-line link and summary")
    terms = fields.get("glossary") or {}
    if not isinstance(terms, dict) or not all(is_line(term) and is_line(meaning) for term, meaning in terms.items()):
        raise ValueError("glossary must map each term to its one-line plain-English meaning")


def _format_entry(number: str, fields: dict, today: str, replaces: str | None) -> str:
    lines = [
        f"## {number}: {fields['question']}",
        "",
        "- **Status:** proposed",
        *([f"- **Replaces:** {replaces}"] if replaces else []),
        f"- **Proposed by:** {fields['proposed_by']} on {today}",
        "- **Options:**",
        *(f"  - {option}" for option in fields["options"]),
    ]
    research = fields.get("research") or []
    if research:
        lines.append("- **Research:**")
        lines.extend(f"  - [{source['link']}]({source['link']}): {source['summary']}" for source in research)
    else:
        lines.append("- **Research:** none")
    lines.append(f"- **Choice:** {fields['choice']}")
    lines.append(f"- **Reason:** {fields['reason']}")
    return "\n".join(lines) + "\n"


def settle_decision(log: Path, number: str) -> None:
    """Mark a decision settled. Only the author settles decisions; the skill never calls this on its own."""
    text = log.read_text()
    if _status(text, number).startswith("replaced"):
        raise ValueError(f"{number} has been replaced and cannot be settled")
    write_safely(log, _set_status(text, number, "settled"))


def _entry_span(text: str, number: str) -> tuple[int, int]:
    """Where an entry starts and ends: from its heading to the next heading."""
    start = text.find(f"## {number}: ")
    if start == -1:
        raise ValueError(f"no decision {number} in the log")
    end = text.find("\n## ", start)
    return start, len(text) if end == -1 else end


def _status(text: str, number: str) -> str:
    start, end = _entry_span(text, number)
    return re.search(r"^- \*\*Status:\*\* (.*)$", text[start:end], re.MULTILINE).group(1)


def _set_status(text: str, number: str, status: str) -> str:
    start, end = _entry_span(text, number)
    entry = re.sub(r"^(- \*\*Status:\*\* ).*$", rf"\g<1>{status}", text[start:end], count=1, flags=re.MULTILINE)
    return text[:start] + entry + text[end:]


def settled_decisions(text: str) -> list[tuple[str, str]]:
    """The question and choice of every settled decision, oldest first."""
    found = []
    for match in re.finditer(r"^## (D\d+): (.*)$", text, re.MULTILINE):
        number, question = match.groups()
        if _status(text, number) == "settled":
            start, end = _entry_span(text, number)
            choice = re.search(r"^- \*\*Choice:\*\* (.*)$", text[start:end], re.MULTILINE)
            found.append((question, choice.group(1) if choice else ""))
    return found
