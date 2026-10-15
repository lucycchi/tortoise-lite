# Tortoise Lite: Design

- **Date:** 2026-10-13
- **Author:** Lucy Chi, written with Claude Code (Claude Opus 5.5)
- **Status:** approved by the author on 2026-10-14
- **Replaces:** the tortoise harness version 2 (`~/tortoise-harness`), kept untouched as an archive.

## 1. What this is

Tortoise Lite is a Claude Code skill plus a small command-line tool. It does three things:

1. **Connects existing skills in order.** It runs a project through stages (PRD review, ideas, spec, architecture, plan, build, final checks), and each stage uses a skill that already exists: gstack, Superpowers, the built-in engineering skills and Codex.
2. **Tests between milestones.** The plan groups tasks into milestones. At the end of each milestone a gate runs the project's tests and two code reviews, and the author looks at the result before the next milestone starts.
3. **Draws diagrams for the author to review.** The architecture is kept as plain English with Mermaid diagrams. One web page, `project.html`, shows the diagrams, the decisions and the milestone results, and is rebuilt at every gate.

## 2. Scope rule

The previous version grew from 5,090 to 24,895 words by accepting every review recommendation, and spent most of its build time on per-task verifiers and retries.

1. **Size limits.** This design stays under 2,700 words (raised from 2,500 on 2026-10-15 for the progress board). The `tortoise` tool stays under about 1,500 lines of Python, not counting tests.
2. **Additions need a stated cost.** Any new feature, rule or check, whether suggested by a review, by Claude or by Codex, is proposed with what it adds: lines of code, time per milestone and new moving parts. The author approves it explicitly. "Do all the recommendations" is not applied to scope additions without that list.
3. **One review per document.** The spec, the architecture and the plan each get at most one review unless the author asks for another.

## 3. Writing rules for every document

1. **Each document stands on its own.** Every named thing is described where it appears, for example "the lab results table, which stores one row for each test result".
2. **Each document ends with a glossary** of terms a junior software engineer might not know.
3. **Plain English, no pseudocode.** Real names of files, functions and tables may appear, each explained in a sentence. A plan may include real code, at most about a tenth of its lines, each block explained in plain English.
4. **No bare codes.** A requirement, task, decision, milestone or finding is named by what it is, with its code in parentheses after it: "the export button that saves a PDF (R3)", never "R3" alone. This holds in documents, diagram labels, review findings, messages to the author and the tool's own output.

## 4. The stages

| Stage | What happens | Skill used | What it produces | Author approval |
|---|---|---|---|---|
| 0. PRD review | Read the PRD (product requirements document: the brief describing what to build) as a skeptical senior engineer, using the prompt in section 4.1 | Claude, with the review prompt | `PRD_REVIEW.md` | No; the author answers its questions |
| 1. Ideas | Explore the problem, who it is for, and what success means, starting from the PRD review's answered questions, or from the author's description when there is no PRD | gstack `/office-hours` | A design note and the first decisions | No |
| 2. Spec | Turn the design note into requirements numbered R1, R2 and so on, then run one review using `prompts/spec-review.md`; the author rules on each finding | Superpowers brainstorming, then Codex with the review prompt | `SPEC.md` and `SPEC_REVIEW.md` | Yes |
| 3. Architecture | Design the system and draw its diagrams; in an existing codebase, first draw how it works today; then one Codex review with `prompts/architecture-review.md`, and the author rules on each finding | `engineering:system-design`, or `feature-dev:code-architect` inside an existing codebase | `ARCHITECTURE.md` with diagrams, `ARCHITECTURE_REVIEW.md` | Yes |
| 4. Plan | Break the work into numbered milestones of a few tasks each; each task is a checkbox line such as "- [ ] Task 3: chart the results. Requirements: R2" | Superpowers `writing-plans` | `PLAN.md` | Yes |
| 5. Build | For each task, write a failing test, make it pass, then tidy the code; then tick the task's box in `PLAN.md` | Superpowers test-driven development | Code and tests | No |
| 6. Milestone gate | See section 6 | `tortoise gate`, Codex and a fresh Claude reviewer | Gate result on the page | Yes, before the next milestone |
| 7. Final checks | Test the running product and check security; bugs are fixed test-first and the checks run once more; write or update the project's README (how to install, run and use it) | gstack `/qa` and `/cso` | Bug fixes, `FINAL_CHECKS.md` (results, fixes and the author's choices) and `README.md` | Yes; the project is done |

Stages 5 and 6 repeat once per milestone in `PLAN.md`. Final checks start after the last milestone's gate is approved.

