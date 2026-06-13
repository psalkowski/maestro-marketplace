---
name: setup
description: Use when onboarding a repository to provider-agnostic project docs, when a consumer skill reports a missing `## docs configuration` block or a missing/dangling `.docs/vault` Docs Root, or when migrating a legacy `## spec configuration` block — writes the unified config into CLAUDE.local.md, scaffolds the seven-folder docs structure into the Backing Store, and links the Docs Root. Triggers on /docs-hub:setup.
---

# /docs-hub:setup

The single front door for project docs. It establishes the three invariants every consumer plugin relies on:

1. A **`## docs configuration`** fenced JSON block in `CLAUDE.local.md`: `{ "project", "provider", "store" }` — `store` always an absolute local path, no provider metadata.
2. A **Backing Store** outside the checkout holding the seven-folder docs structure.
3. A **Docs Root** at `.docs/vault` — a self-ignoring symlink to the store, never a content copy.

Idempotent — safe to re-run: existing files are skipped, the config block is replaced atomically, nothing else in `CLAUDE.local.md` is touched. **Quote every path in every shell command** — stores routinely contain spaces (iCloud vault paths). Use dedicated tools (`Read`/`Write`/`Edit`/`Glob`) over shell wherever possible; any shell line must be a simple single command (no loops, no `$(...)`, no heredocs).

Templates live under `${CLAUDE_PLUGIN_ROOT}/templates/project/`. Use TodoWrite to track the steps.

## Step 0 — Worktree check

This skill writes repo-level config (`CLAUDE.local.md`, `.docs/`), so it must apply the shared worktree rule (documented in `${CLAUDE_PLUGIN_ROOT}/references/docs-protocol.md`):

