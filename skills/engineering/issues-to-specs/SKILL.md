---
name: issues-to-specs
description: Turn approved implementation issues into lightweight codebase-grounded technical specs, orchestrating a team of parallel speccing agents when there are many issues. Use after to-issues and before to-goal when issues need technical planning, TDD-shaped behavior slices, validation plans, or clearer implementation posture.
---

# Issues To Specs

Turn implementation issues into lightweight technical specs that are ready for goal-driven implementation.

Use this after `to-issues` and before `to-goal`:

1. `to-prd` captures the requested product outcome.
2. `to-issues` breaks that outcome into independently-grabbable vertical slices.
3. `issues-to-specs` inspects the existing codebase and adds a technical spec to each issue.
4. `to-goal` consumes the issues and specs to implement, verify, update checkboxes, and audit completion.

This skill does not implement the issues. It adds just enough technical planning that the implementation agent can start from codebase facts, existing patterns, and behavior-focused validation instead of guessing.

## Orchestration model

Speccing many issues one-by-one in a single context is slow, loses cross-issue consistency, and burns the orchestrator's context window. This skill is built around a **main orchestrator that dispatches a team of speccing agents in parallel**, then reconciles their output.

The orchestrator owns three phases and must not skip them:

1. **Map** — The orchestrator reads every selected issue plus shared project context and produces an interconnection map: which issues are independent, which touch the same files/modules/schemas/routes/contracts, and which depend on each other. This is a high-level pass, not a spec.
2. **Dispatch** — The orchestrator partitions the issues by independence and dispatches the speccing work to a team of agents working in parallel. Independent issues go to separate agents; tightly interconnected issues are grouped onto one agent or given an explicit shared-decision brief.
3. **Synthesize and align** — After the agents return their spec drafts, the orchestrator reconciles them: resolves conflicts on shared surfaces, enforces consistent naming/contracts/interfaces, dedupes overlapping work, fills gaps, confirms acceptance-criteria mapping, and only then writes the final specs onto the issues.

**When to use the team (strongly enforced):**

- **More than 3 spec-eligible issues**: you MUST use the parallel team workflow. Do not spec them sequentially in the main context by default.
- **3 or fewer issues, or nearly everything is interconnected into one cluster**: a single-pass sequential spec is acceptable. Still run the Map and Synthesize phases (they are quick), just without fan-out.

Never silently downgrade a large issue set to sequential speccing to save effort. If you cannot dispatch agents in the current environment (no subagent capability), say so explicitly, then fall back to sequential speccing one cluster at a time and tell the user the team workflow was unavailable.

Each parallel agent is a fresh subagent with its own context window. Pass it only the compact packet described in step 6 — never fork or copy the whole parent conversation. Dispatch agents in bounded waves rather than all at once (see step 6), so a large set does not spawn a fleet of agents or overwhelm synthesis.

## Process

### 1. Resolve the issue set

Arguments may be a parent PRD issue, issue set, issue numbers, URLs, local paths, or search terms.

If the user passes arguments, resolve them as:

- a parent PRD issue whose child implementation issues should be specced
- specific child issues to spec
- local markdown issue files
- search terms that identify an issue set

If the user passes no arguments, query the configured issue tracker and show a numbered list of available PRDs or issue sets. Include the issue reference, title, status, child issue count, and how many child issues already contain `## Technical Spec`.

Ask the user to select one before editing issues. If there is only one obvious issue set, show it and ask for confirmation rather than silently selecting it.

The issue tracker and triage label vocabulary should have been provided by `/setup-matt-pocock-skills`. If they are missing, inspect the repo's agent docs first; if still missing, tell the user to run setup before using this skill.

### 2. Build shared context (orchestrator)

The orchestrator does one shared context pass and turns it into a reusable brief that every speccing agent receives. Do this once, centrally, so the agents do not each rediscover the same project facts.

Read and capture:

- the parent PRD or source plan
- `CONTEXT.md`, `CONTEXT-MAP.md`, and relevant ADRs when present
- issue tracker conventions and the triage label vocabulary
- repo-wide naming, testing, and layering patterns the specs must follow
- the `tdd` skill principles that shape every spec (see step 8)

Prefer facts from the current codebase over guesses. Do not invent file paths, commands, or APIs that you have not checked. Record the shared brief compactly enough to hand to each agent.

### 3. Map overlap and interconnectedness (orchestrator)

Build an interconnection map of the issue set — a high-level mapping pass, not specs. Scale the read depth to the set size so this phase does not reload the whole cost back into the main context:

- **Small set (≈10 or fewer issues)**: the orchestrator reads each issue body, comments, and linked blockers/dependencies directly.
- **Large set**: do a light first pass over titles, acceptance criteria, and touched-area signals to spot likely shared surfaces, then deep-read only where collision risk is suspected. Delegate the deep reads to read-only **scout agents** (one per suspected cluster) that each return a compact "surfaces touched + dependencies" note, and assemble those notes into the map. This keeps the orchestrator's context free for synthesis.

Produce an interconnection map that records, for the issue set:

- **Shared surfaces**: files, modules, schemas, migrations, routes, services, jobs, or UI surfaces that more than one issue is likely to touch.
- **Dependency edges**: which issues block or depend on which others, and the implied ordering.
- **Contract boundaries**: APIs, interfaces, data shapes, or domain concepts that multiple issues must agree on.
- **Collision risks**: naming, conventions, or design decisions where two issues could diverge if specced in isolation.
- **Independence**: issues that touch disjoint surfaces and can be specced with no cross-talk.

This map is what makes the dispatch safe and the synthesis honest. Keep it concise but explicit.

### 4. Triage and partition by independence (orchestrator)

First, coarse-triage each issue into:

- **Spec-eligible**: ready to spec or needs a spec refresh.
- **Already specced**: a current `## Technical Spec` exists and still matches the codebase — skip dispatch.
- **Not implementation-ready**: duplicate, obsolete, blocked by an unresolved decision, or not an implementation issue — exclude and name why.

Then partition the spec-eligible issues into **dispatch groups** using the interconnection map:

- Put **independent** issues in their own group so they can be specced fully in parallel.
- Group **tightly interconnected** issues (shared surface + contract boundary they must co-decide) onto a single agent so one mind owns the shared decision. Prefer this over splitting a shared contract across two agents.
- For looser cross-issue links, keep issues in separate groups but attach a **shared-decision brief** to each affected packet that states the agreed contract, naming, or interface up front so drafts converge instead of conflict.

Aim for groups that are coherent and roughly balanced. One agent per group.

### 5. Confirm execution mode

Apply the team-vs-sequential rule from the Orchestration model to the partitioned groups: multiple groups → dispatch the parallel team (step 6); a single small cluster → spec sequentially in the main context, still using the spec template (step 7), TDD shaping (step 8), and the synthesis/align checks (step 9).

Ask one focused question only if a clarification would materially change how the work is partitioned or whether an issue is spec-eligible at all. Otherwise record the uncertainty in the relevant spec under risks and blockers.

### 6. Dispatch speccing to the agent team (parallel)

Dispatch one fresh subagent per dispatch group, running in parallel. Each agent specs its assigned issue(s) end to end and returns drafts — it does not write to the issue tracker itself. The orchestrator finalizes after synthesis (step 9).

Dispatch in bounded waves rather than all at once: cap concurrent speccing agents (a handful at a time is usually right) and drain each wave before launching the next. Waves are driven by group count, not raw issue count. For a large set this keeps the synthesis step (step 9) tractable and avoids spawning a fleet of agents.

Each agent receives a compact packet:

- The shared project brief from step 2 (context, conventions, patterns, tracker vocabulary, TDD principles).
- The relevant slice of the interconnection map: this group's shared surfaces, dependency edges, and contract boundaries.
- Any **shared-decision brief**: contracts, names, interfaces, or data shapes already fixed by the orchestrator that this group must honor exactly.
- For each assigned issue: reference, title, full body, current status, acceptance criteria exactly as written, and any existing `## Technical Spec` to refresh.
- The spec template (step 7) and the TDD-shaping rules (step 8) to follow.
- Instruction to inspect the current codebase at HEAD for the modules, tests, routes, schemas, services, jobs, or UI surfaces its issues touch — and to ground every claim in checked facts, never invented paths or commands.
- Instruction to return **needs clarification** for any issue whose product behavior, architecture, credentials, service dependencies, or acceptance criteria are too unclear to spec, rather than guessing.

Each agent returns a compact result packet per issue:

```markdown
Spec result: drafted | needs-clarification | already-current
Issue: [reference and title]
Codebase read:
- [files, modules, docs, tests, routes, schemas, or commands inspected]
Draft spec:
- [the full ## Technical Spec body, following the template]
Shared-surface touches:
- [files/contracts/interfaces this spec touches that other issues may also touch]
Cross-issue assumptions:
- [contracts, names, or shapes this spec assumes other issues will honor]
Open questions / blockers:
- [clarifications needed, or "none"]
```

Wait for all agents in the wave to return before synthesizing. The orchestrator must not accept a draft as final just because an agent produced one.

### 7. Spec template

Each speccing agent (or the orchestrator in sequential mode) produces a `## Technical Spec` per issue using this template.

Keep the spec short enough to remain useful during implementation. It should guide, not over-prescribe. Prefer behavior, interfaces, codebase patterns, and validation over line-by-line implementation instructions.

