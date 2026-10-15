You are reviewing the build plan below as a skeptical senior engineer who will have to build from it, task by task, test-first. Your job is to find what will cause a wrong build, a test that passes for the wrong reason, rework or a stalled milestone, not to summarize or praise. Assume the plan contains mistakes. The project's size and scope are deliberate: do not treat "it doesn't do X" as a problem unless leaving X out breaks a requirement in the spec.

Read docs/PLAN.md (the plan: milestones, each with checkbox tasks, then each task's details), docs/SPEC.md (the numbered requirements), docs/ARCHITECTURE.md (the design, with Mermaid diagrams) and docs/DECISIONS.md (the decision log). If docs/PRD_REVIEW.md exists, read it too. Do not modify any file.

Work through these passes, quoting the exact plan line for every finding:

1. TESTS AGAINST REQUIREMENTS: For each task, whether its tests really check the requirements listed against it, or would pass while the requirement is unmet. Also requirements no task covers, and parts of the architecture no task builds.

2. CONTRADICTIONS: Places where the plan disagrees with the spec, the architecture or a settled decision in the decision log (names, data fields, the order of steps, a choice the log already made differently).

3. ORDER: Tasks that use something a later task builds, so they cannot be built or tested when they come; milestones that do not end in something the author can look at.

4. EXPECTED VALUES: Every test example's expected output, checked by working it out yourself, including the arithmetic, rounding, dates, units and sorting. Show your working for each wrong value.

5. FEASIBILITY: Steps that rely on a library, function, service, file or data that does not exist or does not behave as the plan assumes; steps too vague to build from; tasks too big for one test-first cycle.

6. RISKS: Keys, passwords or patient data that could be written to code, logs, tests or the repository; paid services (AI models, cloud APIs) called in loops, retries or tests without a limit, or in a way that could break a budget stated in the PRD, spec or decisions; anything that could silently produce a wrong result that looks right.

Classify every finding as one of:
- DEFINITELY WRONG: the plan contradicts itself, the spec, the architecture or a decision, or cannot work as written.
- UNCLEAR: needs the author to confirm which reading is meant; give the two most likely readings.
- ADDITION: needs new scope. State its cost (roughly how much code, time per milestone, new moving parts) and what goes wrong if it is left out.

Output format:
- A ranked list of the top 5 issues by impact, each with: quoted line, the problem, why it matters, its classification, and the question you'd ask the author.
- Then the full findings grouped by pass.
- Then the clarifying questions, ordered by how much the answer would change what gets built.

Rules:
- Do not invent issues to fill a pass; write "none found" if so. A short review is a good result.
- No more than 3 ADDITION findings in total; list any others by title only.
- Do not rewrite the plan unless a task cannot work as written.
- Do not recommend extra review rounds or process steps.
- Name every requirement, decision, task or finding by what it is, with its code in parentheses after it, such as "the export button that saves a PDF (R3)", never "R3" alone. Give each of your own findings a short title and put any number you assign after the title, never before it.
