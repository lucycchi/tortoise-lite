# Sample run: glue notes

From running a made-up project ("lab trend tracker") through every stage on 2026-10-14, with Claude playing the author. Each note is a place where a called skill did not fit Tortoise Lite as written, and how it was handled. Notes 15, 18 and 21 were decided by the author: plans may hold real code up to about a tenth of their lines, explained; a fresh Claude reviewer replaces gstack `/review` at gates; `/cso` stays in final checks.

1. PRD location unspecified. Fix in SKILL.md: save the PRD the author gives as docs/PRD.md.
2. /office-hours is heavy (brain context, web research gate, Codex second opinion, visual mockups, founder signals, writes to the user's developer profile). For Tortoise: tell it builder mode, and skip web research, second opinion and mockups unless the author asks.
3. /office-hours already dual-writes docs/designs/<topic>.md. Fix: tell it to make the repo copy docs/DESIGN.md instead of copying afterwards (avoids two copies).
4. With a PRD review, /office-hours's own escape hatch applies ("fully formed plan" -> skip questions, run premises + alternatives). Fix: say so explicitly; it makes the Ideas stage short.
5. Builder mode pushes "10x / wild" ideas: tell it scope additions go under Open Questions, not into the approach (scope rule).
6. Brainstorming repeats office-hours's "propose 2-3 approaches"; tell it the approach is settled (DESIGN.md + its decision) and to skip that step.
7. Brainstorming's hard gate says spec approval "only permits invoking writing-plans"; the Tortoise override (go to architecture) must be given before it starts. Works when stated up front.
8. Brainstorming commits the spec itself; Tortoise commits at approval. Tell it not to commit (tortoise approve does).
9. The spec review runs with Codex reading docs/ directly (no need to paste the files into the prompt): simpler command in SKILL.md.
10. The spec review came back at ~2,100 words despite "a short review is a good result"; the ADDITION cap held (1). The plain-language sorting step for the author is essential.
11. Requirement IDs must be whole numbers (R12, never R2a): the coverage check silently ignores R2a. Say so in SKILL.md. (Tool could warn about R<n><letter>; small, optional.)
12. engineering:system-design is generic and defaults to ASCII diagrams and scale/caching/queue sections; SKILL.md's Mermaid + diagram rules must override, and say to skip sections that do not apply.
13. Diagram rule to add: one-way arrows with short labels; put return values in the text or a sequence diagram (two-way labelled arrows between the same boxes overlap and become unreadable).
14. writing-plans puts a checkbox on every STEP inside every task. Tortoise counts only checkbox lines directly under "## Milestone N" (it stops at any heading), so the plan must be: milestone heading, task checkbox list, then task details under "### Task N" headings. SKILL.md must say this layout.
15. writing-plans requires full code in every step ("no placeholders"), which clashes with Tortoise's plain-English rule and duplicates the inline TDD build. Sample used plain-English steps with exact test examples and real function names. NEEDS THE AUTHOR'S CALL.
16. writing-plans' required header names subagent-driven-development; replace with a Tortoise inline line. Its "Global constraints" and "Review focus" sections are worth keeping.
17. TOOL BUG (fixed in tortoise-lite, test added): `git diff <review base>` hid every NEW file, because they stay untracked until approval. The gate now marks new non-ignored, non-secret files with git add --intent-to-add, so both reviewers see the milestone's code.
18. gstack /review does not fit the gate: it needs an origin remote and a feature branch (diffs against the default branch's merge-base and stops on main). Tortoise works on main with tags. Sample used a fresh Claude agent with prompts/code-review.md as the second reviewer. NEEDS THE AUTHOR'S CALL (spec change).
19. tortoise gate rebuilds the page at step 1, before the architecture check updates docs, so reviewers saw a stale page summary. SKILL.md step 6 rebuilds before approval; reviewers should be told the page is rebuilt last (or ignore project.html).
20. The spec's display rule (R8) changed during the build with no re-approval; the requirement-change loop was cut for scope. Known gap.
21. /cso is protocol-driven (helper, 10-minute budget, JSON submissions, challenge pass; runtime scanners need Docker). Heavy for small projects. Not run fully on the sample. NEEDS THE AUTHOR'S CALL.
22. TOOL BUG (fixed, test added): approving final checks committed only docs/ and tortoise.json, leaving the README and any QA fixes uncommitted. Now commits all work, like a gate.
23. Two reviewers found different real bugs at both gates (Codex: infinity values, stale page; Claude: non-ASCII digits, uneven-average 10%). Evidence for keeping two reviewers.

24. Trial of the new architecture prompts on the finished sample: Codex's architecture review caught, from the design alone, the floating-point 10% problem and the argparse exit-code problem that the real run only found at the gates, plus a missing index for the one-second target. Codex's architecture check caught a code-versus-design mismatch the Claude check missed (the database is opened before input is checked). Both prompts now say that plain-word field types in database diagrams are deliberate.

## Glossary

- **Glue:** the instructions that make one skill hand its output to the next in the form Tortoise expects.
- **Gate:** the check at the end of a milestone.
