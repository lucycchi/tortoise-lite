I reviewed [SPEC.md](docs/SPEC.md) against the referenced [PRD-review prompt](prompts/prd-review.md). The prompt is not a PRD, so traceability does not apply.

## Top 5 issues

### 1. The stage model cannot represent multiple milestones

> “| 5. Build | For each task, write a failing test, make it pass, then tidy the code | … | No |”  
> “| 6. Milestone gate | … | Yes, before the next milestone |”  
> “| 7. Final checks | … | No |”  
> “`tortoise stage next` moves on…”

**Problem:** The only defined transition after stage 6 is stage 7. Nothing returns the project to Build for the next milestone, identifies the current milestone, or distinguishes three separate gate approvals.

**Why it matters:** The central promised workflow—build milestone, gate, approve, repeat—cannot be represented or enforced by the described commands.

**Classification:** DEFINITELY WRONG

**Question:** What is the exact state graph: does Build alternate with Gate once per `PLAN.md` milestone, and what keys each milestone and its approval?

### 2. Requirement coverage cannot be computed reliably

> “Turn the design note into numbered requirements…”  
> “each task names its requirements”  
> “Lists any requirement in `PLAN.md` that no task covers.”

**Problem:** No syntax or identifiers connect requirements in `SPEC.md` to tasks in `PLAN.md`. Reasonable implementations could parse numbers, Markdown headings, prose mentions, or an explicit field. They will disagree and can silently report false coverage.

**Why it matters:** This is the gate’s only requirements check. A reassuring but incorrect “all covered” result defeats its purpose.

**Classification:** UNCLEAR

**Question:** What exact, machine-readable requirement ID and task-reference format must the tool parse, and is the authoritative requirement list in `SPEC.md` or duplicated in `PLAN.md`?

### 3. Gate records and page refresh order are incomplete

> “At each milestone gate a fresh agent compares the code with this document and updates the diagrams, or lists the gaps for the author.”  
> “3. Rebuilds `project.html`.”  
> “Then the skill runs gstack `/review` … and asks Codex for one review…”

**Problem:** The defined gate rebuilds the page before the two code reviews, while the architecture-sync step is absent from the gate sequence. No durable location or schema is defined for test results, uncovered requirements, review findings, or architecture gaps.

**Why it matters:** A rebuilt page may contain stale diagrams and incomplete gate results. Later page rebuilds cannot preserve history unless implementers invent an undocumented storage format.

**Classification:** UNCLEAR

**Question:** Which gate artifacts belong on the page, where are they persisted, and in what order do architecture comparison, tests, reviews, page generation, and approval occur?

### 4. Existing projects are both supported and out of scope

> “`engineering:system-design`, or `feature-dev:code-architect` inside an existing codebase”  
> “Out of scope … adopting existing projects.”

**Problem:** The architecture-stage branch explicitly supports an existing codebase, while the scope section excludes that use case.

**Why it matters:** This changes initialization, diff baselines, preservation of existing documents, architecture discovery, and test-command setup.

**Classification:** DEFINITELY WRONG

**Question:** Is v1 greenfield-only, making the existing-codebase branch invalid, or must it safely initialize and operate in an existing repository?

### 5. Five mandatory diagrams do not apply to every supported project

> “Every project gets these five:”  
> “Database diagram: each table…”  
> “User flow: the screens a user moves through…”

**Problem:** CLI tools, libraries, batch jobs, and projects without persistent tables or screens cannot truthfully produce these diagrams as specified.

**Why it matters:** Agents must either fabricate architecture, create meaningless empty diagrams, or violate the requirement. All three make the page less trustworthy.

**Classification:** DEFINITELY WRONG

**Question:** Are only database-backed, screen-based applications supported, or can mandatory diagrams be marked not applicable?

# Full findings by pass

## 1. Contradictions

### C1. One review versus two reviews per milestone

> “At the end of each milestone a gate runs the project's tests and one review…”  
> “Then the skill runs gstack `/review` on the milestone's changes and asks Codex for one review of the same changes.”

The first line promises one review; the detailed flow specifies two independent reviews.

**Classification:** DEFINITELY WRONG

### C2. Existing-codebase support conflicts with the out-of-scope list

> “`feature-dev:code-architect` inside an existing codebase”  
> “Out of scope … adopting existing projects.”

These define opposite scope boundaries.

**Classification:** DEFINITELY WRONG

### C3. Mandatory diagrams assume databases and screens

> “Every project gets these five:”  
> “Database diagram: each table…”  
> “User flow: the screens a user moves through…”

“Every project” conflicts with the unrestricted project scope. Not every project has tables, user actions, requests, or screens.

