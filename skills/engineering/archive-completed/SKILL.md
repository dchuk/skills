---
name: archive-completed
description: Archive fully-completed features (a PRD plus its issues) out of the active issue tracker, so the active surface only shows features with outstanding work. On the local-markdown tracker it moves finished feature directories into `archived/`; on GitHub/GitLab it closes the parent PRD once every child issue is terminal. Use when the user wants to clean up, tidy, prune, or archive completed PRDs/issues/features, sweep finished work out of `.scratch/`, close out done PRDs, or shrink the active issue-tracker surface.
---

# Archive Completed

Sweep every feature whose work is fully finished out of the active issue tracker, keeping the active surface small so it only shows features with outstanding work.

First read the tracker config: `docs/agents/issue-tracker.md` tells you whether this repo uses the **local-markdown**, **GitHub**, or **GitLab** tracker, and `docs/agents/triage-labels.md` gives the label vocabulary (use the repo's actual label strings if they differ from the canonical ones below). These should have been written by `/setup-matt-pocock-skills`; if they are missing, inspect the repo's agent docs, and if still missing, tell the user to run setup before using this skill. For "other" trackers (Jira, Linear, etc.), follow the workflow described in `issue-tracker.md` by analogy with the rules below, and confirm the archival action with the user before mutating anything.

## What counts as "fully completed"

A **feature** is a PRD plus its implementation issues. A feature is fully completed when **both** hold:

1. It has **at least one** issue. A feature with only a PRD and no issues is **not** complete — it hasn't been decomposed yet.
2. **Every** issue is in a terminal state. Terminal means:
   - `done`
   - `complete`
   - `wontfix` (a deliberately skipped issue still counts as resolved)

If any issue sits in a non-terminal state (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, an open/unresolved issue, or anything else), the feature is **not** complete — leave it in place.

The PRD's own status is **not** a completion signal. PRDs are commonly left at `ready-for-agent` (or simply left open) even after all their issues land. Judge a feature purely by its issues.

How "terminal" is read depends on the tracker:

- **Local-markdown**: the issue file's `Status:` line is `done`, `complete`, or `wontfix`.
- **GitHub / GitLab**: the issue is **closed** (a `wontfix` issue should already be closed; if your convention leaves it open, the `wontfix` label is terminal too).

## Process — local-markdown tracker

Features live as directories under the tracker root (default `.scratch/`): `<root>/<feature-slug>/PRD.md` plus `<root>/<feature-slug>/issues/<NN>-<slug>.md`.

1. **List** the immediate subdirectories of the tracker root, ignoring `archived/` itself.
2. **Classify** each feature: read the `Status:` line of every file under its `issues/` directory and apply the completion rule above.
3. **Ensure** `<root>/archived/` exists; create it if not.
4. **Mark the PRD** for each fully-completed feature *before* moving it: set its `PRD.md` `Status:` line to `complete` (replace whatever is there). Leave it unchanged if already `complete`. Do not touch any other PRD content or any issue file.
5. **Move** the whole feature directory into `<root>/archived/` using `git mv` to preserve history. If the directory is not git-tracked, fall back to a plain `mv`.
6. **Report** (see summary format below).

Only the PRD `Status:` line may change; issue files are moved untouched. Do **not** commit — leave the changes staged for the user to review.

## Process — GitHub / GitLab tracker

Features are a **parent PRD issue** plus the **child implementation issues** that reference it (the child's body carries a `## Parent` reference, per `to-issues`; sub-issues, task lists, or a shared label may also link them). Nothing is moved on a hosted tracker — archival means closing the parent PRD once its children are all done.

1. **Find candidate features**: list open parent PRD issues (filter by the PRD label/marker the repo uses, e.g. `gh issue list --label prd --state open`, or `glab issue list`).
2. **Resolve children** for each candidate: the issues that reference it as their parent.
3. **Classify**: a feature is complete when it has ≥1 child and **every** child is terminal (closed, or `wontfix`). A parent with no children is not complete.
4. **Confirm before mutating** — there is no staging area on a remote, so present the archival plan (which PRDs will be closed, and their child counts) and get explicit user approval before any write.
5. **Archive** each approved feature: close the parent PRD issue (e.g. `gh issue close <n> --comment "All child issues complete — archiving."` / `glab issue close <n>`). If the repo defines a completed/archived label, apply it too; otherwise closing is the archival signal. Do not reopen, relabel, or edit the child issues — they are already terminal.
6. **Report** (see summary format below).

Do not close a parent whose children are not all terminal, and never close child issues yourself — this skill archives finished features, it does not finish them.

## Summary format

Report concisely:

- **Archived**: feature → issue count (all terminal); note the action taken (local: PRD marked `complete` and directory moved to `archived/`; hosted: parent PRD closed).
- **Kept active**: feature → the non-terminal issues blocking archival, or "no issues yet" for PRD-only features.
