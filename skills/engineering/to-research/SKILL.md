---
name: to-research
description: Pressure-test the ideas and assumptions in a PRD or its implementation issues against external best practices, using a team of parallel web-research agents, then synthesize the findings and align with the user one question at a time before updating the PRD (and optionally its issues). Use after to-prd or to-issues when the user wants to validate or invalidate the assumptions, technology choices, or approach in a PRD/issue set against real-world research before implementation, or mentions researching, validating, or sanity-checking the plan against best practices.
---

# To Research

Validate or invalidate the ideas and assumptions baked into a PRD or its implementation issues by researching external best practices, then reconcile the research with the user and fold the approved findings back into the PRD (and optionally the issues).

This skill fits between authoring intent and breaking it down:

1. `to-prd` captures the requested product outcome and the implementation/testing decisions behind it.
2. `to-issues` breaks that outcome into independently-grabbable vertical slices.
3. **`to-research`** pressure-tests the assumptions in the PRD (or the issue set) against external best practices, then updates them to reflect what the research found and the user approved.
4. `issues-to-specs` adds codebase-grounded technical specs.
5. `to-goal` implements, verifies, and audits.

Run it on a PRD right after `to-prd` to harden the plan before slicing, or on an issue set after `to-issues` to validate the slices. It does NOT implement anything and does NOT invent product intent — it tests existing ideas against the outside world and helps the user decide what to change.

The issue tracker and triage label vocabulary should have been provided by `/setup-matt-pocock-skills`. If they are missing, inspect the repo's agent docs first; if still missing, tell the user to run setup before using this skill.

## Orchestration model

Researching every assumption sequentially in one context is slow, biased toward the first thing found, and burns the orchestrator's window. This skill is built around a **main orchestrator that dispatches a team of research agents in parallel**, then synthesizes their findings before involving the user.

The orchestrator owns five phases and must not skip them:

1. **Extract** — Read the PRD/issues and pull out the discrete, researchable claims: assumptions, technology and library choices, architectural patterns, testing strategy, security/performance bets, and UX patterns. Each becomes a research target with the original rationale attached.
2. **Dispatch** — Partition the research targets into coherent briefs and dispatch a team of web-research agents in parallel. Each agent searches external sources for best-practice guidance that validates or invalidates its targets and returns cited evidence.
3. **Synthesize** — Reconcile all returned findings into one holistic picture: dedupe, resolve conflicting evidence, and rank by impact on the PRD. Classify every target as confirmed, challenged, or uncertain, and surface new best practices the PRD missed.
4. **Align** — Interview the user one question at a time (grill-me style) about every finding that would change the plan, each with a research-grounded recommendation, until you reach shared decisions.
5. **Update** — Fold only the approved decisions into the PRD, and into the issues if the user wants, preserving original ownership and citing the research.

**When to use the team (strongly enforced):**

- **More than 3 research targets**: you MUST use the parallel team workflow. Do not research them one-by-one in the main context by default.
- **3 or fewer targets, or one tightly-coupled question**: a single-pass research is acceptable. Still run Extract, Synthesize, Align, and Update — just without fan-out.

Never silently downgrade a large set of assumptions to sequential research to save effort. If you cannot dispatch agents in the current environment (no subagent capability), say so explicitly, then fall back to sequential research one brief at a time and tell the user the team workflow was unavailable.

Each research agent is a fresh subagent with its own context window. Pass it only the compact packet in step 5 — never fork the whole parent conversation. Dispatch in bounded waves (a handful at a time) so a large set does not spawn a fleet of agents or overwhelm synthesis.

## Process

### 1. Resolve the input

Arguments may be a PRD issue, an issue set, issue numbers, URLs, local markdown paths, or search terms. The two supported input modes are:

- **PRD mode**: a single PRD (issue or document). Research validates the PRD's decisions; updates land on the PRD, optionally cascading to issues.
- **Issues mode**: a set of implementation issues (usually children of a PRD). Research validates the slices; updates land on the issues, and optionally on the parent PRD.

If the user passes arguments, resolve them to one of the modes above and read the full body and comments.

If the user passes no arguments, work from the current conversation context if a PRD or issue set is clearly in play; otherwise query the issue tracker and show a numbered list of PRDs/issue sets (reference, title, status, child count) and ask the user to pick one before doing anything. If exactly one obvious target exists, show it and ask for confirmation rather than silently selecting it.

Confirm the mode with the user if it is ambiguous, because it determines where updates are written.

### 2. Build shared context (orchestrator)

Do one shared context pass and turn it into a reusable brief every research agent receives, so the agents do not each rediscover the same project facts:

