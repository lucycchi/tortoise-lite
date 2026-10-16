You are reviewing the PRD below as a skeptical senior engineer who will have to build and support this. Your job is to find what will bite the team, not to summarize or praise. Assume the document contains mistakes, gaps, and possibly deliberate traps.

Work through these passes, quoting the exact PRD line for every finding:

1. CONTRADICTIONS: Requirements that conflict with each other, or with stated goals, constraints, or non-goals. Include numeric conflicts (e.g., latency vs. data volume vs. budget).

2. AMBIGUITY: Terms that two reasonable engineers would build differently ("real-time," "secure," "users," "support," "fast," "should"). Also check the small words: "or" (either one, or both?), "and," "minimum," "e.g." (a list of permissions, or a checklist?), "preferred," "encouraged," "required." Also check nouns that imply something visible must exist ("selection" implies a control to select with; "display" implies a screen). For each, give the two most likely interpretations and which one the author probably means.

3. HIDDEN ASSUMPTIONS: Things the PRD treats as given but never states or verifies: data availability and quality, existing infrastructure, third-party behavior, user behavior, team capacity, legal/compliance status. Include parts described as independent that would in practice share a vendor, service or point of failure.

4. MISSING REQUIREMENTS: What a production system needs that isn't mentioned: error and failure states, empty/edge cases, scale limits, auth and permissions, data retention/deletion, migration of existing data, observability, rollback, accessibility, i18n, abuse/misuse.

5. SCOPE TRAPS: Features that sound small but are large (e.g., "just add search," "sync across devices," "undo"). Estimate the real size.

6. SUCCESS METRICS: Are they measurable, attributable to this work, and achievable? Could the team hit the metric while failing the user, or vice versa? For every numeric target, name the exact event that starts the clock or count and the event that stops it. Then test that definition against each plausible way of building the system (streaming, buffering, batching, caching, preloading, warm vs. cold start). Say whether it could come out zero, negative or meaningless, or be inflated by something it is not meant to measure (playback time, queueing, setup). If options are compared, check that the same definition measures the same thing in each.

7. RISK AND COMPLIANCE: Security, privacy, regulatory (HIPAA, GDPR, etc.), and safety issues, especially ones the PRD doesn't acknowledge.

8. DELIBERATE TRAPS (if this is an evaluation or take-home): Details planted to test whether the reader notices: buried constraints, footnotes that change the meaning of a requirement, a requirement that is impossible or unwise as written, red-herring features, implied deadlines. Read every sentence and ask: what would a builder in a hurry do here, and what would it cost them when the work is judged?

9. COMPARISONS AND EVIDENCE (if the PRD asks to compare, benchmark, evaluate or recommend): List every variable that differs between the options besides the one under study (vendors, models, defaults, modes of operation such as streaming vs. turn-taking). Ask whether the likely test data would flatter one option (synthetic, scripted, clean, short, or unlike real use). Check whether the PRD's framing assumes the conclusion it asks for, and whether it presents the options as the only ones when others exist.

10. LITERAL REQUIREMENTS: Extract every item the PRD requires or names exactly: named products, models and versions, file names, counts, length limits, required tools, deliverables. A reviewer will check these literally. Flag any that are unwise as written, and for each say whether it can still be met word for word alongside a better alternative.

11. WHO RUNS AND JUDGES IT: Who receives the result and how will they check it? What accounts, keys, paid services, installs or data would they need to run it themselves? What is actually submitted (code, live URL, document)? What will they look at first?

12. SECOND-ORDER EFFECTS: Take your top issues. Assume the obvious fix for each is adopted. What does that fix break or create? Examples: replacing a named component turns the required one into an optional extra; a design choice that removes a delay makes a metric trivially small; a cut-order rule that protects one item drops a required one.

Output format:
- A ranked list of the top 5 issues by impact, each with: quoted line, the problem, why it matters, and the question you'd ask the author.
- Then the full findings grouped by pass.
- Then the literal requirements as a table: requirement (quoted), unwise as written (yes/no and why), can be met word for word (yes/no).
- Then a list of clarifying questions to send the PM, ordered by how much the answer would change the design.

Rules: Do not invent issues to fill a category; write "none found" if so. Distinguish clearly between "definitely wrong" and "unclear, needs confirmation." Don't suggest solutions unless the PRD's approach is unworkable; second-order effects are the exception, since they examine the obvious fixes. Name every requirement or finding by what it is, with any code in parentheses after it, never by a bare code; give each of your findings a short title and put any number you assign after the title.