The skill overrides one Superpowers default: after the spec is approved it goes to the architecture stage, not straight to the plan.

### 4.1 The PRD review

Review prompts live in the Tortoise Lite repository's `prompts/` folder. The PRD review prompt is kept word for word in `prompts/prd-review.md`, and the PRD is attached below it.

The output is a ranked top five, the full findings, and clarifying questions ordered by how much each answer would change the design. The author answers the questions they can; the answers go into `PRD_REVIEW.md` and become the starting point for the ideas stage. Questions only the PM can answer are listed for the author to send. Answers that change what is built become decision log entries.

A project with no PRD skips this stage.

## 5. The records

All records live in the project's `docs/` folder.

### 5.1 The decision log (`DECISIONS.md`)

One file; new entries are added to the end. Only material decisions are logged: choices that change what is built or how. Each entry has:

- a number and a plain-English question;
- the options considered;
- the research, as links with a one-sentence summary each;
- the choice and the reason;
- terms a junior software engineer may not know, with their meanings, which the tool adds to the log's glossary;
- who proposed it (the author, or the exact model) and the date;
- its status: proposed, settled, or replaced by a later entry. Only the author settles a decision; a model can only propose one.

### 5.2 The architecture document (`ARCHITECTURE.md`)

The system in plain English, with each Mermaid diagram placed next to the text it explains. At each milestone gate it is compared with the code (section 6).

### 5.3 The project page (`project.html`)

One web page built from the records by `tortoise page`, never edited by hand. It contains, in order:

1. a one-screen summary: the problem, the approach, the key decisions and the current stage;
2. progress: each milestone's tasks with their checkboxes and a count such as "3 of 5 done";
3. the requirements from `SPEC.md`;
4. the architecture with its diagrams;
5. the decisions;
6. the milestone gates and their results;
7. the final checks.

It has light and dark themes and works on a phone. Diagrams are drawn in the browser by the Mermaid library. A diagram that fails to draw shows an error box in its place, never a blank. Record text is escaped when the page is built and Mermaid runs in its strict mode, so nothing in a record can run as script.

Every record with a diagram also gets its own page beside it, such as `ARCHITECTURE.html`, rebuilt with the project page. `tortoise html FILE.md` does the same for any Markdown file, in a Tortoise project or not.

### 5.4 Diagram rules

1. Labels and arrows are plain English a junior engineer can follow. Every arrow says what moves along it.
2. A sentence under each diagram says what it shows.
3. Workflow steps are numbered, and the text uses the same numbers.
4. No diagram has more than about twelve boxes; bigger subjects are split.
5. Database diagrams give each field the database's own type name with its meaning in plain words beside it, such as `INTEGER id "whole number, given automatically"`, and describe each link between tables in words, such as "each lab result belongs to exactly one patient".

### 5.5 Which diagrams to draw

Every project gets these five; one that cannot apply, such as a user flow for a tool with no screens, gets one line saying why instead:

1. **System overview:** the system as one box, the people who use it, and the outside services it talks to.
2. **Main parts:** the main pieces, such as the web page, API server, database and background worker, and what passes between them.
3. **Database diagram:** each table, its fields in plain words, how tables link, and one made-up example row per table.
4. **Request flows:** one for each important user action, step by step, including what happens on an error or timeout.
5. **User flow:** the screens a user moves through and the choices that lead between them.

The architecture stage adds any of these when its condition is true:

| Diagram | Draw it when |
|---|---|
| 6. API map: endpoints grouped by resource, with which need a login and what each returns | The project offers an API that a separate front end, app or another system calls |
| 7. Login and permissions flow | Users sign in, or different roles can see or do different things |
| 8. State diagram | Something has a status that changes over time, such as an order, an appointment or a review |
| 9. Data flow | The project handles sensitive data (patient information, payments, passwords, keys) or sends data to an outside service, including an AI model |
| 10. Background jobs and messages | Work happens outside a user's request: queues, scheduled jobs, retries or webhooks |
| 11. Deployment | The project runs anywhere other than one process on a laptop, such as Docker, a server or cloud services |
| 12. Code structure | The code has more than about five modules, or the author asks where something lives |
| 13. Business process | A real-world workflow passes between people or roles, such as front desk, then clinician, then billing |

When a condition is unclear, the architecture stage asks the author. Each choice to add or skip one is a line in `ARCHITECTURE.md`, not a decision log entry.

## 6. The milestone gate

At the end of each milestone, in this order:

