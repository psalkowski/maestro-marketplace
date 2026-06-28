# docs-hub (v0.1.0)

Provider-agnostic project docs for Claude Code. Every repo gets a **Docs Root** at `.docs/vault/` — a uniform local access point where project documentation (Features, Brainstorms, Specs, Plans, Contexts, ADRs, Notes) is read AND written with plain file tools, regardless of which provider serves it. Consumer plugins (`spec`) never learn provider internals; the whole contract is `references/docs-protocol.md`.

## The model

- **Docs Provider** — the backing store that owns the documentation: `filesystem` (default, built into this plugin — no driver needed), `obsidian` (via the `docs-obsidian` driver plugin), later `notion` / `gdrive`. Exactly one per repo.
- **Backing Store** — the durable location that outlives every checkout: `~/.docs/<project>/` for the filesystem provider (configurable), `<vault>/Projects/<project>/` for Obsidian. Real data never lives inside a checkout.
- **Docs Root** — `.docs/vault` in every checkout is always a **symlink** to the store (local providers) or a read-only synced mirror (remote providers, future). Never a content copy — copies diverge across worktrees.
- **Self-ignoring directory** — `.docs/.gitignore` containing a single `*` keeps everything invisible to git without touching project-level ignore files; the root nests as `.docs/vault/` so other tools claiming `.docs/` cannot collide.

## Config block

One uniform fenced JSON block under `## docs configuration` in `CLAUDE.local.md`, owned by this plugin:

```json
{
  "project": "<repo-name>",
  "provider": "filesystem",
  "store": "/Users/you/.docs/<repo-name>"
}
```

`store` is always an absolute **local** path — the Docs Root symlink target. No provider metadata lives here (no vault names, no guards); driver specifics (e.g. the Obsidian MCP registration) live in the driver's own artifacts.

## Setup

```
/plugin marketplace add psalkowski/maestro-marketplace
/plugin install docs-hub
```

Then, in each repo:

```
/docs-hub:setup
```

The setup skill is the single front door. It:

1. Applies the **worktree check** (config belongs on the main checkout; run from a worktree, it asks main-vs-here first).
2. **Migrates legacy `## spec configuration` blocks** (the pre-provider Obsidian-coupled format) to `## docs configuration` with `provider: obsidian` — vault content untouched.
3. Asks for the provider (`filesystem` default; `obsidian` requires the `docs-obsidian` plugin and delegates driver setup to `/docs-obsidian:setup`).
4. Writes the config block, scaffolds the seven-folder structure into the store from `templates/project/` (idempotent — existing files are never overwritten), creates `.docs/` + the self-ignoring `.gitignore` + the `vault` symlink, and ensures `CLAUDE.local.md` is git-ignored.

Re-running is safe; `git status` stays untouched by all of it.

## What's inside

| Component                     | Purpose                                                                                              |
| ----------------------------- | ---------------------------------------------------------------------------------------------------- |
| `/docs-hub:setup`             | Front door: worktree check, legacy migration, provider choice, config block, store scaffold, Docs Root |
| `references/docs-protocol.md` | The consumer doctrine: resolve config → file tools on `.docs/vault/` → ADR numbering by Glob → respect `_index.md` templates → remote-provider write exception |
| `templates/project/`          | The seven-folder docs skeleton (`_index.md` per folder + project root index) the setup scaffolds into the store |

## Notes

- **Backups are the user's concern.** The filesystem store at `~/.docs/<project>/` lives outside every repo and is never committed anywhere — include it in your machine backup (Time Machine, etc.).
- An unseeded worktree has no Docs Root; `conductor-kit:setup` wires per-workspace seeding for Conductor, otherwise re-run `/docs-hub:setup` in the worktree and pick "this worktree".