**Classification:** DEFINITELY WRONG

### C4. An empty decision log violates the rule for every document

> “Each document ends with a glossary…”  
> “`tortoise init` | Creates `docs/`, an empty decision log…”

An empty `DECISIONS.md` cannot end with a glossary or stand on its own.

**Classification:** DEFINITELY WRONG

### C5. “Term list” may exclude the required glossaries

> “Each document ends with a glossary…”  
> “Out of scope … a term list…”

Two readings are possible: “term list” means a separate centralized artifact, or it includes any glossary. The latter directly conflicts with section 3. The author probably means a separate centralized term list, but the distinction is unstated.

**Classification:** UNCLEAR

## 2. Ambiguity

### A1. “Review” has at least three incompatible meanings

> “One review per document.”  
> “a fresh agent compares the code with this document and updates the diagrams”  
> “gstack `/review` … and … Codex for one review”

**Readings:**

1. Any evaluation of a document counts, making architecture comparisons at every gate violate the one-review limit.
2. Only the formal creation-stage review counts; maintenance comparisons and code reviews do not.

The author probably means the second.

**Classification:** UNCLEAR

### A2. Record locations and ownership are unspecified

> “All records live in the project's `docs/` folder.”  
> “The approval is a line in the journal section of `tortoise.json`.”  
> “Creates `docs/`, an empty decision log and `tortoise.json`…”

**Readings:**

1. `tortoise.json` is under `docs/` and is considered a record.
2. It is at the project root and “all records” excludes operational state.

The author probably means root-level `tortoise.json`, but that contradicts the ordinary meaning of “all records.”

**Classification:** UNCLEAR

### A3. The decision command has no usable interface contract

> “`tortoise decide` | Adds a decision log entry from a short form, or replaces an earlier one”

**Readings:**

1. An interactive questionnaire collects every required field.
2. Command-line flags or a supplied file contain the fields.

“Replaces” could mean editing the prior entry or appending a superseding entry. The author probably intends an interactive form and append-only supersession.

**Classification:** UNCLEAR

### A4. Test-command execution semantics are undefined

> “Runs the project's test command, which is named once in `tortoise.json`…”

**Readings:**

1. Execute one shell string, allowing pipes, redirection, and environment expansion.
2. Execute an argument array directly without a shell.

The author probably means a shell command from the project root. Working directory, environment, timeout, output capture, and signal handling remain undecided.

**Classification:** UNCLEAR

### A5. Spec-review findings have no disposition model

> “the author rules on each finding”

**Readings:**

1. Every finding gets an explicit accept/reject/defer entry.
2. The author edits the spec and a single approval implies all rulings.

The author probably means explicit rulings, because decisions that change the build are meant to enter `DECISIONS.md`.

**Classification:** UNCLEAR

### A6. Architecture divergence handling is discretionary

> “updates the diagrams, or lists the gaps for the author.”

**Readings:**

1. Update diagrams whenever code is authoritative.
2. Preserve approved architecture and report code divergence whenever architecture is authoritative.

Which artifact wins is a material design decision. No decision rule is given.

**Classification:** UNCLEAR

### A7. “Works on a phone” has no delivery meaning

> “It has light and dark themes and works on a phone.”

**Readings:**

1. The static file is manually copied to and opened on a phone.
2. A locally or remotely served page is reachable from a phone.

The author probably means responsive layout, but the spec defines neither a serving mechanism nor file transfer.

**Classification:** UNCLEAR

### A8. “Important user action” has no owner

> “Request flows: one for each important user action…”

**Readings:**

1. The architecture agent decides importance.
2. The author supplies or approves the list.

The author probably intends agent selection with author review.

**Classification:** UNCLEAR

## 3. Untestable requirements

### U1. The Python limit has no definite threshold

> “The `tortoise` tool stays under about 1,500 lines of Python, not counting tests.”

“About” has no pass/fail boundary. It also does not say whether comments, blank lines, generated files, vendored assets, or `SKILL.md` count.

**Classification:** UNCLEAR

### U2. Junior-readable prose has no evaluator

> “Every named thing is described where it appears…”  
> “Labels and arrows are plain English a junior engineer can follow.”

No target experience level, example boundary, or designated human judge is provided.

**Classification:** UNCLEAR

### U3. Mobile and one-screen behavior lack observable thresholds

> “a one-screen summary”  
> “works on a phone”

No viewport size, allowed scrolling, browser set, orientation, or overflow behavior is stated.

**Classification:** UNCLEAR

### U4. The fuzzy diagram and planning limits are not enforceable

> “No diagram has more than about twelve boxes…”  
> “The code has more than about five modules…”  
> “milestones of a few tasks each”

