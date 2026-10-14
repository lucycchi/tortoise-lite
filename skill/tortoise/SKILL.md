---
name: tortoise
description: Run a project through Tortoise Lite's stages (PRD review, ideas, spec, architecture, plan, test-first build with a gate at each milestone, final checks), calling existing skills at each stage and keeping a decision log and a project page with diagrams. Use when the user says "tortoise", asks to start a project with the harness, or asks what stage a tortoise project is at.
---

# Tortoise Lite

You conduct a project through fixed stages. Each stage uses a skill that already exists; your job is to call it, put its output where Tortoise expects it, and keep the records. Do not reimplement what a stage's skill does.

## Setup

The `tortoise` tool and the review prompts live in the Tortoise Lite repository, two folders above this skill's base directory. Resolve it once:

```bash
TL=$(cd "$(readlink -f <this skill's base directory>)/../.." && pwd)   # then use "$TL/bin/tortoise" and "$TL/prompts/"
```

Run every `tortoise` command from the project's root folder. Start with `"$TL/bin/tortoise" stage`. If it says there is no `tortoise.json`, ask the author for the project's name and the command that runs its tests, then run `tortoise init --name "..." --test-command "..."`.

## Rules that apply at every stage

1. **Only the author approves and settles.** Never run `tortoise approve` or `tortoise decide --settle` unless the author has said so in their own words in this conversation, for this stage or decision. Approval of one stage never carries over to the next.
2. **Record material decisions** (choices that change what is built or how) with `tortoise decide --from <form.json>`. The form holds `question`, `options`, `research` (a list of `{link, summary}`), `choice`, `reason`, `proposed_by` (the exact model, such as "Claude (claude-opus-5-5)"), and `glossary` (terms a junior software engineer may not know, each with a plain-English meaning). Decisions start as proposed; tell the author which ones await them.
3. **Writing rules for every document you write:** it stands on its own (describe each named thing where it appears), it ends with a glossary for a junior software engineer, and it is plain English with no pseudocode. The plan is the one exception: it may include real code, at most about a tenth of its lines, and each code block is explained in plain English just before it.
4. **Scope rule.** When a review or your own judgement suggests something new, present it with its cost (lines of code, time per milestone, new moving parts) and let the author choose. Never apply "all recommendations" to additions. Each document gets one review unless the author asks for another.
5. **Ask in plain sentences**, one decision at a time, and say what you recommend.
6. **Keep going between stages.** After a stage's work is done and any approval is recorded, run `tortoise stage next`, say in one line where the project is, and start the next stage.

## Running Codex

Codex reviews run read-only on the project, with its input closed so it does not wait for typing:

```bash
codex exec -s read-only --ephemeral -o <output.md> "$(cat <prompt file>; echo; echo '<extra context>')" < /dev/null
```

Run it in the background and keep working; it can take several minutes.

## The stages

### 0. PRD review (skip if there is no PRD)

1. Save the PRD the author gives you as `docs/PRD.md`. Review it yourself using `$TL/prompts/prd-review.md` word for word, with the PRD attached below it.
2. Save the review as `docs/PRD_REVIEW.md`. Show the author the top five issues and the clarifying questions in plain sentences.
3. Ask the author the questions they can answer. Add an `## Answers` section with their answers, and a `## Questions for the PM` section with the rest. Answers that change what is built become decisions.

If there is no PRD, ask the author to describe the project in a few sentences and save that as `docs/PRD_REVIEW.md` under `## Author's description`.

### 1. Ideas

Invoke gstack `/office-hours`. Tell it, before it starts:

- use builder mode, and treat `docs/PRD_REVIEW.md` (with its answers) as a fully formed plan, so it skips its open questions and goes to premises and alternatives;
- write its in-project copy of the design document as `docs/DESIGN.md` (not `docs/designs/`);
- skip web research, the second opinion and visual mockups unless the author asks for them;
- put any bigger or "10x" ideas under Open Questions, not into the chosen approach.

Ask the author to confirm the premises and choose the approach, then record the approach and other material choices as decisions.

### 2. Spec

1. Invoke the Superpowers brainstorming skill with `docs/DESIGN.md`. Tell it, before it starts: the approach is already settled in `docs/DESIGN.md` and the decision log, so skip proposing approaches; save the spec to `docs/SPEC.md` (not `docs/superpowers/specs/`) and do not commit it (`tortoise approve` does); number every requirement as a list item `- R1: ...`, `- R2: ...` using whole numbers only, never `R2a`, because the coverage check ignores anything else (a new requirement gets the next free number); follow the writing rules above; and **do not invoke writing-plans when it finishes**, because Tortoise moves to architecture next.
2. Run Codex from the project folder with `$TL/prompts/spec-review.md` plus the line "The spec is docs/SPEC.md and the PRD review is docs/PRD_REVIEW.md; read both." Save the result as `docs/SPEC_REVIEW.md`. Reviews come back long: the plain-sentence sorting in the next step is essential.
3. Show the author each finding in plain sentences, sorted into: real problems to fix, wording to settle, and additions with their cost. Record each ruling under `## Rulings` in `docs/SPEC_REVIEW.md`, then apply the accepted ones to `docs/SPEC.md`.
4. Ask the author to approve the spec.

### 3. Architecture

