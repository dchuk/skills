---
name: to-goal
description: Turn a PRD issue, child issue set, or approved plan into a Claude Code or Codex CLI /goal prompt that iterates through all goal-eligible issues until implemented, verified, updated in the issue tracker, and audited complete. Use after to-prd and to-issues, or when the user wants to set a long-running implementation goal from issues.
---

# To Goal

Turn a PRD and its implementation issues into a Claude Code or Codex CLI `/goal`.

This skill is the final step after `to-prd` and `to-issues`:

1. `to-prd` publishes the parent PRD issue.
2. `to-issues` publishes dependency-ordered child issues that reference the parent.
3. `to-goal` turns the parent and child issue set into a long-running goal that works through the children until complete.

It can also consume a plain approved plan or a manually supplied list of issues, but the preferred input is a PRD issue with child implementation issues.

This skill borrows the useful goal-control ideas from GoalBuddy without creating GoalBuddy boards, dashboards, `state.yaml`, or local servers. The issue tracker remains the durable task board. It only plans subagent use when the user explicitly passes `--agent-per-issue`.

## Goal target

Default to producing goal commands for both Claude Code and Codex CLI unless the user names one.

- **Claude Code**: `/goal` starts immediately when set. The completion condition must be visible in the transcript because the goal evaluator judges what Claude reports after each turn.
- **Codex CLI**: goals require the experimental goals feature. If `/goal` is unavailable, tell the user to enable it from `/experimental` or set `goals = true` under `[features]` in `config.toml`. Keep the final `/goal` command under 4,000 characters.

Do not start or replace a goal implicitly. Prepare the handoff first and wait for the user to approve starting it.

## Invocation arguments

Invocation arguments may be a PRD issue, issue set, issue numbers, URL, local path, search terms, or flags.

Supported flags:

- `--agent-per-issue`: generate a goal that keeps the main agent as the coordinator and executes each included child issue in a fresh subagent. Use this to preserve the main context window during long PRD implementations.

When parsing arguments, separate flags from target selectors. Target selectors still resolve the PRD or issue set. Flags change only the generated goal contract.

## Process

### 1. Resolve the target work

If the user passed arguments, resolve them as one of:

- a parent PRD issue number, URL, or local issue path
- child issue numbers, URLs, or local issue paths
- search terms that identify a PRD or issue set
- a plan or PRD document path

If the user passed no arguments, query the configured issue tracker and show a numbered list of available PRDs or issue sets. Include:

- issue reference
- title
- status
- child issue count
- completed child issue count
- blocked or HITL child issue count

Ask the user to select one before drafting the goal. If only one obvious issue set exists, show it and ask for confirmation rather than silently selecting it.

The issue tracker and triage label vocabulary should have been provided by `/setup-matt-pocock-skills`. If they are missing, inspect the repo's agent docs first; if still missing, tell the user to run setup before using this skill.

### 2. Gather full context

For a PRD issue set:

- read the full parent PRD issue body and comments
- find child issues created by `to-issues` via the `## Parent` section, issue links, comments, labels, or issue tracker relationships
- read every child issue body and comments, not just titles
- read blocker references and order child issues by dependency
- inspect existing issue tracker conventions for closing or updating parent PRD issues

For any target work:

- read `CONTEXT.md`, `CONTEXT-MAP.md`, and relevant ADRs when present
- read issue tracker setup docs, especially tracker type and triage label vocabulary
- identify commands, tests, screenshots, artifacts, or manual checks that prove completion

### 3. Compile goal intake

Before drafting the goal, summarize the selected work as an intake. Keep it concise, but make it explicit enough to prevent a goal from succeeding at the wrong thing.

Record:

- **Target**: selected parent PRD, issue set, or plan
- **Input shape**: PRD issue set, child issue list, approved plan, recovery, or audit
- **Authority**: requested, approved, inferred, needs approval, or blocked
- **Proof type**: test, demo, artifact, metric, review, source-backed answer, or decision
- **Completion proof**: observable signal that the full PRD outcome is complete
- **Likely misfire**: how the goal could appear successful while missing the user's real outcome
- **Blind spots**: risks, missing checks, unclear ownership, or unstated product choices
- **Existing plan facts**: user-provided sequencing, constraints, issue links, or verification expectations to preserve

