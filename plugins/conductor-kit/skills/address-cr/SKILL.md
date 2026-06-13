---
description: Use when addressing, resolving, or acting on code-review feedback for the current branch — the additive companion to Conductor's actions (Conductor has no native "address review" button). Resolves review comments from args/attachments, the GitHub PR's reviews, or the ephemeral review store, normalizes them into a uniform block, then prefers a user's own review-addressing skill if present, otherwise follows the bundled edit loop. Triggers on /conductor-kit:address-cr or any "address / resolve / fix the PR review comments" request.
---

# /conductor-kit:address-cr

Address the code-review feedback on the current branch. Thin and discovery-first: resolve and normalize the comments, defer to a user's own review-addressing skill if they have one, otherwise load the bundled edit loop.

## 1. Resolve inputs (Fallback Chain)

Resolve the **comments to address**, walking the chain until something is found and noting the source:

- **Arguments / Conductor-attached snippets** — comment text passed in or attached →
- **GitHub PR reviews:** `gh pr view --json reviews` for the branch's PR, then `gh api` for the per-comment review threads (file, line, body, comment/thread ids, URLs) →
- **Ephemeral Review Store:** `.context/reviews/<branch>.md` (what code-review wrote in terminal mode) — derive `<branch>` and parse the block shape per `../../references/review-comment-format.md` (`<branch>` = current branch with slashes replaced by `-`), so this reads the exact path and structure code-review wrote.

Degrade gracefully: no PR / `gh` not installed or unauthenticated → skip the GitHub rung; no store file → that rung is empty. If no comments are found anywhere, say so and stop.

## 2. Normalize

Normalize whatever was found into a uniform structured comment block — `File:` / `Lines:` / body for every comment, plus `Comment ID:` / `Thread ID:` / `Remote URL:` when the comment came from GitHub — following the shared contract in `../../references/review-comment-format.md`. This is the same shape the Ephemeral Review Store uses, so a discovered user skill can consume it.

## 3. Discovery-first dispatch

Scan the skills present in this session's context for one whose **purpose is addressing/resolving review comments**, excluding conductor-kit's own skills. If a clear capability match exists, hand it the normalized block and let it drive, then **stop** — the user's skill takes precedence. If a discovered skill turns out not to fit, fall through to step 4 rather than failing.

## 4. Fallback — load the playbook

Only if no user skill applies, `Read` `references/playbook.md` (relative to this skill) and follow the disciplined edit loop.
