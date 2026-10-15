import pytest

from tortoise.markdown import to_html


@pytest.mark.parametrize(
    "markdown, html",
    [
        ("Hello <script>alert(1)</script> & bye", "<p>Hello &lt;script&gt;alert(1)&lt;/script&gt; &amp; bye</p>"),
        ("one line\nsecond line\n\nnew paragraph", "<p>one line second line</p>\n<p>new paragraph</p>"),
        ("## Data model", "<h2>Data model</h2>"),
        ("**bold <b>** and `x < y`", "<p><strong>bold &lt;b&gt;</strong> and <code>x &lt; y</code></p>"),
        ("`**not bold**`", "<p><code>**not bold**</code></p>"),
        ("[SQLite](https://sqlite.org/a?b=1&c=2)", '<p><a href="https://sqlite.org/a?b=1&amp;c=2">SQLite</a></p>'),
        ("[local](#d2)", '<p><a href="#d2">local</a></p>'),
        ('[x](javascript:alert(1))', "<p>x</p>"),
        ('[x](" onclick="bad)', "<p>x</p>"),
    ],
    ids=[
        "escapes html",
        "joins lines into paragraphs",
        "heading",
        "bold and inline code are escaped",
        "inline code is not formatted",
        "safe link",
        "same-page link",
        "javascript link is dropped",
        "attribute-breaking link is dropped",
    ],
)
def test_inline_and_blocks(markdown, html):
    assert to_html(markdown) == html


def test_heading_offset_pushes_headings_down():
    assert to_html("# Architecture\n\n## Parts", heading_offset=1) == "<h2>Architecture</h2>\n<h3>Parts</h3>"


def test_nested_unordered_list():
    markdown = "- **Options:**\n  - SQLite\n  - PostgreSQL\n- **Choice:** SQLite"
    assert to_html(markdown) == (
        "<ul>\n"
        "<li><strong>Options:</strong>\n<ul>\n<li>SQLite</li>\n<li>PostgreSQL</li>\n</ul></li>\n"
        "<li><strong>Choice:</strong> SQLite</li>\n"
        "</ul>"
    )


def test_ordered_list():
    assert to_html("1. Browser sends the ID\n2. Server returns labs") == (
        "<ol>\n<li>Browser sends the ID</li>\n<li>Server returns labs</li>\n</ol>"
    )


def test_table():
    markdown = "| Field | Type |\n|---|---|\n| name | text |\n| born | date <now> |"
    assert to_html(markdown) == (
        "<table>\n"
        "<thead><tr><th>Field</th><th>Type</th></tr></thead>\n"
        "<tbody>\n<tr><td>name</td><td>text</td></tr>\n<tr><td>born</td><td>date &lt;now&gt;</td></tr>\n</tbody>\n"
        "</table>"
    )


def test_mermaid_block_becomes_an_escaped_diagram():
    markdown = "```mermaid\ngraph TD\n  A[Browser] -->|sends <ID>| B\n```"
    assert to_html(markdown) == '<pre class="mermaid">graph TD\n  A[Browser] --&gt;|sends &lt;ID&gt;| B</pre>'


def test_other_code_block_is_escaped_and_not_formatted():
    markdown = "```\n**x** <y>\n```"
    assert to_html(markdown) == "<pre><code>**x** &lt;y&gt;</code></pre>"


def test_task_checkboxes():
    assert to_html("- [x] Task 1: store\n- [ ] Task 2: chart") == (
        "<ul>\n"
        '<li class="task done"><span class="box" aria-label="done">✓</span><span>Task 1: store</span></li>\n'
        '<li class="task"><span class="box" aria-label="not done"></span><span>Task 2: chart</span></li>\n'
        "</ul>"
    )


def test_quoted_lines_become_one_quote_block_with_their_own_formatting():
    text = "> **Status.** Built and tested.\n> See [the plan](PLAN.md).\n\nAfter."

    assert to_html(text) == (
        '<blockquote>\n<p><strong>Status.</strong> Built and tested. See <a href="PLAN.md">the plan</a>.</p>\n'
        "</blockquote>\n<p>After.</p>"
    )


def test_a_line_of_three_dashes_or_stars_is_a_horizontal_rule():
    assert to_html("Above\n\n---\n\nBelow\n\n***") == "<p>Above</p>\n<hr>\n<p>Below</p>\n<hr>"


def test_single_stars_are_italics_and_double_stars_stay_bold():
    assert to_html("the *category* and **bold** and 2 * 3 * 4") == (
        "<p>the <em>category</em> and <strong>bold</strong> and 2 * 3 * 4</p>"
    )