If `--agent-per-issue` was passed, record this in the intake as:

- **Agent mode**: main coordinator with a fresh subagent per included issue

If authority is blocked, completion proof is missing, or the likely misfire is severe, ask one focused question before drafting the goal.

### 4. Classify the issue set

Classify every child issue before drafting the goal:

- **Included**: goal-eligible AFK issue that can be implemented and verified without human input
- **Pause-before**: issue that can be reached, but requires HITL input before implementation can continue
- **Excluded**: issue outside the current goal, unrelated, duplicate, or blocked by unresolved product/architecture decisions
- **Already complete**: issue whose acceptance criteria are already implemented and verified

Do not include unresolved HITL work in an unattended goal. Either make the goal stop before that issue or exclude it and name the exclusion.

Do not create one goal for unrelated work. If the selected set contains multiple independent objectives, recommend multiple goals and start with the first dependency.

### 5. Draft the goal contract

The contract must include:

- **Objective**: implement the selected PRD issue set through all included child issues
- **Stopping condition**: included issues fully satisfy every acceptance criterion, validation evidence proves each criterion passes, issue checkboxes reflect that verified state, child issue states are updated, and the parent PRD is handled according to repo convention
- **First-read context**: parent PRD, child issues, issue tracker docs, `CONTEXT.md`, ADRs, and any referenced plans
- **Issue checkpoints**: included child issues in dependency order
- **Execution rules**: one active issue at a time, largest safe useful slice, continue around blocked issues when safe, and final audit before completion
- **Issue tracker updates**: how to reflect verified acceptance criteria in checkboxes, close or update children, and handle the parent PRD based on observed convention
- **Validation loop**: per-issue checks and final full-suite or end-to-end checks
- **Pause conditions**: HITL issue, blocked dependency, missing credential, unavailable service, unclear acceptance criteria, failing check that needs product judgment, or issue tracker permission failure
- **Progress format**: a clear count of completed issues out of total, plus current issue and validation state
- **Agent mode**: normal main-thread execution, or fresh subagent per issue when `--agent-per-issue` was passed

### 6. Add agent-per-issue rules when requested

Only include this section in the generated goal when the user passed `--agent-per-issue`.

The main agent remains the coordinator:

- Read the parent PRD, issue set, tracker convention, `CONTEXT.md`, and ADRs once.
- Select the next included issue in dependency order.
- Start a brand-new subagent for that issue. Do not reuse a subagent across issues.
- Pass only the compact issue packet to the subagent, not the whole parent conversation.
- Wait for the subagent result before starting the next issue.
- Review the result, run or inspect validation as needed, update issue acceptance checkboxes, append the receipt, update issue status, report progress, and then continue.
- Keep final audit, parent PRD handling, and goal completion decisions in the main agent.

Sequential execution is the default. Do not parallelize child issues unless the user separately asks for parallelism and the write scopes are clearly disjoint.

Each subagent receives a compact issue packet:

- Issue reference, title, body or path, and current status
- Parent PRD or goal contract reference
- Relevant `CONTEXT.md`, ADR, issue tracker convention, and implementation-notes paths or excerpts
- Existing `## Technical Spec` or `## Technical Plan` from the issue, when present
- Acceptance criteria exactly as written
- Dependency, blocker, and pause-condition notes
- Expected validation commands, artifacts, routes, or manual checks
- Requirement to update `implementation-notes.md` for decisions, deviations, tradeoffs, and open questions when applicable
- Requirement to stop and return blocked if criteria conflict, credentials are missing, required services are unavailable, or product judgment is needed

Each subagent returns a compact result packet:

```markdown
Subagent result: done | blocked
Issue: [reference and title]
Changed files:
- [paths or "none"]
Summary:
- [what changed or why blocked]
Acceptance criteria evidence:
- [criterion] — [passing evidence or blocker]
Validation:
- [command, artifact, screenshot, or manual check and result]
Issue tracker changes made by subagent:
- [none unless explicitly delegated]
Implementation notes:
- [updated/not needed/blocker]
Remaining blockers:
- [none or blocker]
```

