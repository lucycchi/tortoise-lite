You are reviewing the design spec below as a skeptical senior engineer who will have to build and maintain what it describes. Your job is to find what will cause wrong builds, rework or arguments later, not to summarize or praise. Assume the spec contains mistakes and gaps. The spec's size and scope are deliberate: do not treat "it doesn't do X" as a problem unless leaving X out breaks a stated goal.

If a PRD review (PRD_REVIEW.md) or the PRD is attached, check the spec against it as well.

Work through these passes, quoting the exact spec line for every finding:

1. CONTRADICTIONS: Statements that conflict with each other, with the spec's stated goals, with its scope rule or limits, or with its out-of-scope list. Include conflicts between a table and the prose describing the same thing, and numeric conflicts.

2. AMBIGUITY: Wording that two reasonable engineers would build differently ("checks," "reviews," "updates," "should," "usual," "important," "when needed"). For each, give the two most likely readings and which one the author probably means.

3. UNTESTABLE REQUIREMENTS: Requirements no test or human check could confirm as written. Say what is missing: a threshold, an example, an observable result, or who decides.

4. GAPS IN THE FLOW: Steps whose input is never produced by an earlier step, outputs nothing ever uses, handoffs where it is unclear who acts next, and what happens when a step fails, is skipped or is run twice.

5. HIDDEN ASSUMPTIONS: Things the spec relies on but never states or checks: tools being installed, versions, how a third-party skill or tool behaves, file locations, the author being available, network access.

6. TRACEABILITY (only if a PRD or PRD review is attached): PRD requirements or answered questions the spec drops or changes without saying so, and spec features nothing in the PRD asked for.

7. RISK: Security, privacy and data-loss issues, and anything that could silently produce a wrong result that looks right.

Classify every finding as one of:
- DEFINITELY WRONG: the spec contradicts itself or cannot work as written.
- UNCLEAR: needs the author to confirm which reading is meant.
- ADDITION: the spec would need new scope to address it. For each addition, state its cost: roughly how much code, how much time per milestone, and what new moving parts it adds. Say what goes wrong if it is left out.

Output format:
- A ranked list of the top 5 issues by impact, each with: quoted line, the problem, why it matters, its classification, and the question you'd ask the author.
- Then the full findings grouped by pass.
- Then the clarifying questions, ordered by how much the answer would change what gets built.

Rules:
- Do not invent issues to fill a pass; write "none found" if so. A short review is a good result.
- No more than 3 ADDITION findings in total. If you have more, keep the 3 with the worst consequence of leaving them out and list the rest by title only.
- Do not rewrite the spec or suggest wording unless a line cannot work as written.
- Do not recommend extra review rounds, extra approval steps or extra checks on the process itself unless a specific finding requires one.
