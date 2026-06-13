---
description: Use when reviewing the current branch or workspace changes — Conductor's Code Review action and its terminal-mode equivalent. Resolves the diff, prefers a user's own code-review skill if present, otherwise follows the bundled reviewer playbook, then reports findings as inline diff comments or persists them to the ephemeral review store. Triggers on /conductor-kit:code-review or any "review my changes / this diff" request.
---

# /conductor-kit:code-review

Review the workspace's changes and report concrete findings. Thin and discovery-first: resolve the diff, defer to a user's own skill if they have one, otherwise load the bundled reviewer default.

## 1. Resolve inputs (Fallback Chain)

Resolve the **diff**, noting where it came from:

- `mcp__conductor__GetWorkspaceDiff` when the Conductor MCP is available (request the stat first to size it, then the full diff) →
- otherwise `git merge-base <remote>/<parent> HEAD` to find the base, then `git diff <merge-base> HEAD`.

If the tree is clean / there is no diff, report "nothing to review" and stop — never invent findings.

## 2. Discovery-first dispatch

Scan the skills present in this session's context for one whose **purpose is reviewing code**, excluding conductor-kit's own skills. If a clear capability match exists, invoke it with the resolved diff and **stop** — the user's skill takes precedence. If a discovered skill turns out not to fit, fall through to step 3 rather than failing.

## 3. Fallback — load the playbook

Only if no user skill applies, `Read` `references/playbook.md` (relative to this skill) and follow its reviewer guidelines.

## 4. Resolve outputs (Fallback Chain)

- **Conductor MCP present:** post one finding per unique issue via `mcp__conductor__DiffComment` (`{"comments":[{"file","lineNumber","body"}]}`, plain-text bodies).
- **Otherwise (terminal mode):** persist findings to the **Ephemeral Review Store** `.context/reviews/<branch>.md` in the shared block format — both the filename (`<branch>` = current branch with slashes replaced by `-`) and the block shape are defined in `../../references/review-comment-format.md`; follow it exactly so address-cr reads the same path and structure back. Optionally also post to the GitHub PR via `gh` if one exists and the user wants.
