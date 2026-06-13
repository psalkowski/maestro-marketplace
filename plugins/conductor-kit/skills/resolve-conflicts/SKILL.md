---
description: Use when a rebase or merge has stopped on conflicts that need resolving — Conductor's Resolve Conflicts action and its terminal-mode equivalent. Resolves the conflicted tree, prefers a user's own conflict-resolution skill if present, otherwise follows the bundled forge-aware playbook, preserving both sides' intent. Triggers on /conductor-kit:resolve-conflicts or any "resolve the conflicts / finish the rebase" request.
---

# /conductor-kit:resolve-conflicts

Resolve the in-progress rebase or merge conflicts. Thin and discovery-first: resolve inputs, defer to a user's own skill if they have one, otherwise load the bundled default.

## 1. Resolve inputs (Fallback Chain)

Resolve the **conflicted state** and the **target branch**, noting their source:

- **Conflicted tree:** local git state — `git status` to confirm rebase vs merge and list conflicted files.
- **Forge + target branch:** the Conductor context when set → otherwise `git`/`gh` (the repo's default branch via `git remote show origin`, fall back to `main`).

## 2. Discovery-first dispatch

Scan the skills present in this session's context for one whose **purpose is resolving merge/rebase conflicts**, excluding conductor-kit's own skills. If a clear capability match exists, invoke it with the resolved state and target and **stop** — the user's skill takes precedence. If a discovered skill turns out not to fit, fall through to step 3 rather than failing.

## 3. Fallback — load the playbook

Only if no user skill applies, `Read` `references/playbook.md` (relative to this skill) and follow it.

## 4. Resolve outputs

Report which files conflicted, what each resolution preserved from each side, and anything you had to ask about or were unsure of.
