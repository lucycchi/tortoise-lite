"""Building the project page, docs/project.html, from the project's records.

The page is generated, never edited by hand: summary, architecture, decisions,
then the milestone gates.
"""

import html
import re
from pathlib import Path

from tortoise.decisions import settled_decisions
from tortoise.markdown import to_html
from tortoise.project import STAGES, load_state, write_safely

KEY_DECISIONS_SHOWN = 5
MERMAID_URL = "https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.esm.min.mjs"


def build_page(root: Path) -> Path:
    docs = root / "docs"
    state = load_state(root)
    name = html.escape(state["name"])
    summary, architecture = _split_summary(_read(docs / "ARCHITECTURE.md"))
    decisions_text = _read(docs / "DECISIONS.md")

    body = "\n".join(
        [
            f"<header>\n<h1>{name}</h1>\n<p class=\"stage\">Current stage: {STAGES[state['stage']]}</p>\n</header>",
            _section("summary", "Summary", to_html(summary, heading_offset=1), "The summary is not written yet.", own_heading=True)
            + "\n" + _key_decisions(decisions_text),
            _section("architecture", "Architecture", to_html(architecture, heading_offset=1), "The architecture is not written yet."),
            _section("decisions", "Decisions", to_html(decisions_text, heading_offset=1), "The decision log is not written yet."),
            _section("gates", "Milestone gates", _gates(docs / "gates"), "No milestone gates yet.", own_heading=True),
        ]
    )
    path = docs / "project.html"
    write_safely(path, PAGE.format(title=name, body=body, style=STYLE, script=SCRIPT.replace("MERMAID_URL", MERMAID_URL)))
    return path


def _read(path: Path) -> str:
    return path.read_text() if path.exists() else ""


def _split_summary(architecture: str) -> tuple[str, str]:
    """Take the "## Summary" section out of the architecture document so it can lead the page."""
    match = re.search(r"^## Summary\n(.*?)(?=^## |\Z)", architecture, re.MULTILINE | re.DOTALL)
    if not match:
        return "", architecture
    return match.group(1).strip(), architecture[: match.start()] + architecture[match.end():]


def _section(anchor: str, heading: str, content: str, missing: str, own_heading: bool = False) -> str:
    """A page section. Records bring their own top heading unless own_heading is set or the record is missing."""
    if not content:
        content = f"<h2>{heading}</h2>\n<p>{missing}</p>"
    elif own_heading:
        content = f"<h2>{heading}</h2>\n{content}"
    return f'<section id="{anchor}">\n{content}\n</section>'


def _key_decisions(decisions_text: str) -> str:
    settled = settled_decisions(decisions_text)[-KEY_DECISIONS_SHOWN:]
    if not settled:
        return "<h3>Key decisions</h3>\n<p>No settled decisions yet.</p>"
    items = "\n".join(f"<li>{html.escape(question)} {html.escape(choice)}</li>" for question, choice in settled)
    return f"<h3>Key decisions</h3>\n<ul>\n{items}\n</ul>"


def _gates(folder: Path) -> str:
    if not folder.is_dir():
        return ""
    numbered = []
    for path in folder.glob("milestone-*.md"):
        match = re.fullmatch(r"milestone-(\d+)\.md", path.name)
        if match:
            numbered.append((int(match.group(1)), path))
    return "\n".join(to_html(path.read_text(), heading_offset=2) for _, path in sorted(numbered))


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{style}</style>
</head>
<body>
<main>
{body}
</main>
<script type="module">{script}</script>
</body>
</html>
"""

STYLE = """
:root {
  --background: #fbfaf7; --text: #1f2328; --muted: #59636e; --border: #d8dee4;
  --panel: #f1efe9; --accent: #2f6f5e; --error-background: #fdecea; --error-text: #8a1c12;
}
@media (prefers-color-scheme: dark) {
  :root {
    --background: #15181c; --text: #e6e8eb; --muted: #9aa4af; --border: #30363d;
    --panel: #1e2328; --accent: #7cc4ad; --error-background: #3a1d1b; --error-text: #ffb4a9;
  }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--background); color: var(--text);
  font: 16px/1.6 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width: 860px; margin: 0 auto; padding: 24px 16px 64px; }
header { border-bottom: 2px solid var(--accent); margin-bottom: 24px; }
h1 { margin: 0 0 4px; font-size: 1.9rem; }
.stage { margin: 0 0 12px; color: var(--muted); }
section { margin-top: 40px; }
h2 { font-size: 1.4rem; border-bottom: 1px solid var(--border); padding-bottom: 4px; }
h3 { font-size: 1.15rem; margin-top: 28px; }
a { color: var(--accent); overflow-wrap: anywhere; }
code { background: var(--panel); padding: 1px 4px; border-radius: 4px; font-size: 0.9em; }
pre { background: var(--panel); padding: 12px; border-radius: 6px; overflow-x: auto; }
pre code { padding: 0; background: none; }
pre.mermaid { background: #ffffff; text-align: center; }
table { display: block; overflow-x: auto; border-collapse: collapse; margin: 16px 0; }
th, td { border: 1px solid var(--border); padding: 6px 10px; text-align: left; vertical-align: top; }
th { background: var(--panel); }
.diagram-error { background: var(--error-background); color: var(--error-text);
  border-left: 4px solid var(--error-text); padding: 12px; border-radius: 6px; }
.diagram-error pre { background: transparent; color: inherit; padding: 8px 0 0; margin: 0; }
@media print { pre, table, .diagram-error { break-inside: avoid; } }
"""

# Draws every diagram with Mermaid in strict mode, so diagram text cannot run as script.
# A diagram that fails to parse, or cannot be drawn because Mermaid did not load, is
# replaced by an error box showing its source, never left blank. Checked by eye in a
# browser, since the unit tests cannot run the page's script.
SCRIPT = """
function showError(node, reason) {
  const box = document.createElement("div");
  box.className = "diagram-error";
  box.textContent = "This diagram could not be drawn: " + reason;
  const source = document.createElement("pre");
  source.textContent = node.textContent;
  box.appendChild(source);
  node.replaceWith(box);
}
const diagrams = [...document.querySelectorAll("pre.mermaid")];
try {
  const { default: mermaid } = await import("MERMAID_URL");
  mermaid.initialize({ startOnLoad: false, securityLevel: "strict" });
  const drawable = [];
  for (const node of diagrams) {
    try {
      await mermaid.parse(node.textContent);
      drawable.push(node);
    } catch (error) {
      showError(node, String(error.message || error).split("\\n")[0]);
    }
  }
  await mermaid.run({ nodes: drawable });
  // Keep each diagram at its natural size so its text stays readable on a phone;
  // a diagram wider than the screen scrolls sideways inside its own box.
  for (const svg of document.querySelectorAll("pre.mermaid svg")) {
    svg.style.maxWidth = "none";
    svg.setAttribute("width", svg.viewBox.baseVal.width);
  }
} catch (error) {
  for (const node of diagrams) {
    if (node.isConnected && !node.dataset.processed) showError(node, "the Mermaid library did not load (are you offline?)");
  }
}
"""
