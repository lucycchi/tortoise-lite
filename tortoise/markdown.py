"""A small Markdown-to-HTML converter for the project's records.

It covers only what the records use: headings, paragraphs, lists, bold, inline
code, links, tables and fenced code blocks, with ```mermaid blocks becoming
diagrams. All record text is escaped, so nothing in a record can run as script.
"""

import html
import re

HEADING = re.compile(r"^(#{1,6}) (.*)$")
LIST_ITEM = re.compile(r"^( *)([-*]|\d+\.) (.*)$")
TABLE_SEPARATOR = re.compile(r"^\|?\s*:?-{3,}")
CODE_SPAN = re.compile(r"`([^`]+)`")
LINK = re.compile(r"\[([^\]]+)\]\(([^()\n]*(?:\([^()\n]*\)[^()\n]*)*)\)")
BOLD = re.compile(r"\*\*(.+?)\*\*")
TASK_BOX = re.compile(r"^\[([ xX])\] (.*)$")
# A link is kept only if it is a web address, a same-page anchor or a plain relative path.
SAFE_URL = re.compile(r"^(https?://[^\s\"'<>`]+|#[\w-]+|[\w./-]+)$")


def to_html(text: str, heading_offset: int = 0) -> str:
    lines = text.split("\n")
    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
        elif line.startswith("```"):
            language = line[3:].strip()
            end = i + 1
            while end < len(lines) and not lines[end].startswith("```"):
                end += 1
            body = html.escape("\n".join(lines[i + 1:end]), quote=False)
            if language == "mermaid":
                blocks.append(f'<pre class="mermaid">{body}</pre>')
            else:
                blocks.append(f"<pre><code>{body}</code></pre>")
            i = end + 1
        elif match := HEADING.match(line):
            level = min(len(match.group(1)) + heading_offset, 6)
            blocks.append(f"<h{level}>{_inline(match.group(2))}</h{level}>")
            i += 1
        elif line.startswith("|") and i + 1 < len(lines) and TABLE_SEPARATOR.match(lines[i + 1]):
            end = i + 2
            while end < len(lines) and lines[end].startswith("|"):
                end += 1
            blocks.append(_table(lines[i], lines[i + 2:end]))
            i = end
        elif LIST_ITEM.match(line):
            end = i
            while end < len(lines) and LIST_ITEM.match(lines[end]):
                end += 1
            items = [LIST_ITEM.match(item).groups() for item in lines[i:end]]
            blocks.append(_list([(len(indent), marker[0].isdigit(), body) for indent, marker, body in items])[0])
            i = end
        else:
            end = i
            while end < len(lines) and lines[end].strip() and not _starts_block(lines[end]):
                end += 1
            end = max(end, i + 1)
            blocks.append(f"<p>{_inline(' '.join(part.strip() for part in lines[i:end]))}</p>")
            i = end
    return "\n".join(blocks)


def _starts_block(line: str) -> bool:
    return bool(line.startswith(("```", "|")) or HEADING.match(line) or LIST_ITEM.match(line))


def _list(items: list[tuple[int, bool, str]], start: int = 0) -> tuple[str, int]:
    """Render the list beginning at items[start]; deeper-indented items become a nested list.

    Returns the HTML and the index of the first item that does not belong to this list.
    """
    indent, ordered, _ = items[start]
    tag = "ol" if ordered else "ul"
    rendered = []
    i = start
    while i < len(items) and items[i][0] == indent:
        text, css = _inline(items[i][2]), ""
        if checkbox := TASK_BOX.match(items[i][2]):
            done = checkbox.group(1) != " "
            box = '<span class="box" aria-label="done">✓</span>' if done else '<span class="box" aria-label="not done"></span>'
            text, css = f"{box}<span>{_inline(checkbox.group(2))}</span>", ' class="task done"' if done else ' class="task"'
        i += 1
        if i < len(items) and items[i][0] > indent:
            nested, i = _list(items, i)
            text += "\n" + nested
        rendered.append(f"<li{css}>{text}</li>")
    return f"<{tag}>\n" + "\n".join(rendered) + f"\n</{tag}>", i


def _table(header: str, rows: list[str]) -> str:
    def cells(row: str) -> list[str]:
        return [_inline(cell.strip()) for cell in row.strip().strip("|").split("|")]

    head = "".join(f"<th>{cell}</th>" for cell in cells(header))
    body = "\n".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in cells(row)) + "</tr>" for row in rows)
    return f"<table>\n<thead><tr>{head}</tr></thead>\n<tbody>\n{body}\n</tbody>\n</table>"


def _inline(text: str) -> str:
    """Format one line of text. Code spans are kept verbatim; everything is escaped."""
    parts = CODE_SPAN.split(text)
    out = []
    for index, part in enumerate(parts):
        if index % 2:
            out.append(f"<code>{html.escape(part, quote=False)}</code>")
        else:
            out.append(_links(part))
    return "".join(out)


def _links(text: str) -> str:
    out = []
    position = 0
    for match in LINK.finditer(text):
        out.append(_bold(text[position:match.start()]))
        label, url = _bold(match.group(1)), match.group(2)
        if SAFE_URL.match(url):
            out.append(f'<a href="{html.escape(url)}">{label}</a>')
        else:
            out.append(label)
        position = match.end()
    out.append(_bold(text[position:]))
    return "".join(out)


def _bold(text: str) -> str:
    return BOLD.sub(r"<strong>\1</strong>", html.escape(text, quote=False))
