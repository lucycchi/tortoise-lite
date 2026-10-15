## Top 5 issues

1. [tortoise/page.py:17](tortoise/page.py:17) — `MERMAID_URL` pins Mermaid 11.4.1, while [line 151](tortoise/page.py:151) relies on `securityLevel: "strict"` to make records safe. Mermaid 11.4.1 is in the affected range for a critical sequence-diagram XSS fixed in 11.10.0. The advisory describes exploitation under Mermaid’s default configuration, which is `strict`. A model-authored architecture record can therefore execute script when the author opens `project.html`, directly contradicting SPEC line 84. [Official advisory](https://github.com/mermaid-js/mermaid/security/advisories/GHSA-7rqq-prvp-x9jh), [security-level documentation](https://mermaid.js.org/config/schema-docs/config-properties-securitylevel.html). **DEFINITELY WRONG.**

2. [tortoise/gate.py:47](tortoise/gate.py:47) records only `{"milestone": ..., "passed": ...}`. [tortoise/stages.py:103](tortoise/stages.py:103) trusts that cached result without binding it to a commit or worktree snapshot. Code or tests can change after a passing gate, and `approve` will commit the now-untested tree. This defeats SPEC line 128’s failing-test approval block. **DEFINITELY WRONG.**

3. [tortoise/stages.py:87](tortoise/stages.py:87) persists approval before Git operations; [lines 90–97](tortoise/stages.py:90) roll back only working-tree files. If `git commit` fails, the approval remains staged in the index. If the commit succeeds but `git tag` fails, the approval remains committed in `HEAD` even though the working JSON is rolled back. The repository then has conflicting approval histories. **DEFINITELY WRONG.**

4. [tortoise/stages.py:89](tortoise/stages.py:89) limits `git add` for non-gate approvals, but [line 91](tortoise/stages.py:91) runs an unrestricted `git commit`. Any unrelated file already staged by the author is included, contradicting [lines 60–61](tortoise/stages.py:60), which promise to leave unrelated work alone. **DEFINITELY WRONG.**

5. [tortoise/decisions.py:15](tortoise/decisions.py:15) checks required fields only for truthiness; [lines 57–62](tortoise/decisions.py:57) assume particular list/object shapes. A string `options` value becomes one bullet per character, malformed research raises an uncaught exception, and embedded newlines can inject fake `## D999:` headings that [line 23](tortoise/decisions.py:23) later treats as real decision numbers. Model-produced forms can therefore corrupt the decision log. **DEFINITELY WRONG.**

## Full findings

### Correctness

- [tortoise/gate.py:47](tortoise/gate.py:47), [tortoise/stages.py:103](tortoise/stages.py:103) — stale gate results can approve later, failing code. **DEFINITELY WRONG.**

- [tortoise/decisions.py:15](tortoise/decisions.py:15) — malformed but truthy decision fields produce corrupt records or tracebacks. **DEFINITELY WRONG.**

### Security

- [tortoise/page.py:17](tortoise/page.py:17) — known-vulnerable Mermaid 11.4.1 makes model-authored diagrams an XSS path despite `strict` mode. **DEFINITELY WRONG.**

### Data loss

- [tortoise/stages.py:87](tortoise/stages.py:87) — failed approval cannot restore the Git index or undo a commit made before tag failure. **DEFINITELY WRONG.**

- [tortoise/stages.py:89](tortoise/stages.py:89) — unrelated pre-staged changes are silently swept into approval commits. **DEFINITELY WRONG.**

### Spec mismatches

- [tortoise/stages.py:72](tortoise/stages.py:72) records only a tag in each approval, and [tortoise/gate.py:25](tortoise/gate.py:25) uses that tag as the review base. Literal reading: SPEC line 128 requires the commit identity in `tortoise.json`, which is absent. Alternative reading: the tag is intended as a stable reference to that commit. A deleted or moved tag makes the distinction observable. **UNCLEAR.**

- [tortoise/stages.py:44](tortoise/stages.py:44) refuses to advance an approved plan with no milestone headings. Literal reading: SPEC line 137 says `stage next` refuses *only* for a missing approval. Practical reading: structurally invalid plans are implicit precondition failures. **UNCLEAR.**

### Tests that would not catch a realistic break

- [tests/test_stages.py:159](tests/test_stages.py:159) approves immediately after running the gate; it never changes code afterward or exercises commit-hook/tag failure and pre-staged files. Without these cases, the three approval-integrity defects can regress unnoticed. **ADDITION:** roughly 50–80 test lines using the existing Git fixture; no new moving parts.

- [tests/test_decisions.py:63](tests/test_decisions.py:63) covers missing fields, but not wrong types, malformed research objects, or newline-injected headings. Without them, malformed model output can corrupt numbering and still pass the suite. **ADDITION:** roughly 30–40 test lines; no new moving parts.

- [tests/test_markdown.py:65](tests/test_markdown.py:65) checks only escaped Mermaid source, not execution of the pinned runtime. It cannot detect a vulnerable Mermaid release. **ADDITION:** about 10 lines for a minimum-safe-version guard; a full browser exploit regression would require roughly 40–80 lines plus a headless-browser dependency.

`pytest` was unavailable (`No module named pytest`), so the suite did not run. All nine Python modules parsed successfully, and the worktree remained clean.