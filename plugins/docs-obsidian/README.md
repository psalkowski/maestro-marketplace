# docs-obsidian (v0.1.1)

Obsidian **driver plugin** for the docs-hub provider contract. It integrates an Obsidian vault as the project's docs provider: bootstraps the vault-global folders, ensures the project's Backing Store folder (`<vault>/Projects/<project>/`) exists, and optionally registers the Obsidian MCP add-on.

## Relationship to docs-hub

This plugin **requires [`docs-hub`](../docs-hub/)** and only handles the Obsidian-specific half of setup. The provider-uniform parts — the `## docs configuration` block in `CLAUDE.local.md`, the self-ignoring `.docs/` directory, the `.docs/vault` symlink, and the seven-folder project scaffolding — are owned by `docs-hub:setup`, which delegates to `docs-obsidian:setup` when the user picks the `obsidian` provider. Running this skill directly works too; it ends by pointing you at `docs-hub:setup` to finish the wiring.

Once set up, consumer plugins (`spec`, `graphify-kit`, ...) never talk to Obsidian: they read and write through the `.docs/vault` symlink with plain file tools, and Obsidian picks up external changes natively (ADR 0001). There is no vault guard and no `vault.name` metadata — the symlink pins the exact vault path, so identity comes from the filesystem.

## What setup does

`/docs-obsidian:setup`:

1. Asks/confirms the vault root path (creating it if the user wants — a vault is just a folder).
2. Scaffolds the vault-global folders (`Daily/`, `References/`, `Roadmap/`, `Scratch/`, `Projects/`) with their `_index.md` files from `templates/vault/`. Idempotent: existing files are skipped, never overwritten.
3. Ensures `Projects/<project>/` exists — the Backing Store the `store` config value and the `.docs/vault` symlink point at.
4. **Offers** the MCP add-on (below).

## Obsidian MCP add-on (optional)

The MCP is an enhancement layer for vault-wide search and backlinks — never the read/write path. Setup scans listening ports around the Local REST API defaults (27124 HTTPS / 27123 HTTP; one port per vault), probes the candidates, asks which port serves this vault when several answer, and registers the server at personal scope via `claude mcp add` (the entry lands under the current `CLAUDE_CONFIG_DIR`, per project — never in a committed `.mcp.json`).

If nothing is listening, setup prints the [Local REST API](https://coddingtonbear.github.io/obsidian-local-rest-api/) install pointer and finishes successfully — the provider is fully functional through the symlink without MCP, and you can re-run the skill later to add it.

## iCloud vault paths contain spaces

iCloud-synced vaults live under `.../iCloud~md~obsidian/Documents/<Vault Name>/...` — paths with spaces. Every shell command this plugin generates double-quotes the vault path; do the same in anything you script around it.
