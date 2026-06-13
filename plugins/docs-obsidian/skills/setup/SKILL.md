---
description: Use when setting up the Obsidian docs provider for a project — bootstraps the vault-global folders, ensures the project's Backing Store folder exists, and offers the optional Obsidian MCP Add-on with Local REST API port detection. Invoked by docs-hub:setup when the user picks the obsidian provider, or directly via /docs-obsidian:setup.
---

# /docs-obsidian:setup

Driver setup for the **obsidian** docs provider. This skill owns only the driver side: the vault's global folders, the project's Backing Store folder inside the vault, and the optional MCP add-on. Everything provider-uniform belongs to `docs-hub:setup` and must NOT be duplicated here: the `## docs configuration` block, the `.docs/` directory with its self-ignoring `.gitignore`, the `.docs/vault` symlink, and the seven-folder project scaffolding.

Idempotent — safe to re-run; existing files and folders are always skipped, never overwritten.

**Path quoting is mandatory in every shell command.** Obsidian vault paths routinely contain spaces (iCloud vaults live under `.../iCloud~md~obsidian/Documents/<Vault Name>/...`). Always double-quote the vault path; keep each command a simple single command (no loops, no subshells, no heredocs, no multi-line scripts).

## Step 1 — Vault root

Determine the absolute path of the Obsidian vault root:

- When invoked by `docs-hub:setup`, it may pass a candidate path — confirm it with the user instead of re-asking from scratch.
- When run directly, ask the user for the vault root path.

Then verify it: `test -d "<vault root>"`. If the directory does not exist, ask whether to create it (`mkdir -p "<vault root>"` — a vault is just a folder; the user opens it in Obsidian afterwards) or to correct the path.

## Step 2 — Scaffold vault-global folders

Create the vault-global folders (one `mkdir -p` with all five quoted paths is fine as a single command):

```bash
mkdir -p "<vault root>/Daily" "<vault root>/References" "<vault root>/Roadmap" "<vault root>/Scratch" "<vault root>/Projects"
```

Then seed each folder's `_index.md` from this plugin's templates, one `cp -n` per folder (`-n` never overwrites, which keeps the step idempotent):

```bash
cp -n "${CLAUDE_PLUGIN_ROOT}/templates/vault/Daily/_index.md" "<vault root>/Daily/_index.md"
```

Repeat for `References`, `Roadmap`, `Scratch`, and `Projects`. Report which `_index.md` files were created and which already existed and were skipped.

## Step 3 — Ensure the project's Backing Store folder

```bash
mkdir -p "<vault root>/Projects/<project>"
```

This folder is the project's **Backing Store** — the `store` value in the `## docs configuration` block points here, and every checkout's `.docs/vault` symlinks to it. Do NOT create the seven project folders (Features, Brainstorms, Specs, Plans, Contexts, ADRs, Notes) — that scaffolding is `docs-hub:setup`'s job and it runs against the store after this skill returns.

If this skill was run **directly** (not delegated from docs-hub), finish by telling the user to run `docs-hub:setup` next — it writes the config block, scaffolds the project structure, and creates the `.docs/vault` symlink. Without it the provider has no Docs Root.

## Step 4 — Offer the Obsidian MCP Add-on (optional)

Explain before offering: the MCP is an **optional enhancement layer** (vault-wide search, backlinks). It is never the read/write path — all reads and writes go through the `.docs/vault` symlink with plain file tools (ADR 0001). The provider is **fully functional without it**, so declining or failing this step still ends the setup successfully.

If the user declines, finish here and report success.

### 4a — Detect Local REST API listeners

The Obsidian **Local REST API** community plugin binds one port per vault. Defaults are `27124` (HTTPS, on by default) and `27123` (HTTP, optional); additional vaults typically sit on nearby or custom ports. Scan:

```bash
lsof -nP -iTCP -sTCP:LISTEN | grep 2712
```

### 4b — Probe candidates

For each candidate port found, probe it with a single `curl` (one command per port):

```bash
curl -sk --max-time 2 "https://127.0.0.1:<port>/"
```

(use plain `curl -s --max-time 2 "http://127.0.0.1:<port>/"` for HTTP candidates). A Local REST API instance answers with JSON containing `"service": "Obsidian Local REST API"`; anything else is not a candidate.

- **Exactly one confirmed candidate** → use that port.
- **Several confirmed candidates** → the root endpoint does not identify which vault it serves, so never guess: ask the user which port belongs to THIS vault (visible in the Local REST API settings tab of the Obsidian window that has this vault open).
- **No listeners at all** → print the install pointer — Local REST API community plugin, https://coddingtonbear.github.io/obsidian-local-rest-api/ — note that the MCP add-on can be added later by re-running this skill, and **finish successfully**. This is not a failure.

### 4c — Register at personal scope

1. Ask the user for the API key (shown in the Local REST API plugin settings).
2. Check `claude mcp list` first — if an `obsidian` server is already registered for another project on this machine, reuse its command and env shape, swapping only the port (and key if it differs).
3. Register with `claude mcp add` at **personal scope** — the default (`local`) scope, which stores a per-project entry in `~/.claude.json` under the current `CLAUDE_CONFIG_DIR` (on dual-subscription machines that is the session's subscription). Never use `--scope project`: it writes a committed `.mcp.json` and reveals local tooling. Example with the `mcp-obsidian` server:

```bash
claude mcp add obsidian --env OBSIDIAN_API_KEY=<key> --env OBSIDIAN_HOST=127.0.0.1 --env OBSIDIAN_PORT=<port> -- uvx mcp-obsidian
```

4. Verify the entry appears in `claude mcp list` and report that the MCP becomes available in fresh sessions.

## Explicit non-goals (dead by design)

Do not add any of the following — they were retired by ADR 0001 (identity comes from the `.docs/vault` symlink, which pins the exact vault path):

- **No vault guard** — no "active vault" check, no probing which vault Obsidian currently has open.
- **No `vault.name` metadata** — neither in the docs configuration nor anywhere else; the config block is provider-uniform (`project`, `provider`, `store`).
- **No "same port + API key across vaults" advice** — per-vault ports are correct and expected; the MCP registration is per-project, so each project points at its own vault's port.

## Report

Summarize: vault root confirmed/created, global folders created vs skipped, the Backing Store path (`<vault root>/Projects/<project>`), and the MCP outcome (registered on port N / declined / not installed with the install pointer printed). If run directly, repeat the pointer to `docs-hub:setup`.
