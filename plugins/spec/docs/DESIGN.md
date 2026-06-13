# spec — design

The design record for the `spec` plugin. Captures what was decided and why, so the rationale survives.

## Goal

Take a set of project-specific Claude skills, agents, and instructions — built for one project — and turn them into a **portable, personal bundle** usable across many projects, without committing anything to the project repos. As of 0.3.0 the plugin is also **storage-agnostic**: it consumes project docs through the Docs Root contract owned by `docs-hub` and carries no provider logic of its own.

## Constraints (from the owner)

1. **Two tiers only.** Everything is either user-level (global `~/.claude/` + the installed plugin) or project-level **uncommitted** (`CLAUDE.local.md`). Nothing from the bundle is committed to a project repo.
2. **Generic, but dependency-aware.** The skills depend on `grill-with-docs`, `docs-hub` (storage), and optionally the `playwright` MCP (for design skills). These are prerequisites, not bundled.
3. **Design skill is project-owned.** Not every project has one; it's referenced by name in config and invoked dynamically, never hardcoded.
4. **Storage is someone else's problem.** Docs may live in a filesystem store, an Obsidian vault, or a remote provider — the spec skills must not know which.

## Decisions

| Area | Decision | Why |
|---|---|---|
| Vehicle | A private marketplace repo with the `spec` plugin | Standard Claude plugin format; installs user-level, so nothing touches the project repo |
| Config source | Fenced ```json blocks in uncommitted `CLAUDE.local.md` | Auto-loaded into context (skills read them for free); no sidecar file; honors the two-tier rule |
| Keeping config un-tracked | `.git/info/exclude` (per-repo, never committed) — fall back only if not already ignored | Avoids editing the committed `.gitignore` |
| Storage contract | The `## docs configuration` block (`project`, `provider`, `store`) + the Docs Root (`.docs/vault/`), both owned by `docs-hub` | Consumer plugins use plain file tools and stay provider-blind (ADR 0001/0002 in the project docs) |
| Spec-specific schema | A minimal `## spec configuration` block with only optional `designSkill` | Everything storage-related moved to the docs configuration |
| Naming | Plugin-namespaced: `spec:plan` / `spec:execute` | Groups them legibly; no collisions |
| Design skill | Not bundled; named in config; invoked by name or skipped (explicitly) | Different projects have different design skills; some have none |
| Doc access | Plain `Read`/`Write`/`Edit`/`Glob` on `.docs/vault/...` | One code path for every provider; no MCP size limits, no patch quirks |
| ADR numbering | Glob scan of `ADRs/` for the highest `NNNN` | No provider tooling needed for a directory listing |
| Setup | `/spec:setup` — verifies the docs configuration, manages `designSkill`; storage setup delegated to `/docs-hub:setup` | One owner per concern; idempotent; never overwrites |
| Distribution | Private GitHub repo (owner handles the git identity) | Portable across machines |

## Why the vault guard is gone (historical note)

Through 0.2.x this plugin was welded to Obsidian: it wrote via the Obsidian MCP tools, which talk to whichever vault is *currently open* and cannot switch. That forced an "active vault" pre-write guard (check a `vault:` frontmatter marker against config), a ~3000-line REST-truncation workaround, and a frontmatter-patch cheatsheet for the MCP's quirks.

ADR 0001 (Docs Root is the read+write surface) made all of it obsolete: every checkout's `.docs/vault` is a symlink that **pins the exact store path**, so plain file tools structurally cannot write to the wrong vault — there is nothing left to guard. Obsidian picks up external file changes natively; its MCP is demoted to an optional search/backlinks add-on owned by the `docs-obsidian` driver. Remote providers (Notion, GDrive — future) are the one exception: their Docs Root is a read-only mirror and writes go through the driver API with a re-sync.

The vault skeleton templates that used to live in this plugin moved with the responsibility: project templates to `docs-hub`, vault-global ones to `docs-obsidian`.

## `_index.md` as the contract

Each Docs Root folder's `_index.md` documents the folder's purpose and the frontmatter template for notes created in it. The skills **read the target folder's `_index.md` before creating any note** and copy its template, then update the folder's index list where the convention calls for it (Features, Contexts, ADRs). This keeps the note schema in the project docs — per-project, customizable — instead of hardcoded in the skills.

## Layout

```
plugins/spec/
├── .claude-plugin/plugin.json
├── README.md
├── docs/DESIGN.md                  # this file
├── skills/
│   ├── plan/SKILL.md (+ references/{plan-format,execution-modes}.md)
│   └── execute/SKILL.md
├── agents/{plan-executor,plan-executor-light,plan-executor-heavy,plan-reviewer}.md
└── commands/setup.md
```

## Out of scope (deliberately)

- Provider drivers and storage scaffolding — `docs-hub` / `docs-obsidian` own them.
- Global personal rules (attribution, Markdown formatting) — they stay in `~/.claude/CLAUDE.md`, applying to all work.
- Hard inter-plugin dependency resolution — Claude plugins have none; dependencies are documented and the setup command warns if any are missing.