1. `tortoise gate` runs the project's test command, which is named once in `tortoise.json`, lists any requirement in `SPEC.md` that no task in `PLAN.md` names, and lists the milestone's tasks that are not ticked.
2. Codex and a fresh Claude agent each compare the code with `ARCHITECTURE.md`, using `prompts/architecture-check.md`, and list where the two disagree; the author decides which side changes.
3. The skill asks Codex and a fresh Claude agent for one code review each, both with `prompts/code-review.md`; Claude writes the code, so Codex's checks are always from another company. (gstack `/review` needs a feature branch and remote, which Tortoise does not use.) Both review the same changes: everything since the commit recorded at the previous gate.
4. The results, review findings and the author's choice of which findings to fix go in `docs/gates/milestone-N.md`, where N is the milestone number.
5. `tortoise page` rebuilds `project.html`.
6. The author looks at the page and approves with `tortoise approve`. Failing tests block the approval: the skill checks each failing test against its requirement, fixes the code, or changes the test only with the author's agreement, then re-runs the gate. `--despite-failing-tests "reason"` approves anyway and records the reason. The approval commits the work, tags the commit (such as `tortoise/milestone-1`) and records the approval and its tag in `tortoise.json`.

## 7. The `tortoise` tool

Plain Python 3, standard library only, with pytest for its own tests.

| Command | What it does |
|---|---|
| `tortoise init` | Works in a new or existing repository and never overwrites a file. Creates `docs/`, an empty decision log and `tortoise.json`, which holds the project name, the current stage, the test command and the approvals |
| `tortoise stage` | Shows the current stage and, during a milestone, how many of its tasks are ticked; `tortoise stage next` moves on, refusing when the stage needs an approval that is not recorded, or when the plan has no milestones |
| `tortoise approve` | Records the author's approval of the current stage |
| `tortoise decide` | Adds a decision log entry from a short form, or replaces an earlier one |
| `tortoise gate` | Runs the milestone gate (section 6) |
| `tortoise page` | Builds `project.html` |
| `tortoise html` | Writes any Markdown file as a page beside it, with its diagrams drawn |
| `tortoise board` | Copies the plan's tasks onto the project's progress board (section 7.1) |

The skill, `SKILL.md`, tells Claude Code which skill to run at each stage and when to call the tool.

### 7.1 The progress board (optional)

If the author wants one when the plan is approved, `tortoise board` creates a GitHub Project linked to the project's repository, then the author adds a board view by hand (GitHub cannot create views for a tool). Each task becomes an issue titled by what it is, such as "Chart the results (Task 3)", under a GitHub milestone named after its plan milestone; `tortoise.json` records the board and which issue is which task. Card statuses:

- **To do:** in a later milestone.
- **In progress:** in the current milestone, not ticked.
- **Awaiting gate:** ticked; the gate is not approved.
- **Done:** the gate is approved; the issue is closed.

`PLAN.md` stays the only source of truth: moving a card changes nothing. The skill runs `tortoise board` after each ticked task and approval, using the `gh` tool; if GitHub is unreachable it warns and never blocks a stage.

## 8. How it is built

Test-first with the Superpowers test-driven-development skill, in one Claude Code session, without per-task subagents. Three milestones, each ending with the author reviewing the page:

1. **Records and page:** `init`, `decide`, `page` and the page layout.
2. **Stages and gate:** `stage`, `approve`, `gate`.
3. **The skill:** `SKILL.md`, then one run of a small sample project through every stage.

## 9. Out of scope

Hidden and locked tests, mutation testing, judges, per-task verifiers, cross-company roles per task, secret scanning, a term list, cost tracking, sandboxed rendering, and copying board changes back into the plan.

## Glossary

- **Skill:** a packaged set of instructions Claude Code loads for a kind of task, such as Superpowers brainstorming.
- **gstack:** a collection of Claude Code skills for ideation, reviews and quality checks.
- **Superpowers:** a collection of Claude Code skills for brainstorming, planning and test-driven development.
- **Codex:** OpenAI's coding agent, used here as an independent second reviewer.
- **Mermaid:** a text format for diagrams that a browser library turns into pictures.
- **Milestone:** a group of tasks that together deliver something the author can look at.
- **Test-first (test-driven development):** write a test that fails because the feature is missing, then write the code that makes it pass.
- **Gate:** a check at the end of a milestone that must be looked at before work continues.
- **PRD (product requirements document):** the brief, usually from a product manager (PM), describing what to build and why.
- **Pytest:** the standard Python tool for running tests.
- **GitHub Project:** a GitHub planning board whose cards are issues; a board view shows them in status columns.
- **Issue:** a GitHub record of one piece of work, which can be linked to commits and closed when done.
