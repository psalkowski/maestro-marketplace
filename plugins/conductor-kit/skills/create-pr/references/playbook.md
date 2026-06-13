# create-pr — playbook

The default behavior, loaded only when Discovery-first Dispatch found no user PR-creation skill.
Grounded in Conductor's extracted Create PR default (`O3t`) plus the named intrinsic additions.

Work through these steps in order. Inputs (workspace diff, PR target) were already resolved by the
skill body; reuse them rather than re-fetching.

## Steps

1. **Review uncommitted work.** Run `git diff` (and `git diff --staged`) to see what is not yet
   committed, so the PR captures it.
2. **Commit.** Commit the outstanding work. Honor the user's commit-message preferences (any prefix,
   style, or co-author rule from their config); write a concise subject describing the change.
3. **Push.** Push the branch. When it has no upstream yet, use `git push --set-upstream origin HEAD`.
4. **Review the PR diff.** Look over the full diff that will land — the diff resolved in the skill
   body (`mcp__conductor__GetWorkspaceDiff` or `git diff <remote>/<target>...HEAD`). Base the
   description on **all** changes in the workspace diff, not just the ones made in this session.
5. **Create the PR:** `gh pr create --base <target>` with `--title` and `--body`. Use `--draft` only
   if the user asked for a draft.
   - **Title:** one line, under 80 characters, imperative and specific ("Add worktree seeding to
     conductor setup", not "Updates").
   - **Description:** at most 5 sentences describing all workspace-diff changes. Plain prose for a
     human skimming their PR list — no boilerplate section headers, no checklists, no emoji, no
     restating the diff file-by-file.

## Intrinsic additions (good practice, beyond the bare default)

- **Watch checks.** After the PR is created, offer to watch its CI — a `Monitor` loop or
  `gh pr checks <number> --watch` — so the user learns of a red check without polling manually.
- **Close issues precisely.** Add a `Closing #NNN` / `Fixes #NNN` line only for issues this PR fully
  closes. Do not auto-close an issue the PR only partially addresses.

## Edge cases

- **PR already exists** for the branch: don't open a duplicate — surface the existing PR and offer to
  update its title/body.
- **`gh` not installed or not authenticated:** report that the PR could not be opened via `gh` and
  hand the user the branch + a ready title/body so they can open it in the UI.