No threshold says whether 13 boxes, 6 modules, or 8 tasks crosses the boundary.

**Classification:** UNCLEAR

### U5. Architecture comparison has no success condition

> “a fresh agent compares the code with this document and updates the diagrams, or lists the gaps…”

The spec does not define what counts as a material mismatch, how a human confirms completeness, or what observable result proves comparison occurred.

**Classification:** UNCLEAR

### U6. Final security and QA checks have no completion criterion

> “Test the running product and check security”

There is no defined supported surface, severity threshold, required output, or condition for declaring the project finished.

**Classification:** UNCLEAR

## 4. Gaps in the flow

### G1. There is no Build–Gate loop

> “| 5. Build…”  
> “| 6. Milestone gate…”  
> “| 7. Final checks…”  
> “`tortoise stage next` moves on…”

After the first gate, the defined linear transition reaches final checks rather than the next milestone.

**Classification:** DEFINITELY WRONG

### G2. Skipping the PRD stage removes the Ideas stage’s only named input

> “starting from the PRD review's answered questions”  
> “A project with no PRD skips this stage.”

No alternate starting input is defined for a project without a PRD.

**Classification:** DEFINITELY WRONG

### G3. The project page has no defined source for its summary

> “Ideas … produces … A design note and the first decisions”  
> “a one-screen summary: the problem, the approach, the key decisions and the current stage”

The design note has no filename or structure. Nothing says where `tortoise page` obtains “problem” and “approach.”

**Classification:** UNCLEAR

### G4. Historical gate results have no defined persistence location

> “records pass or fail”  
> “the milestone gates and their results”  
> “The approval is a line in the journal section of `tortoise.json`.”

Only approvals are explicitly placed in the journal. There is no defined record for test results, uncovered requirements, review findings, timestamps, or milestone identity.

**Classification:** UNCLEAR

### G5. Requirement coverage lacks a data contract

> “numbered requirements”  
> “each task names its requirements”  
> “Lists any requirement in `PLAN.md` that no task covers.”

No requirement-ID syntax or parsing rule connects these artifacts.

**Classification:** UNCLEAR

### G6. “Milestone changes” have no boundary

> “runs gstack `/review` on the milestone's changes and asks Codex for one review of the same changes.”

Nothing records a starting commit, ending commit, patch, file list, or snapshot. Without that, the two reviewers cannot reliably receive the same change set.

**Classification:** DEFINITELY WRONG

### G7. Architecture synchronization is missing from the gate sequence

> “At each milestone gate a fresh agent compares the code with this document…”  
> “`tortoise gate` runs at the end of each milestone:”  
> “Then the skill runs gstack `/review`…”

Section 6 never invokes the fresh architecture agent or says whether it runs before or after page generation and code review.

**Classification:** DEFINITELY WRONG

### G8. Failure and repeat behavior is absent

> “`tortoise gate` runs at the end of each milestone”  
> “`tortoise approve` | Records the author's approval of the current stage”

The flow does not say what happens if tests fail, a reviewer fails to run, Mermaid fails, the process is interrupted, approval is repeated, or the gate is rerun after fixes. It is unclear whether results append, replace, or duplicate.

**Classification:** UNCLEAR

### G9. Final-check bugs have no consumer

> “| 7. Final checks | … | Bugs to fix | No |”

There is no repair step, repeat of final checks, final gate, or completion state. The workflow can end while still holding unresolved bugs.

**Classification:** DEFINITELY WRONG

### G10. Review outputs are not named records

> “Findings go to the author, who decides which to fix.”

No artifact stores either milestone review, the dispositions, or the resulting work. The next actor and re-entry point after “fix” are also undefined.

**Classification:** UNCLEAR

## 5. Hidden assumptions

### H1. All named skills exist with compatible behavior

> “each stage uses a skill that already exists”  
> “`engineering:system-design`, or `feature-dev:code-architect`”  
> “Superpowers `writing-plans`”

The spec assumes installation, exact names, compatible versions, stable output formats, and that each skill follows Tortoise’s document rules. No versions or installation/preflight behavior are specified.

**Classification:** UNCLEAR

### H2. Claude Code can invoke Codex as required

> “asks Codex for one review of the same changes.”

This assumes a callable Codex installation, authentication, network access, model availability, and a way to supply the exact patch. None is checked.

**Classification:** UNCLEAR

### H3. Git or an equivalent history system exists

> “the milestone's changes”

Computing a milestone-specific diff assumes version control and usable boundaries, although Git is never required and milestone commits are never produced.

**Classification:** UNCLEAR

### H4. Mermaid is available in the browser

> “Diagrams are drawn in the browser by the Mermaid library.”

