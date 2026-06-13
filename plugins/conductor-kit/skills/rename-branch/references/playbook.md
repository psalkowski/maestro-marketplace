# rename-branch — playbook

The default behavior, loaded only when Discovery-first Dispatch found no user branch-naming skill.
Grounded in Conductor's extracted Rename Branch default (`R3t`).

The work intent was already resolved by the skill body. Generate the name from it.

## Generate the name

- **Concise and concrete:** lowercase, hyphenated (kebab-case), concrete language. Avoid abstract
  nouns ("updates", "changes", "improvements"). Name the change, not the activity —
  `conductor-setup-seeding`, not `my-changes` or `updates-2026`. Keep it under 30 characters when
  possible.
- **Honor a configured branch prefix.** If the repo's existing branches show a prefix convention
  (`feature/`, `fix/` — check `git branch -a`) or the user has a configured prefix, apply it; don't
  invent slashes otherwise.
- **No ticket numbers** unless one is clearly attached to the work (then prefix it:
  `se-12345-conductor-seeding`).
- **`<none>` escape hatch:** if the intent is genuinely contentless (nothing to name on), return
  `<none>` rather than a placeholder name — do not reuse a placeholder.

## Apply

Apply the rename with `git branch -m <new-name>` **only when the user actually asked to rename** —
not when they merely asked for a suggestion. If the old name was already pushed, push the new one and
fix the upstream (`git push --set-upstream origin <new-name>`), and tell the user the old remote
branch still exists for them to delete.
