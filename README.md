# Tortoise Lite

Tortoise Lite walks a software project through fixed stages, from reviewing the brief to final checks, using Claude Code skills that already exist (gstack, Superpowers, the built-in engineering skills and Codex). Along the way it keeps a decision log, tests the work at the end of every milestone, and builds one web page with the project's diagrams, decisions and progress for the author to review.

It has two parts:

- **The skill** (`skill/tortoise/SKILL.md`): instructions that tell Claude Code which skill to run at each stage, where its output goes, and when to stop for the author's approval.
- **The `tortoise` command** (`bin/tortoise`): a small Python tool that keeps the records, moves between stages, runs the milestone gate and builds the page.

The full design is in [docs/SPEC.md](docs/SPEC.md).

## Install

You need Python 3.10 or later and git. The tool uses only Python's standard library.

1. Clone this repository, for example to `~/tortoise-lite`.
2. Make the skill available to Claude Code by linking it into your skills folder:

   ```bash
   ln -s ~/tortoise-lite/skill/tortoise ~/.claude/skills/tortoise
   ```

3. Optionally put the command on your path: `ln -s ~/tortoise-lite/bin/tortoise ~/.local/bin/tortoise`.

The stages also call gstack, Superpowers, the `engineering` and `feature-dev` plugins, and the Codex command-line tool, so those need to be installed for a full run.

## Use

In a project folder that is a git repository, start Claude Code and say "use tortoise" (or run `/tortoise`). The skill asks for the project's name and test command, runs `tortoise init`, and starts the first stage.

## The stages

| Stage | What happens | You approve? |
|---|---|---|
| 0. PRD review | A skeptical review of the brief, with questions for you | No; you answer its questions |
| 1. Ideas | gstack `/office-hours` explores the problem | No |
| 2. Spec | Numbered requirements (R1, R2...), then one Codex review | Yes |
| 3. Architecture | The design, with diagrams on the project page | Yes |
| 4. Plan | Milestones of tasks, each task a checkbox naming its requirements | Yes |
| 5. Build | Each task built test-first, then ticked | No |
| 6. Milestone gate | Tests, requirement coverage, unticked tasks, an architecture check and two code reviews | Yes, per milestone |
| 7. Final checks | QA and security checks, a final checks record and the project README | Yes; the project is done |

Stages 5 and 6 repeat once per milestone.

## Commands

Run each from the project's root folder.

| Command | What it does |
|---|---|
| `tortoise init --name NAME --test-command CMD` | Starts a project: creates `tortoise.json` and `docs/DECISIONS.md`. Never overwrites a file. |
| `tortoise stage` | Shows the current stage and, during a milestone, how many of its tasks are ticked. |
| `tortoise stage next` | Moves to the next stage. Refuses while the current stage still needs your approval. |
| `tortoise approve` | Records your approval of the current stage, commits the approved work, tags the commit (such as `tortoise/milestone-1`) and lists the files committed. Refuses to commit new files that look like secrets, such as `.env`. |
| `tortoise approve --despite-failing-tests "REASON"` | Approves a milestone gate whose tests failed, recording your reason. |
| `tortoise decide --from FORM.json [--replaces D2]` | Proposes a decision. The form holds `question`, `options`, `research`, `choice`, `reason`, `proposed_by` and an optional `glossary`. |
| `tortoise decide --settle D3` | Settles a proposed decision. Only you settle decisions. |
| `tortoise gate` | Runs the milestone gate and writes `docs/gates/milestone-N.md`. |
| `tortoise page` | Builds `docs/project.html`. |

## What a project ends up with

All in the project's `docs/` folder: `PRD_REVIEW.md`, `DESIGN.md`, `SPEC.md`, `SPEC_REVIEW.md`, `ARCHITECTURE.md`, `PLAN.md`, `DECISIONS.md`, `gates/milestone-N.md`, `FINAL_CHECKS.md` and `project.html`, plus the project's own `README.md`. Every document stands on its own, is in plain English and ends with a glossary.

## Developing Tortoise Lite

```bash
python3 -m venv .venv && .venv/bin/pip install pytest
.venv/bin/pytest -q
```

## Glossary

- **Skill:** a packaged set of instructions Claude Code loads for a kind of task.
- **PRD (product requirements document):** the brief describing what to build and why.
- **Milestone:** a group of tasks that together give the author something to look at.
- **Gate:** the check at the end of a milestone that the author looks at before work continues.
- **Test-first (test-driven development):** write a test that fails because the feature is missing, then the code that makes it pass.
- **Mermaid:** a text format for diagrams that the project page turns into pictures.
- **Tag:** a named pointer git keeps to one commit, so it can be found again later.
