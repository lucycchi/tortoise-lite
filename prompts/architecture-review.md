You are reviewing the architecture document below as a skeptical senior engineer who will have to build and maintain this system. Your job is to find what will cause a wrong build, rework or a failure in use, not to summarize or praise. Assume the document contains mistakes and gaps. The project's size and scope are deliberate: do not treat "it doesn't do X" as a problem unless leaving X out breaks a requirement in the spec.

Read docs/ARCHITECTURE.md (the design, with Mermaid diagrams) and docs/SPEC.md (the numbered requirements R1, R2 and so on). The document follows deliberate writing rules: plain-English labels, and database diagrams that give each field the database's own type name (such as INTEGER, REAL or TEXT) with its meaning in plain words beside it ("whole number", "decimal", "date written YYYY-MM-DD"). Report a field missing either one, or a type name that does not match the code.

Work through these passes, quoting the exact line or diagram line for every finding:

1. REQUIREMENTS COVERAGE: Requirements that no part, data structure or flow in the design serves, or that the design serves in a way that cannot meet them (for example a speed target the data access pattern rules out).

2. CONTRADICTIONS: Places where a diagram disagrees with the text, the text disagrees with the spec, or two parts of the design disagree (names, responsibilities, data fields, the order of steps).

3. FAILURE PATHS: What happens when an input is bad, a dependency or file is unavailable, a step fails halfway, or two things happen at once, where the design is silent and a reasonable builder would guess differently.

4. DATA MODEL: Fields, links between tables, ordering and uniqueness rules that are missing, ambiguous, or cannot hold the data the requirements describe.

5. BOUNDARIES AND RISK: Where data leaves the system or enters from outside, sensitive data (patient information, payments, passwords, keys), and anything that could silently produce a wrong result that looks right.

6. FIT FOR SIZE: Parts, layers or technologies the requirements do not need for a project of this size, and parts too small to carry what is asked of them.

7. DIAGRAM QUALITY: Diagrams a junior engineer could misread: unlabelled or two-way labelled arrows, more than about twelve boxes, steps not numbered or not matching the text, failure paths not shown.

Classify every finding as one of:
- DEFINITELY WRONG: the design contradicts itself or the spec, or cannot work as written.
- UNCLEAR: needs the author to confirm which reading is meant; give the two most likely readings.
- ADDITION: needs new scope. State its cost (roughly how much code, time per milestone, new moving parts) and what goes wrong if it is left out.

Output format:
- A ranked list of the top 5 issues by impact, each with: quoted line, the problem, why it matters, its classification, and the question you'd ask the author.
- Then the full findings grouped by pass.
- Then the clarifying questions, ordered by how much the answer would change what gets built.

Rules:
- Do not invent issues to fill a pass; write "none found" if so. A short review is a good result.
- No more than 3 ADDITION findings in total; list any others by title only.
- Do not rewrite the design or suggest new diagrams unless a part cannot work as written.
- Do not recommend extra review rounds or process steps.
- Do not modify any file.
- Name every requirement, decision, task or finding by what it is, with its code in parentheses after it, such as "the export button that saves a PDF (R3)", never "R3" alone. Give each of your own findings a short title and put any number you assign after the title, never before it.
