---
description: Configure the spec workflow for this project — verify the docs configuration exists and manage the spec-specific config (designSkill) in CLAUDE.local.md. Idempotent.
argument-hint: "[design-skill] (optional; discovered if omitted)"
---

You are running the **`spec` setup** for the current repository. Storage setup is **not** this command's job — `docs-hub` owns the docs configuration and the Docs Root. This command only verifies that prerequisite and manages the spec-specific config. Be smart: propose defaults, confirm before writing, never overwrite anything you don't own.

Work through these steps in order. Use TodoWrite to track them.

## 1. Verify the docs configuration (prerequisite, owned by docs-hub)

Check `CLAUDE.local.md` for a fenced ```json block under `## docs configuration` (`{ "project", "provider", "store" }`).

- **Missing** → tell the user to run `/docs-hub:setup` first; if the `docs-hub` plugin is installed, offer to invoke it now. Do **not** duplicate its work — no config-block writing, no scaffolding, no symlinking here.
- **Present** → confirm `.docs/vault` resolves to a directory (`test -d` through the symlink). If it doesn't, point at `/docs-hub:setup` (or conductor-kit worktree seeding in a Conductor workspace) and stop.

## 2. Gather the spec config

- **`designSkill`** — if `$1` (argument) was given, use it; otherwise discover it: scan the project's `.claude/skills/` and the user-level `~/.claude/skills/` for a skill whose name/description is about designing UI/pages/mockups. If you find a likely one, propose it; if not, leave it **absent** (the project simply has no design skill — that's fine). Confirm with the user.

## 3. Preflight (warn, don't block)

Check and report — these are warnings, not hard stops:

- The sub-skills `spec:plan`/`execute` rely on `grill-with-docs`. Note if it looks absent from the available skills.
- Note if the **`playwright`** MCP (used by typical design skills) is not connected — only relevant when a `designSkill` is configured.

## 4. Confirm and write the config

If a `designSkill` was chosen, show the **full JSON** you assembled:

```json
{
  "designSkill": "<skill-name>"
}
```

Ask for explicit permission to store it. On approval:

- Add (or update) a `## spec configuration` heading in `CLAUDE.local.md` with the JSON in a fenced ```json block. If the heading already exists, replace only that block — don't touch the rest of the file.
- **Keep `CLAUDE.local.md` out of git without editing the committed `.gitignore`:** run `git check-ignore -q CLAUDE.local.md`; if it is NOT already ignored, append `CLAUDE.local.md` to `.git/info/exclude` (the per-repo, never-committed ignore file). Report which mechanism already covered it, or that you added it to `info/exclude`.

If no `designSkill` was chosen, skip the block entirely — `spec:plan` works without it (and says so when it skips the design phase). If a stale `## spec configuration` block with legacy keys (`project` plus the old storage keys) exists, replace it with the minimal block (or remove it when there's no `designSkill`) — storage now lives in `## docs configuration`.

## 5. Report

Summarize: docs-configuration status, the spec config written (or that none was needed), and any preflight warnings. Then the project is ready for `/spec:plan`.