- the PRD (problem, solution, implementation decisions, testing decisions, out of scope) and/or the issue set
- `CONTEXT.md`, `CONTEXT-MAP.md`, and relevant ADRs when present — the research must respect decisions already made and use the project's domain vocabulary
- the project's tech stack, constraints, and conventions, so research is scoped to what is actually usable here (e.g. don't recommend a Python library for a Rails app)

Record this brief compactly. Its job is to keep research relevant: a "best practice" that ignores the project's stack or an existing ADR is noise.

### 3. Extract research targets (orchestrator)

Read the PRD/issues and extract the discrete, researchable claims. Pull from the PRD's **Implementation Decisions**, **Testing Decisions**, **Solution**, and **Out of Scope** sections, and from each issue's **What to build** and **Acceptance criteria**. Look specifically for:

- **Technology / library / service choices** ("use X for Y")
- **Architectural patterns** (the chosen module shapes, data flows, integration patterns)
- **Approach assumptions** (implicit bets about how something should be built or sequenced)
- **Testing strategy** (what will be tested and how)
- **Security / performance / scale bets** (assumptions about safety, throughput, limits)
- **UX / product patterns** (interaction models assumed to be standard)

For each target record:

```markdown
Target: [one-line claim or assumption, in the project's vocabulary]
Source: [PRD section or issue reference it came from]
Stated rationale: [why the PRD/issue chose this, if stated — else "implicit"]
What would validate it: [evidence that confirms this is sound]
What would invalidate it: [evidence that contradicts it]
Impact if wrong: [how much of the plan changes if this assumption fails]
```

Drop targets that are pure internal product intent (e.g. "users want feature X") with no external best-practice angle — research can't validate what the user wants. Keep targets where the outside world has real guidance (how to build it, what to use, what pitfalls exist). Show the extracted target list to the user and let them add, remove, or reprioritize before you dispatch.

### 4. Partition into research briefs (orchestrator)

Group related targets into coherent **research briefs**, one per agent:

- Put targets that share a topic (same technology, same architectural area) in one brief so a single agent builds deep context once.
- Keep unrelated topics in separate briefs so they research in parallel without cross-talk.
- Aim for briefs that are coherent and roughly balanced. One agent per brief.

Apply the team-vs-sequential rule from the Orchestration model: multiple briefs → dispatch the parallel team (step 5); a single small brief → research it in the main context, still using the agent return format (step 5) and synthesis (step 6).

### 5. Dispatch the research team (parallel)

Dispatch one fresh subagent per brief, running in parallel in bounded waves. Each agent researches its targets against external sources and returns cited findings — it does not touch the issue tracker.

Each agent receives a compact packet:

- The shared project brief from step 2 (stack, constraints, conventions, domain vocabulary, relevant ADRs).
- Its assigned research targets with rationale, validate/invalidate criteria, and impact.
- Instruction to search the web for **authoritative, current** best-practice guidance (official docs, well-regarded engineering write-ups, maintained projects, standards) and to prefer primary/authoritative sources over SEO content.
- Instruction to actively seek **disconfirming** evidence, not just confirmation — the goal is to invalidate weak assumptions, not rubber-stamp them.
- Instruction to scope every recommendation to the project's actual stack and constraints, and to flag when guidance conflicts with an existing ADR rather than silently overriding it.
- Instruction to cite sources (title + URL) for every material claim and to return **uncertain** when the evidence is thin or conflicting rather than fabricating a verdict.

> If a `deep-research` skill is available in the environment, an agent may invoke it for a target that needs a deep, multi-source, fact-checked dive. Otherwise use the available web search/fetch tools directly. Either way, findings must be cited.

Each agent returns a compact result packet per target:

```markdown
Target: [the claim researched]
Verdict: validated | challenged | invalidated | uncertain
Confidence: high | medium | low
Evidence:
- [finding] — [source title + URL]
- [finding] — [source title + URL]
Recommended alternative: [if challenged/invalidated — the better approach, scoped to this stack; else "none"]
Tradeoffs: [what the recommendation costs or risks]
Conflicts with: [existing ADR/decision it contradicts, or "none"]
Impact on plan: [what in the PRD/issues would change if this verdict is accepted]
```

Wait for all agents in a wave to return before synthesizing. Do not accept a finding as final just because an agent produced one.

### 6. Synthesize holistically (orchestrator)

Reconcile all returned findings into one coherent picture before involving the user. This is mandatory — it is the reason the work was extracted and dispatched rather than researched ad hoc.

First, gate each finding: reject and re-research any that cite no sources, ignored the stack/constraints, or asserted a confident verdict on thin evidence.