1. For a new project, invoke `engineering:system-design`. Inside an existing codebase, invoke `feature-dev:code-architect`, and first draw how the code works today, then the planned changes. Tell either one: diagrams are Mermaid, never ASCII; follow the diagram rules below; skip sections that do not apply to this project (such as caching, queues or scaling for a small tool).
2. Write `docs/ARCHITECTURE.md`. It starts with `## Summary` (the problem, the approach, and where the project stands: the project page shows this first), then the diagrams as ```` ```mermaid ```` blocks, each placed next to the text it explains.
3. **Diagrams.** Always draw: system overview, main parts, database diagram, request flows for each important user action, user flow. A default that cannot apply (for example a user flow for a tool with no screens) gets one line saying why. Add these when their condition is true, and ask the author when unclear:
   - API map: the project offers an API that a separate front end, app or system calls.
   - Login and permissions flow: users sign in, or roles see or do different things.
   - State diagram: something has a status that changes over time.
   - Data flow: sensitive data (patient information, payments, passwords, keys), or data sent to an outside service including an AI model.
   - Background jobs and messages: queues, scheduled jobs, retries or webhooks.
   - Deployment: anything beyond one process on a laptop.
   - Code structure: more than about five modules, or the author asks where something lives.
   - Business process: a real-world workflow passes between people or roles.

   Note each added or skipped diagram in one line in `ARCHITECTURE.md`.
4. **Diagram rules.** Plain-English labels; every arrow says what moves along it; a sentence under each diagram says what it shows; numbered workflow steps with the same numbers in the text; about twelve boxes at most, split bigger subjects; one-way arrows with short labels, with what comes back described in the text or shown in a sequence diagram (two labelled arrows between the same boxes overlap and become unreadable); database diagrams describe each link in words ("each lab result belongs to exactly one patient") with one made-up example row per table.
5. Run `tortoise page`, check every diagram draws (a broken one shows a red error box), give the author the path to `docs/project.html`, and ask them to look at the diagrams and approve the architecture.

### 4. Plan

1. Invoke Superpowers `writing-plans`. Tell it, before it starts: save the plan to `docs/PLAN.md` (not `docs/superpowers/plans/`); group the tasks under headings `## Milestone 1: <name>`, `## Milestone 2: <name>`, each milestone a few tasks that together give the author something to look at; under each milestone heading, list its tasks as one checkbox line each, such as `- [ ] Task 3: chart the results. Requirements: R2`, and put each task's details (files, interfaces, test examples, steps) further down under its own `### Task 3: ...` heading, because the tool counts every checkbox directly under a milestone heading as a task; in the header, replace its line about subagent-driven development with "Built by Tortoise Lite inline, test-first"; keep its Global constraints and Review focus sections; write steps in plain English with exact test examples (inputs and expected outputs), using real code for at most about a tenth of the plan and explaining each code block just before it; and **when it finishes, do not offer an execution choice**, because Tortoise builds inline, test-first.
2. Ask the author to approve the plan. `tortoise stage next` then starts milestone 1.

### 5. Build (once per milestone)

Build the current milestone's tasks one at a time in this session, each with the Superpowers test-driven-development skill. Do not use subagent-driven development. As soon as a task's tests pass, tick its box in `docs/PLAN.md` (`- [x]`); never tick a task whose tests have not passed. `tortoise stage` shows how many are ticked. When the milestone's tasks are done, run `tortoise stage next` to reach its gate.

### 6. Milestone gate (once per milestone)

1. Run `tortoise gate`. It runs the tests, checks requirement coverage, lists the milestone's unticked tasks, writes `docs/gates/milestone-N.md` and prints the review base (the tag of the last approval). Finish or explain any unticked task before asking for approval.
2. **If tests failed**, for each failing test find the requirement it covers and decide which side is wrong:
   - The code is wrong: fix it with the test-driven-development skill.
   - The test does not match what the spec intends: do not edit it yet. Show the author the requirement, the test and why they disagree; change the test only once they agree, and note their choice under `## Author's choices` in the gate file.

   Then run `tortoise gate` again.
3. **Architecture check:** ask a fresh agent (the Agent tool) to compare the code with `docs/ARCHITECTURE.md` and either update the diagrams or list the gaps. Replace "Not recorded yet." under `## Architecture check` with the result.
4. **Reviews:** two independent reviews of the changes since the review base, both using `$TL/prompts/code-review.md` with the line `BASE is <review base>`: Codex (see Running Codex), and a fresh Claude agent (the Agent tool) told to work in the project folder, read that prompt file and follow it word for word. Run them in the background, at the same time as the architecture check. `tortoise gate` has already marked new files so `git diff <review base>` includes them. Tell both reviewers to ignore `docs/project.html`, which is rebuilt last. Summarise both under `## Reviews` as a table showing which reviewer found what.
5. Show the author the findings in plain sentences. Fix the ones they choose, test-first, and record their choices under `## Author's choices`. If any code changed, run `tortoise gate` again.
6. Run `tortoise page` and ask the author to look at the page and approve the milestone. `tortoise approve` refuses while tests fail; only if the author gives a reason for a failure outside this milestone, use `tortoise approve --despite-failing-tests "<their reason>"`. Show the author the "committed:" line it prints.

### 7. Final checks

1. Run gstack `/qa` if the project has a running app (a command-line tool is covered by its own command tests instead; say so in `FINAL_CHECKS.md`). Always run gstack `/cso`: it is driven by its own helper program with about a ten-minute budget for its static mode, and its runtime scanners need Docker; when they are unavailable, run the static mode and say so. Fix bugs test-first, then run the checks once more.
2. Write `docs/FINAL_CHECKS.md`: what each check found, what was fixed, and the author's choices about anything left, following the writing rules.
3. Write or update the project's `README.md`: what it does, how to install it, how to run it and its tests, and how to use it, for a junior software engineer.
4. Run `tortoise page`, then ask the author to approve final checks; that finishes the project.
