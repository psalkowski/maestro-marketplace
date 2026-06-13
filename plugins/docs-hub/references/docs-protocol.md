# Docs protocol — consumer doctrine

How any plugin or skill reads and writes project docs. Consumer skills embed or reference this; it is the whole contract — no provider internals leak past it.

## Resolve the config

Read the fenced JSON under `## docs configuration` in `CLAUDE.local.md`: `{ "project", "provider", "store" }`. If the block is absent, or `.docs/vault` is missing or a dangling symlink (`test -d ".docs/vault"` fails through the link), **stop** and tell the user to run `/docs-hub:setup` (or `conductor-kit:setup` for an unseeded worktree). Never write into an unlinked `.docs/` — content written there dies with the checkout.

## Operate on the Docs Root

All reads AND writes go through `.docs/vault/` with plain file tools — `Read`, `Write`, `Edit`, `Glob`. No provider-specific tools on the read/write path, no MCP required, no size workarounds. The path is identical in every checkout regardless of provider.

## ADR numbering

Number a new ADR by `Glob` over `.docs/vault/ADRs/` for `[0-9]*.md`, take the highest `NNNN`, increment. Filenames are `NNNN-<slug>.md` (4-digit, no `ADR-` prefix).

## Respect each folder's `_index.md`

Before creating a note in any folder, read that folder's `_index.md` and copy its frontmatter template — never invent frontmatter. If the folder keeps an index list, add the new note's entry.

## Remote providers — the one write exception

For remote providers (Notion, GDrive — future), the Docs Root is a **read-only synced mirror**. Reads stay identical; writes go through the driver plugin's API, followed by a re-sync of the mirror. Never edit mirror files directly.

## Worktree check — config-writing skills only

Any skill writing **repo-level config** (`CLAUDE.local.md`, `.conductor/*`, MCP registration) must compare `git rev-parse --git-dir` with `git rev-parse --git-common-dir`. When they differ (linked worktree), ask the user: configure the **main checkout** (derive its path from the common dir) or **this worktree**. Docs *content* writes never need this — the store is shared through the symlink.