1. Run `git rev-parse --git-dir` and `git rev-parse --git-common-dir`.
2. If the outputs are **equal**, this is the main checkout — continue here.
3. If they **differ**, this is a linked worktree. Derive the main checkout path (the parent directory of the common git dir) and ask the user: **configure the main checkout** (recommended — worktrees are then seeded by `conductor-kit:setup`'s script) **or this worktree**? Perform every following step against the chosen root.

Docs *content* writes never need this check — the store is shared through the symlink. Only config-writing skills do.

## Step 1 — Legacy migration (`## spec configuration`)

Read `CLAUDE.local.md` (if it exists) and look for a `## spec configuration` heading with a fenced JSON block (`project`, `vault.name`, `vault.root`, `vault.subpath`, optional `designSkill`). If found, run the Legacy Migration instead of asking the provider question:

1. Build the new config: `project` = old `project`; `provider` = `"obsidian"`; `store` = `vault.root` joined with `vault.subpath` (absolute path).
2. Show the user the old block and the converted block; confirm before writing.
3. **Never move or rewrite vault content** — the store already exists and is the truth; Step 4 will only fill genuinely missing files.
4. Remove the `## spec configuration` heading and its fenced block. If the old block carried `designSkill`, tell the user it now belongs to the spec plugin's own slim config (`/spec:setup` manages it) and preserve the value by writing a minimal `## spec configuration` block containing only `{ "designSkill": "<value>" }`.
5. Continue at Step 3 (write the new block), then Steps 4–7 as normal.

No legacy block → continue to Step 2.

## Step 2 — Provider and store (fresh setup)

Propose defaults; let the user accept or override:

- **`project`** — derive from the git repo name: run `git remote get-url origin` and take the basename without `.git`; fall back to the repo directory name. Show it; let the user correct it.
- **`provider`** — ask: **`filesystem`** (default — no extra tooling, store under `~/.docs/`) or **`obsidian`** (docs live in an Obsidian vault).
- **`store`** — always stored as an **absolute** path (expand `~`):
  - `filesystem` → propose `~/.docs/<project>/`.
  - `obsidian` → the **docs-obsidian** driver plugin is required. Check that the `/docs-obsidian:setup` skill is available; if not, **stop** and tell the user to `/plugin install docs-obsidian` first. Then delegate the driver part — vault location, vault-global scaffolding, optional MCP add-on — by invoking `/docs-obsidian:setup`; it yields the vault root, and `store` = `<vault-root>/Projects/<project>/`. Project scaffolding (Step 4) stays this skill's job.

## Step 3 — Write the config block

Show the full JSON and get explicit confirmation:

```json
{
  "project": "<repo-name>",
  "provider": "filesystem",
  "store": "/Users/you/.docs/<repo-name>"
}
```

On approval, using `Read`/`Write`/`Edit` on `CLAUDE.local.md` in the repo root (create the file if missing):

- Add a `## docs configuration` heading with the JSON in a fenced ```json block.
- If the heading already exists, **replace only that block** — atomically, never touching the rest of the file.

## Step 4 — Scaffold the store (idempotent)

Materialize the seven-folder structure in the store. **Skip every file that already exists; never overwrite.**

1. `mkdir -p "<store>"`.
2. For each of the seven folders in `${CLAUDE_PLUGIN_ROOT}/templates/project/` (`Features/`, `Brainstorms/`, `Specs/`, `Plans/`, `Contexts/`, `ADRs/`, `Notes/`): `mkdir -p` the folder under the store, then copy its `_index.md` **only if the destination doesn't already exist** (check with `Glob` first; one plain `cp` per missing file, both paths quoted).
3. **Root `_index.md`** — at `<store>/_index.md`, if absent, write it from `templates/project/_index.md` substituting:
   - `{{PROJECT_NAME}}` → a human-readable name (default the project name; let the user supply a nicer one)
   - `{{REPO}}` → `config.project`
   - `{{DESCRIPTION}}` → a one-line description (ask, or leave a short placeholder)
4. If any destination files **already existed**, list them as skipped and offer to show a template-vs-existing diff for hand-merging — do **not** auto-modify them.

## Step 5 — Create the Docs Root (`.docs/vault`)

In the repo root, first inspect what's already there with `ls -la ".docs"` (if `.docs/` exists) and `readlink ".docs/vault"`:

- **Symlink already resolving to `<store>`** → done; report it as already linked.
- **Symlink pointing elsewhere or dangling** (target missing or different) → the store moved or the link is stale. Do **not** silently recreate or re-point: show the current target vs the configured store and ask the user before running `rm ".docs/vault"` and relinking.
- **Existing non-symlink `.docs/vault`** (real directory or file) → **abort this step and ask**: something else owns that path; never overwrite it. Offer to merge its contents into the store manually before re-running.
- **Nothing there** → create it:
  1. `mkdir -p ".docs"`
  2. Write `.docs/.gitignore` containing exactly `*` (the self-ignoring directory — everything inside, including the `.gitignore` itself, stays invisible to git with no project-level ignore edits). Skip if it already exists with that content.
  3. `ln -s "<store>" ".docs/vault"`

Verify: `readlink ".docs/vault"` shows the store, and listing `.docs/vault/` through the link shows the seven folders.

## Step 6 — Keep `CLAUDE.local.md` out of git

Unlike `.docs/`, this file can't self-ignore:

1. `git check-ignore -q CLAUDE.local.md` — if it exits 0, some mechanism already ignores it; report which is likely (global gitignore, repo `.gitignore`).
2. If NOT ignored, append a `CLAUDE.local.md` line to `.git/info/exclude` (the per-repo, never-committed ignore file) using `Read` + `Edit`/`Write`, then re-run `git check-ignore -q CLAUDE.local.md` to confirm.

Never add `.docs/` to any ignore file — it is self-ignoring by design.

## Step 7 — Report

Summarize:

- The config block written (and the migration performed, if any).
- Store paths created vs skipped.
- The Docs Root symlink target (`readlink ".docs/vault"`).
- Confirmation that `git status --porcelain` shows nothing new from this setup.
- For the filesystem provider: the store lives outside every repo at `<store>` — **backups are the user's concern**.

The project is then ready for consumer skills (`/spec:plan`, `/graphify-kit:sync-docs`) following `${CLAUDE_PLUGIN_ROOT}/references/docs-protocol.md`.
