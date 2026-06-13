# resolve-conflicts — playbook

The default behavior, loaded only when Discovery-first Dispatch found no user conflict-resolution
skill. Grounded in Conductor's extracted Resolve Conflicts default (`D3t`), which is forge-aware, plus
the named intrinsic addition.

The skill body resolved whether this is a rebase or a merge and the target branch. The forge decides
the finish step:

- **GitHub, rebase:** rebase the branch onto the remote target, resolve conflicts, stage the resolved
  files, run `git rebase --continue`, then push with `--force-with-lease`.
- **GitHub, merge:** merge the remote target into the branch, resolve conflicts, then commit and push.
- **Local-git forge:** the same resolution steps without the push.

## Orient before editing

1. `git status` confirms rebase vs merge and lists conflicted files.
2. Establish what each side **is** before editing. During a **rebase**, `HEAD`/"ours" is the branch
   being rebased **onto** (e.g. the target) and "theirs" is your branch's commit being replayed — the
   labels are inverted versus a merge; getting this wrong silently destroys work.
3. For each conflicted file, understand both changes' intent: `git log --oneline -3 <base>..HEAD --
   <file>` and the same for the other side, plus `git diff` of each side against the merge base when
   the hunks aren't self-explanatory.

## Resolve, file by file

1. Read the whole conflicted region with its surroundings — not just the lines between the markers;
   correct resolutions often require edits outside the markers (an import both sides need, a renamed
   symbol one side introduced).
2. **Preserve both sides' intent.** Write the resolution that makes both changes true at once: if one
   side renamed a function and the other added a caller, the resolution is the new caller using the
   new name. Never resolve by blindly discarding one side; "take ours" / "take theirs" wholesale is
   only correct when one side is provably obsolete, and you must be able to say why.
3. **Ask when intents genuinely conflict.** If both sides made contradictory product decisions that
   cannot coexist, stop and ask the user which intent wins — that is a human decision, not a
   mechanical one.
4. Remove every conflict marker, then verify the file is syntactically valid (the file's targeted test
   or a type-check/compile of that module when one exists).
5. `git add <file>` once resolved.

## Finish

Continue per the forge (`git rebase --continue`, then push `--force-with-lease`; or commit + push for
a merge; or no push on a local-git forge) and repeat for further stops. When done, run the targeted
tests covering the conflicted areas.
