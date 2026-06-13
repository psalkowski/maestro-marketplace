---
description: Use when the current branch needs a proper name — Conductor's Rename Branch action and its terminal-mode equivalent. Resolves the work intent, prefers a user's own branch-naming skill if present, otherwise follows the bundled playbook to generate a concise name and (when asked) apply it. Triggers on /conductor-kit:rename-branch or any "rename this branch / suggest a branch name" request.
---

# /conductor-kit:rename-branch

Generate a concise, descriptive branch name from what this workspace actually changes. Thin and discovery-first: resolve the intent, defer to a user's own skill if they have one, otherwise load the bundled default.

## 1. Resolve inputs

Resolve the **work intent**, cheapest evidence first — no external service needed:

- The user message / args, if they describe the work →
- otherwise the branch diff: commit subjects (`git log --oneline <default-branch>..HEAD`), then `git diff --stat <default-branch>..HEAD`, then the changed files' nature. Uncommitted-only work: `git diff --stat HEAD` plus session context.

## 2. Discovery-first dispatch

Scan the skills present in this session's context for one whose **purpose is naming/renaming branches**, excluding conductor-kit's own skills. If a clear capability match exists, invoke it with the resolved intent and **stop** — the user's skill takes precedence. If a discovered skill turns out not to fit, fall through to step 3 rather than failing.

## 3. Fallback — load the playbook

Only if no user skill applies, `Read` `references/playbook.md` (relative to this skill) and follow it.

## 4. Resolve outputs

Reply with the new name (or the suggested alternatives if the user asked for options rather than a rename). Apply with `git branch -m` only when the user actually asked to rename.
