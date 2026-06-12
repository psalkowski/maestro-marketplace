# spec — design

The design record for the `spec` plugin and this marketplace. Captures what was decided and why, so the rationale survives.

## Goal

Take a set of project-specific Claude skills, agents, instructions, and an Obsidian vault structure — built for one project — and turn them into a **portable, personal bundle** usable across many projects, without committing anything to the project repos.

## Constraints (from the owner)

1. **Two tiers only.** Everything is either user-level (global `~/.claude/` + the installed plugin) or project-level **uncommitted** (`CLAUDE.local.md`). Nothing from the bundle is committed to a project repo.
2. **Generic, but dependency-aware.** The skills depend on `superpowers`, `grill-with-docs`, and the `obsidian` + `playwright` MCPs. These are prerequisites, not bundled.
3. **Design skill is project-owned.** Not every project has one; it's referenced by name in config and invoked dynamically, never hardcoded.
4. **Vault = project.** One project (a group of microservices) = one vault. Different projects = different vaults, switched by hand in Obsidian.

## Decisions

| Area | Decision | Why |
|---|---|---|
| Vehicle | A private marketplace repo with one plugin, `spec` | Standard Claude plugin format; installs user-level, so nothing touches the project repo |
| Config source | A fenced ```json block in uncommitted `CLAUDE.local.md` under `## spec configuration` | Auto-loaded into context (skills read it for free); no sidecar file; honors the two-tier rule |
| Keeping config un-tracked | `.git/info/exclude` (per-repo, never committed) — fall back only if not already ignored | Avoids editing the committed `.gitignore` |
| Schema | `project`, `vault.{name,root,subpath}` (subpath required), optional `designSkill` | Minimal; everything the skills need to resolve paths, the guard, and the design step |
| Naming | Plugin-namespaced: `spec:brainstorm` / `spec:plan` / `spec:execute` | Groups them legibly; no collisions |
| Design skill | Not bundled; named in config; invoked by name or skipped (explicitly) | Different projects have different design skills; some have none |
| Vault model | Vault = project; manual switch; a pre-write **guard** | The Obsidian MCP serves whichever vault is open — it can't pick one, so the skills refuse to write to the wrong one |
| Vault template | A **full vault** skeleton (Daily, References, Roadmap, Scratch, Projects + a project subtree), every dir with a frontmatter'd `_index.md` | "A full installation, not just a project"; the `_index.md` files are the note-convention source of truth |
| Setup | `/spec:setup` — config + idempotent vault scaffold; skips existing files; smart defaults; preview + consent | One command leaves a project ready; never overwrites |
| Distribution | Private GitHub repo (owner handles the git identity) | Portable across machines |

## The vault guard

The Obsidian MCP connects to **one running vault at a time** (the currently-open one). A skill cannot switch vaults. So:

- The project `_index.md` at `<root>/<subpath>/_index.md` carries `vault: <name>` in its frontmatter — the **identity marker**.
- Before any write, a skill reads that file and checks `vault:` against `config.vault.name`. Mismatch or missing → it **stops** and asks the user to open the right vault in Obsidian.
- For cross-vault reach with a single MCP config, each vault's Local REST API uses the **same port + API key**, so the one `obsidian` MCP follows whichever vault is open. `/spec:setup` prints this as a one-time reminder.

## `_index.md` as the contract

Each vault folder's `_index.md` documents the folder's purpose and the frontmatter template for notes created in it. The skills **read the target folder's `_index.md` before creating any note** and copy its template, then update the folder's index list where the convention calls for it (Features, Contexts, ADRs). This keeps the note schema in the vault — per-project, customizable — instead of hardcoded in the skills.

## Layout

```
spec-marketplace/
├── .claude-plugin/marketplace.json
├── README.md
├── docs/DESIGN.md                  # this file
└── plugins/spec/
    ├── .claude-plugin/plugin.json
    ├── README.md
    ├── skills/{brainstorm,plan,execute}/SKILL.md
    ├── agents/{plan-executor,plan-executor-heavy,plan-reviewer}.md
    ├── commands/setup.md
    └── templates/
        ├── vault/{Daily,References,Roadmap,Scratch,Projects}/_index.md
        └── project/{_index.md, Features,Brainstorms,Specs,Plans,Contexts,ADRs,Notes/_index.md}
```

## Out of scope (deliberately)

- A `Shared/` cross-project area in the vault — left to the owner to add if a need appears.
- Global personal rules (attribution, Markdown formatting) — they stay in `~/.claude/CLAUDE.md`, applying to all work.
- Hard inter-plugin dependency resolution — Claude plugins have none; dependencies are documented and the setup command warns if any are missing.