The main agent must not mark an issue done just because the subagent says it is done. The main agent must verify that every acceptance criterion passes, update checkboxes so they reflect the passing state, append the implementation receipt, and update issue status according to repo convention.

### 7. Encode execution rules

The generated goal must tell the runner:

- Work one child issue at a time in dependency order unless the user explicitly asks for parallel work.
- Before implementing each issue, read its `## Technical Spec` if present. Also accept an older `## Technical Plan` heading if present. If neither exists, do a brief codebase-grounded planning pass for that issue before changing code: inspect the relevant files at HEAD, identify existing patterns to follow, map each acceptance criterion to implementation areas and validation evidence, name the focused tests or checks to run, state the posture constraints for the issue, and list explicit out-of-scope follow-ups. Treat a missing technical spec as a warning to plan carefully, not as a blocker.
- Complete each issue as a coherent vertical slice. Do not stop after tiny helper work when the issue's behavior is not done.
- Do not mark the goal complete after planning, discovery, or selecting the next issue.
- Do not mark the goal complete after one issue if more included issues remain.
- Before marking an issue done, prove every acceptance criterion passes. Then update the issue checklist so every passing criterion is checked. Leave any unproven or failing criterion unchecked and treat the issue as blocked or incomplete.
- If one issue is blocked, write a blocker receipt, update that issue appropriately, and continue with any safe unblocked issue.
- Use review or reorientation at phase, risk, rejected-verification, ambiguity, or final-completion boundaries. Do not insert a review after every small change by habit.
- Finish only after a final audit maps child issue receipts, validation evidence, and parent PRD handling back to the original PRD outcome.

If `--agent-per-issue` was passed, add:

- Keep the main agent as coordinator and final auditor.
- Execute each included issue in a fresh subagent.
- Do not fork or copy the whole parent conversation into the subagent. Provide the compact issue packet instead.
- Do not start the next issue until the current subagent result has been reviewed and the issue tracker has been updated or marked blocked.

### 8. Require receipts

Each completed child issue needs fully passing acceptance criteria, issue checkboxes that reflect that passing state, and a compact implementation receipt before it is closed or marked complete.

Acceptance criteria rules:

- Treat the criterion text as the requirement. The checkbox is only the visible record that the requirement passed.
- For local markdown issue files, change a checklist item from `- [ ]` to `- [x]` only after implementation and validation evidence prove that criterion passes.
- For hosted issue trackers, update the issue body checklist when the tracker permits it, but only for criteria that have passing evidence.
- If the tracker does not allow body edits, include an explicit acceptance-criteria checklist in the receipt and do not claim the issue tracker is fully updated unless the status/labels/comments also match the repo convention.
- Never mark `Status: done`, close an issue, or count it in completed progress while any required acceptance criterion is failing, unproven, unchecked, or unmapped to receipt evidence.

Receipt format:

```markdown
## Implementation Receipt

Result: done | blocked
Summary: [what changed or why blocked]
Acceptance criteria:
- [x] [criterion] — [evidence]
- [ ] [criterion] — [why still incomplete, if blocked]
Validation:
- [command, artifact, screenshot, or manual check]
Changed behavior:
- [user-visible or domain behavior]
Remaining blockers:
- [none or blocker]
```

For blocked issues, record the blocker and continue with safe unblocked work when possible.

For the parent PRD, require a final audit comment that lists included child issues, acceptance checklist status, receipt status, final validation, excluded/pause-before issues, and whether the PRD should be closed according to repo convention.

### 9. Prepare CLI-specific goal commands

Progress reports must include:

```markdown
Progress: [completed]/[total] issues complete
Current: [issue reference and title]
Agent mode: [main | fresh subagent]
Subagent: [not used | not started | running | done | blocked]
Acceptance criteria: [passing and checked]/[total]
Receipt: [posted/not yet/blocked]
Verified: [what passed, or "not yet"]
Issue tracker: [updated/not yet/blocked]
Remaining: [count and next issue reference]
Blocked: [none or blocker]
```

When `--agent-per-issue` is not passed, use `Agent mode: main` and `Subagent: not used`.