Then reconcile across the full set:

- **Dedupe**: collapse the same finding surfaced by multiple agents into one.
- **Resolve conflicts**: where two agents found contradictory evidence, weigh source authority and recency and state the reconciled verdict (or mark it genuinely contested).
- **Cross-target coherence**: if accepting one recommendation undermines another target's assumption, surface the interaction rather than treating targets in isolation.
- **Rank by impact**: order findings by how much of the PRD/issues changes if accepted.

Classify every target into:

- **Confirmed** — research validates it; no change needed. Split these by stakes: **high-impact confirmed** (a load-bearing assumption a lot of the plan rests on — surface it for explicit user sign-off) vs **routine confirmed** (just report it, don't grill on it).
- **Challenged / invalidated** — research contradicts or weakens it; needs a user decision.
- **New recommendation** — a best practice the PRD missed entirely; offer it as an addition.
- **Uncertain / contested** — evidence is thin or split; flag for a judgment call.

Produce a short synthesis the user can skim before the interview begins.

### 7. Align with the user, one question at a time

Interview the user about the findings until you reach shared, recorded decisions — the same posture as `grill-me`: relentless, one question at a time, walking the decision tree in dependency order, and **providing your recommended answer for each question**.

Rules:

- Ask about every **challenged/invalidated** target, every **new recommendation** worth adopting, and every **uncertain/contested** point that needs a judgment call.
- Also surface every **high-impact confirmed** target — not to change it, but to get the user's explicit sign-off that this load-bearing assumption is settled. Frame it as a confirmation: "Research backs this; a lot of the plan rests on it — good to lock in?" so the user can still challenge it if they know something the research doesn't.
- Do **not** grill on **routine confirmed** targets — just report them as validated in the summary.
- One question at a time. Each question states: the original assumption, what the research found (with the key source), the recommended decision (or "lock in as-is" for a confirmed target), and its tradeoff. Then ask the user how they want to proceed.
- Resolve dependencies between decisions first; a choice that moots later questions should come earlier.
- If a question can be settled by checking the codebase or an ADR instead of asking, do that and report it rather than burdening the user.
- Record each resolution as an approved decision: lock in as-is, adopt the recommendation, adopt a variant, or defer to Out of Scope. Track them in a running list. A high-impact confirmed target that the user signs off on is recorded as "locked in"; if they instead challenge it, reclassify it and research the objection.

Iterate until every challenged/uncertain finding and every high-impact confirmed target has a decision the user has approved.

### 8. Apply the approved findings

Fold **only** the approved decisions into the source material. Never apply a finding the user did not approve.

- **PRD mode**: edit the relevant PRD sections — `Implementation Decisions`, `Testing Decisions`, `Solution`, `Out of Scope`, `Further Notes`. Adjust each changed decision to reflect the approved direction and cite the research that drove it (source title + URL) so the rationale survives. If the change affects existing child issues, list which issues are now stale and offer to update them (or to run `to-issues` if none exist yet).
- **Issues mode**: update the affected issues' `What to build` / `Acceptance criteria` to reflect approved decisions, and offer to reflect cross-cutting changes back on the parent PRD so the PRD and issues stay consistent.

Preserve ownership, exactly as the rest of the pipeline does:

- preserve original product intent, acceptance-criteria wording, and dependency structure unless the user explicitly approved a change to them
- preserve existing comments, receipts, and status unless the project convention says otherwise
- append a dated/clearly-separated update rather than silently overwriting an older decision, so prior context isn't hidden

Also post a concise **research log** (as a comment on the PRD/issue, or appended to `Further Notes`) listing each target, its verdict, and the deciding source — so a later reader can see what was tested against the outside world and why decisions changed.

For local markdown files, edit the file directly. For hosted trackers, update the body when permitted; otherwise post the changes as a comment.

### 9. Summarize the research pass

After updating, report:

```markdown
Input: [PRD reference | issue set] — mode: [PRD | Issues]
Research: [N agents across M briefs | sequential]
Targets researched: [count]
- Confirmed: [count]
- Challenged/invalidated: [count]
- New recommendations adopted: [count]
- Uncertain/deferred: [count]

Key decisions:
- [assumption] -> [approved decision] -> [deciding source]

Updated:
- [PRD/issue reference] — [what changed]

Stale / needs follow-up:
- [issue reference] — [why it may now be out of date]

Next step:
- [run to-issues to (re)slice the hardened PRD | run issues-to-specs | proceed to to-goal]
```

End by pointing the user at the natural next step in the pipeline (`to-issues` if the PRD changed and issues don't exist or are now stale, otherwise `issues-to-specs` / `to-goal`).
