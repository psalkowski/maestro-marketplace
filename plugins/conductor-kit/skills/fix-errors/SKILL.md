---
description: Use when the workspace has failing builds, tests, type checks, CI actions, or runtime errors to diagnose and fix — Conductor's Fix Errors action and its terminal-mode equivalent. Resolves the failing logs through the fallback chain, prefers a user's own error-fixing skill if present, otherwise follows the bundled playbook to fix root causes and re-run to green. Triggers on /conductor-kit:fix-errors or any "fix the errors / make CI pass" request.
---

# /conductor-kit:fix-errors

Diagnose and fix whatever is currently failing. Thin and discovery-first: resolve the failing logs, defer to a user's own skill if they have one, otherwise load the bundled default.

## 1. Resolve inputs (Fallback Chain)

Resolve the **failing logs**, walking the chain until something is found and noting the source:

- Logs **attached by Conductor** →
- `mcp__conductor__GetTerminalOutput` (read what the user is looking at) →
- **GitHub:** `gh pr checks` for the branch's PR, `gh run list --branch <branch>`, then `gh run view <id> --log-failed` for the failing run →
- **Reproduce locally:** run the project's own CI / test / build command (the most targeted one) and capture its output.

Degrade gracefully: no PR / `gh` not installed or unauthenticated → skip the GitHub rung with a note and fall through to local reproduction. Never error out for a missing rung.

## 2. Discovery-first dispatch

Scan the skills present in this session's context for one whose **purpose is fixing failing CI / build / test errors**, excluding conductor-kit's own skills. If a clear capability match exists, invoke it with the resolved logs and **stop** — the user's skill takes precedence. If a discovered skill turns out not to fit, fall through to step 3 rather than failing.

## 3. Fallback — load the playbook

Only if no user skill applies, `Read` `references/playbook.md` (relative to this skill) and follow it.

## 4. Resolve outputs

Report the root cause, the files changed, and the passing command output. If something remains red and out of scope, say so explicitly.
