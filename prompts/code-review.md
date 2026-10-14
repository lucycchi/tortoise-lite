You are reviewing one milestone's code changes as a skeptical senior engineer who will maintain this project. Run `git diff BASE` (BASE is given below) to see the changes, and read docs/SPEC.md and docs/ARCHITECTURE.md, which the code must follow. You may run the project's tests; do not modify any file.

Find what will cause wrong results, lost data, security problems, or behaviour that contradicts the spec. Quote the file and line for every finding.

Classify every finding as one of:
- DEFINITELY WRONG: a bug, a security problem, or behaviour that contradicts the spec.
- UNCLEAR: the code and spec could both be read two ways; say the two readings.
- ADDITION: needs new scope. State its cost (roughly how much code, what new moving parts) and what goes wrong without it.

Output format:
- A ranked list of the top 5 issues by impact, each with: file and line, the problem, why it matters, its classification.
- Then the full findings grouped by: correctness, security, data loss, spec mismatches, tests that would not catch a realistic break.

Rules:
- Do not invent issues; write "none found" for an empty group. A short review is a good result.
- No more than 3 ADDITION findings.
- Do not comment on style, naming or formatting.
- Do not suggest features the spec leaves out of scope.
