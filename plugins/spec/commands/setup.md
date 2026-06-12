---
description: Configure the spec workflow for this project — write the config block into CLAUDE.local.md and scaffold the Obsidian vault. Idempotent; skips anything that already exists.
argument-hint: "[vault-name] (optional; you'll be prompted if omitted)"
---

You are running the **one-time `spec` setup** for the current repository. Be smart: derive what you can, propose sensible defaults, confirm before writing anything, and **never overwrite existing files** — only create what's missing. The plugin's templates live under `${CLAUDE_PLUGIN_ROOT}/templates/`.

Work through these steps in order. Use TodoWrite to track them.

## 1. Gather the config (propose, don't interrogate)

Assemble this config, proposing defaults the user can accept or override:

- **`project`** — derive from the git repo name: `basename` of the `origin` remote URL (strip `.git`), falling back to the repo directory name. Show it; let the user correct it.
- **`vault.root`** — propose **`~/Documents/Vault`**. Expand `~` to the absolute home path when you store it.
- **`vault.name`** — if `$1` (argument) was given, use it; otherwise ask. This is the Obsidian vault name and the guard's identity.
- **`vault.subpath`** — propose **`Projects/<vault.name>`**; let the user override. Required (never empty).
- **`designSkill`** — discover it: scan the project's `.claude/skills/` and the user-level `~/.claude/skills/` for a skill whose name/description is about designing UI/pages/mockups. If you find a likely one, propose it; if not, leave it **absent** (the project simply has no design skill — that's fine). Confirm with the user.

## 2. Preflight (warn, don't block)

Check and report — these are warnings, not hard stops:

- The sub-skills `spec:plan`/`execute` rely on `grill-with-docs`. Note if it looks absent from the available skills.
- **Actively probe the `obsidian` MCP** — it's load-bearing for the whole workflow (the skills read/write the vault and run the guard through it). Make a lightweight call (e.g. `mcp__obsidian__vault_list` at the vault root, or `mcp__obsidian__active_file_get_path`) to confirm it's connected and reachable. Report the result: connected + which vault is currently open, or **clearly warn** that until the `obsidian` MCP is connected, `spec:plan`/`execute` can't write to the vault. If a call succeeds, also note whether the open vault matches the `vault.name` you just configured (a heads-up, since you'll need that vault open to use the skills).
- Note if the **`playwright`** MCP (used by typical design skills) is not connected.
- Print the one-time reminder: **"For the vault guard to work across your vaults, give each vault's Local REST API the same port + API key, so the single `obsidian` MCP config reaches whichever vault you have open."**

## 3. Confirm and write the config

Show the **full JSON** you assembled, e.g.:

```json
{
  "project": "<repo-name>",
  "vault": {
    "name": "<VaultName>",
    "root": "/Users/you/Documents/Vault",
    "subpath": "Projects/<VaultName>"
  },
  "designSkill": "<skill-or-omit>"
}
```

Ask for explicit permission to store it. On approval:

- Ensure `CLAUDE.local.md` exists in the repo root (create it if missing).
- Add (or update) a `## spec configuration` heading with the JSON in a fenced ```json block. If the heading already exists, replace only that block — don't touch the rest of the file.
- **Keep it out of git without editing the committed `.gitignore`:** run `git check-ignore -q CLAUDE.local.md`; if it is NOT already ignored, append `CLAUDE.local.md` to `.git/info/exclude` (the per-repo, never-committed ignore file). Report which mechanism already covered it, or that you added it to `info/exclude`.

## 4. Scaffold the vault (idempotent, filesystem-based)

Materialize the vault at `vault.root` using the filesystem (this does not depend on which vault Obsidian currently has open). **Skip every file that already exists; never overwrite.**

1. `mkdir -p "<vault.root>"`.
2. **Vault-global skeleton** — for each directory under `${CLAUDE_PLUGIN_ROOT}/templates/vault/` (`Daily/`, `References/`, `Roadmap/`, `Scratch/`, `Projects/`), create the dir under `vault.root` and copy its `_index.md` **only if the destination doesn't already exist**.
3. **Project subtree** — create `<vault.root>/<vault.subpath>/` and copy the contents of `${CLAUDE_PLUGIN_ROOT}/templates/project/` into it (the seven sub-folders + their `_index.md`), again **skipping existing files**.
4. **Project `_index.md`** — at `<vault.root>/<vault.subpath>/_index.md`, if it doesn't already exist, write it from `templates/project/_index.md` substituting:
   - `{{PROJECT_NAME}}` → a human-readable name (default the vault name; let the user supply a nicer one)
   - `{{REPO}}` → `config.project`
   - `{{VAULT_NAME}}` → `config.vault.name` ← this is the **guard identity marker**; it must be present
   - `{{DESCRIPTION}}` → a one-line description (ask, or leave a short placeholder)
5. If any destination files **already existed**, list them as skipped, and offer to show a diff of template-vs-existing so the user can hand-merge — do **not** auto-modify them.

## 5. Report

Summarize: the config written (and how it's git-ignored), the vault paths created vs skipped, any preflight warnings, and the reminder to **open `<vault.root>` as a vault in Obsidian** (and set its REST API port/key to match the others). Then the project is ready for `/spec:plan`.
