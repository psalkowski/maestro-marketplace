---
description: Use when creating a pull request for the current branch — Conductor's Create PR action and its terminal-mode equivalent. Resolves the workspace diff and PR target, prefers a user's own PR-creation skill if one is present, otherwise follows the bundled playbook to commit, push, and open the PR with gh. Triggers on /conductor-kit:create-pr or any "create/open a PR" request.
---

# /conductor-kit:create-pr

Open a pull request for the current branch. Thin and discovery-first: resolve inputs, defer to a user's own skill if they have one, otherwise load the bundled default.

## 1. Resolve inputs (Fallback Chain)

Resolve the **workspace diff** and the **PR target**, noting where each came from:

- **Diff:** `mcp__conductor__GetWorkspaceDiff` when the Conductor MCP is available → otherwise `git diff <remote>/<target>...HEAD` (three-dot, against the merge base) plus `git diff HEAD` for uncommitted work.
- **PR target:** the Conductor target branch when set → otherwise the repo's default branch (`git remote show origin`, fall back to `main`).

## 2. Discovery-first dispatch

Scan the skills present in this session's context for one whose **purpose is creating pull requests**, excluding conductor-kit's own skills. If a clear capability match exists, invoke it with the resolved diff and PR target and **stop** — the user's skill takes precedence. If a discovered skill turns out not to fit, fall through to step 3 rather than failing.

## 3. Fallback — load the playbook

Only if no user skill applies, `Read` `references/playbook.md` (relative to this skill) and follow it end to end.

## 4. Resolve outputs

Report the created PR URL. If a PR already exists for the branch (`gh pr view` succeeds), say so and offer to update its title/body instead of opening a duplicate.