For Claude Code, phrase the command as a transcript-visible completion condition:

```markdown
/goal Complete the selected PRD issue set. Continue until the transcript shows that [completed]/[total] included child issues fully satisfy every acceptance criterion, have issue checkboxes updated to reflect those passing criteria, have implementation receipts mapping evidence to each criterion, passed validation, were updated in the issue tracker, and the parent PRD has a final audit handled according to repo convention. Work one issue at a time in dependency order, continue around blocked issues when safe, report completed/total progress and criteria passing-and-checked/total after each issue, and pause before [pause conditions].
```

When `--agent-per-issue` is passed, add this Claude Code requirement to the command or full goal contract:

```markdown
Use a fresh Claude Code subagent with its own context window for each included child issue. Do not use a fork that copies the full parent conversation. The main thread stays the coordinator: it selects the next issue, gives the subagent only the compact issue packet, waits for the result, verifies acceptance criteria, updates checkboxes and receipts, reports progress, and then starts the next fresh subagent. If no suitable custom subagent exists, use a general-purpose subagent if available; otherwise state that subagent mode is unavailable and pause before implementing locally.
```

For Codex CLI, phrase the command as a durable execution objective:

```markdown
/goal Implement the selected PRD issue set without stopping until every included child issue fully satisfies every acceptance criterion, has issue checkboxes updated to reflect those passing criteria, has an implementation receipt mapping evidence to each criterion, passed validation, child issue tracker state has been updated, and the parent PRD has a final audit handled according to repo convention. Read [first-read context] first. Work one issue at a time in dependency order: [issue checkpoints]. Continue around blocked issues when safe. Report completed/total progress and criteria passing-and-checked/total after each issue. Pause for [pause conditions].
```

When `--agent-per-issue` is passed, add this Codex CLI requirement to the command or full goal contract:

```markdown
For each included child issue, explicitly spawn a fresh Codex worker subagent. Do not set fork_context and do not copy the full parent conversation; pass only the compact issue packet. The main thread must wait for the worker result, review and verify it, update acceptance checkboxes and receipts, report progress, and only then start the next worker. Keep execution sequential by default. Use parallel workers only if the user later asks and write scopes are disjoint.
```

If either command would exceed 4,000 characters, recommend storing the full goal contract in the parent PRD issue, a child tracking issue, or a repo plan document, then make the `/goal` command reference that durable artifact.

## Output template

```markdown
## Goal target

[Selected parent PRD / issue set / plan]

## Intake

- Input shape: [shape]
- Authority: [authority]
- Proof type: [type]
- Completion proof: [proof]
- Likely misfire: [misfire]
- Blind spots: [risks considered]
- Existing plan facts: [facts to preserve]
- Agent mode: [main | main coordinator with fresh subagent per issue]

## Issue set

- Included: [count and issue refs]
- Already complete: [count and issue refs]
- Pause-before: [count and issue refs]
- Excluded: [count and issue refs]

## Goal handoff

Objective:
[One durable implementation outcome]

Stopping condition:
[Verifiable done state, including fully passing acceptance criteria, checkboxes reflecting that state, receipts, and issue tracker updates]

First-read context:
- [Parent PRD, child issues, tracker docs, CONTEXT.md, ADRs, plans]

Issue checkpoints:
- [Issue 1]
- [Issue 2]

Execution rules:
- Work one issue at a time.
- Complete the largest safe useful slice for each issue.
- Continue around blocked issues when safe.
- Finish only after final audit.

Subagent execution:
[Omit if not using --agent-per-issue. Otherwise describe the fresh-subagent-per-issue rule, issue packet, result packet, and CLI-specific Claude/Codex requirements.]

Validation loop:
- [Per-issue and final checks]

Issue tracker updates:
- [Acceptance criteria proof, checkbox update, child issue receipt, and update behavior]
- [Parent PRD final audit convention]

Pause conditions:
- [Condition that should stop the goal]

Progress reports:
Use the completed/total receipt format after each issue.

Claude Code goal:
[Claude-specific /goal command]

Codex CLI goal:
[Codex-specific /goal command]
```

End by asking whether the user wants to revise the contract, publish it somewhere durable, or start the goal.