```markdown
## Technical Spec

Codebase read:
- [files, modules, docs, tests, routes, schemas, or commands inspected]

Public interface to prove:
- [API route, CLI command, UI workflow, job behavior, service boundary, or domain behavior]

Existing patterns to follow:
- [helpers, modules, tests, conventions, or architecture already present]

Behavior slices:
1. [behavior] — test/check: [focused test, command, route, or manual check]
2. [behavior] — test/check: [focused test, command, route, or manual check]

Tracer bullet:
- [first narrow end-to-end behavior to prove]

Acceptance criteria mapping:
- [criterion] -> [behavior slice] -> [validation evidence]

Shared surfaces and cross-issue contracts:
- [files, interfaces, schemas, or names shared with other issues, and the agreed contract]

Posture:
- [constraints for this issue: no new dependency, no schema change, no route change, preserve API shape, etc.]

Out of scope:
- [follow-ups, deferred ideas, or tempting expansions not included]

Risks / blockers:
- [unknowns, credentials, service availability, product judgment, or architectural conflicts]
```

### 8. Apply TDD-shaped planning

Use the repo's `tdd` skill principles to shape every spec:

- Plan tests and checks around observable behavior through public interfaces.
- Avoid implementation-coupled tests, private-method tests, or mocks of internal collaborators unless the project convention already requires them.
- Do not plan a horizontal "all tests first, then all implementation" batch.
- Plan vertical behavior slices: one behavior, one test or check, one minimal implementation path, then repeat.
- Identify the tracer bullet: the first narrow end-to-end test or check that proves the issue's path works.
- Put refactor or cleanup work after the behavior is green, not before.
- Name the most important focused tests or checks, but do not try to test every edge case.

If an issue is not suitable for TDD, explain why in the spec and provide the closest behavior-focused validation loop.

### 9. Synthesize and align (orchestrator)

After the agents return, the orchestrator reconciles all drafts into one coherent spec set before anything is written to the issue tracker. This step is mandatory — it is the whole reason the work was mapped before being dispatched.

First, gate each draft for quality. A returned draft is an input to synthesis, not an accepted spec: reject and re-spec any draft that cites file paths, commands, or APIs that do not exist, skipped the codebase-read grounding, or left acceptance criteria unmapped.

Then square up the following across the full set:

- **Shared-surface conflicts**: where two drafts touch the same file, schema, route, or interface, confirm they agree. If they diverge, decide the single correct contract and adjust the affected specs.
- **Contract and naming consistency**: enforce one name, one data shape, and one interface for any concept that crosses issues. Update each spec to use it.
- **Cross-issue assumptions**: verify every "assumes other issue will do X" is actually satisfied by that other issue's spec. If not, fix one side or record a blocker.
- **Dependency ordering**: confirm tracer bullets and behavior slices respect the dependency edges from the map.
- **Duplication and gaps**: remove work two specs both claim; assign orphaned shared work to exactly one issue.
- **Acceptance mapping**: confirm every acceptance criterion on every issue maps to a behavior slice and validation evidence.

If synthesis surfaces a conflict that needs product or architecture judgment, raise one focused question or record it as a blocker on the affected issues rather than papering over it.

If the synthesis materially changes a draft on a shared contract, it is acceptable to re-dispatch just the affected issues with an updated shared-decision brief rather than hand-patching deep conflicts. Limit this to a single realignment wave; if conflicts remain after it, raise a focused question or record a blocker rather than looping. Only after synthesis are the specs final.

### 10. Preserve issue ownership

Do not rewrite the original product intent, acceptance criteria, or dependency structure unless the user explicitly asks.

When updating issue bodies:

- preserve existing comments and receipts
- preserve acceptance criteria wording
- preserve issue status unless the project convention says otherwise
- append a dated or clearly separated spec update if replacing an older spec would hide useful context

For local markdown issue files, edit the issue file directly. For hosted issue trackers, update the issue body when permitted; otherwise post the technical spec as a comment.

Only the orchestrator writes finalized specs to the issue tracker, and only after step 9.

### 11. Summarize the spec pass

After updating issues, report:

```markdown
Issues specced: [count]
Dispatch: [N agents across M groups | sequential]
Already current: [count]
Needs clarification: [count]
Not implementation-ready: [count]

Interconnection summary:
- [shared surfaces and cross-issue contracts that were aligned]

Updated issues:
- [issue reference] — [short title] — [technical spec added/refreshed]

Clarifications needed:
- [issue reference] — [question or blocker]

Ready for to-goal:
- [issue references]
```

End by telling the user that `to-goal` should now read each issue's `## Technical Spec` before implementation.