The spec does not say whether Mermaid is vendored, loaded from a CDN, or already installed. Those choices change offline behavior, privacy, version stability, and whether the page works on a phone.

**Classification:** UNCLEAR

### H5. Runtime versions and platforms are compatible

> “Plain Python 3, standard library only, with pytest for its own tests.”

No minimum Python or pytest version, supported operating system, executable installation method, or command-shell behavior is defined.

**Classification:** UNCLEAR

### H6. Third-party skills produce the required standalone documents

> “Each document stands on its own.”  
> “Each document ends with a glossary…”

The spec assumes office-hours, brainstorming, writing-plans, QA, CSO, and both architecture skills will honor these rules despite their own output contracts.

**Classification:** UNCLEAR

### H7. The author is always available synchronously

> “The author opens the page … and approves the next milestone.”  
> “in one Claude Code session”

The build assumes the author can answer architecture questions and gate decisions without the session ending or state needing restoration.

**Classification:** UNCLEAR

## 6. Traceability

None found. No PRD or `PRD_REVIEW.md` was attached. `prompts/prd-review.md` is a review instruction template, not product requirements.

## 7. Risk

### R1. Generated HTML may execute content from project records

> “One web page built from the records by `tortoise page`…”  
> “Diagrams are drawn in the browser by the Mermaid library.”  
> “Out of scope … sandboxed rendering…”

If Markdown, decision text, diagram source, or review output is inserted without correct contextual escaping, opening `project.html` can execute script or load external resources. Mermaid configuration also affects links and embedded HTML.

**Classification:** ADDITION

**Cost:** Roughly 75–150 lines plus tests; negligible time per milestone; adds contextual HTML escaping, a restrictive content policy/Mermaid configuration, and an explicit local-versus-CDN asset rule. Without it, a project record can turn a local report into code execution or data exfiltration. This does not require full sandboxed rendering.

### R2. The configured test command is an unstated code-execution boundary

> “Runs the project's test command, which is named once in `tortoise.json`…”

If repositories or configuration files are not fully trusted, this executes arbitrary code. Even in trusted projects, shell versus direct-process execution changes quoting and injection behavior.

**Classification:** UNCLEAR

### R3. Initialization can overwrite existing records

> “`tortoise init` | Creates `docs/`, an empty decision log and `tortoise.json`…”

The behavior when any target already exists is missing. Overwriting can destroy decisions or configuration; merging can create invalid mixed state.

**Classification:** UNCLEAR

### R4. Sole-copy records have no crash-safe write behavior

> “One file; new entries are added to the end.”  
> “`tortoise decide` | Adds a decision log entry … or replaces an earlier one”

A crash during an in-place replacement can corrupt the only decision log or JSON state.

**Classification:** ADDITION

**Cost:** Roughly 50–100 lines plus tests; negligible time per milestone; adds temporary-file writes, atomic replacement, and a defined refusal or backup policy. Without it, interruption during a write can lose the workflow state or decision history.

### R5. Model-made decisions have no authority boundary

> “who decided (the author, or the exact model)”

The spec permits a model to be recorded as the decider but does not say which kinds of material decisions a model may settle. Two implementations could either allow security/product scope choices autonomously or require author decisions.

**Classification:** UNCLEAR

# Clarifying questions

1. What exact state graph represents repeated Build–Gate cycles, current milestone identity, and per-milestone approval?
2. Is v1 strictly greenfield-only, or must it operate safely inside existing repositories?
3. What exact requirement-ID syntax links `SPEC.md`, `PLAN.md`, tasks, and the coverage check?
4. What defines “the milestone’s changes,” and how are both reviewers guaranteed the same change set?
5. Where are gate results, review findings, architecture gaps, dispositions, and approvals persisted?
6. What is the exact gate order, including architecture comparison, tests, both reviews, fixes, page generation, and approval?
7. Does a milestone have one reviewer or both gstack and Codex?
8. What starts the Ideas stage when there is no PRD?
9. What happens after final checks find a bug or security issue, and what state means the workflow is complete?
10. Which project types are supported, and how should database, request, and user-flow diagrams behave when not applicable?
11. Where exactly do `tortoise.json`, `project.html`, the design note, gate history, and review outputs live?
12. What are the overwrite, rerun, interruption, and duplicate-approval semantics for every mutating command?
13. Is the configured test command a shell string or argument list, and what are its working directory, timeout, environment, and output rules?
14. Which versions and installation sources of gstack, Superpowers, architecture skills, Codex, Python, pytest, and Mermaid are supported?
15. Does “works on a phone” mean responsive rendering only, or must Tortoise provide a way for the phone to access the page?