# Interview Map

The hand-authored knowledge maestro relies on: which question maps to which plugin set,
the dependency Setup Order, and a one-line pitch per plugin. This is the **single maintenance
surface** when a new marketplace plugin ships — add a question/option line here and an entry to
the catalog (`marketplace.json`); `skills/setup/SKILL.md` reads its intent from this file and
needs no change.

Maestro never hardcodes the installable plugin list — that comes from the **Dynamic Catalog**
(the live `marketplace.json` + `claude plugin list`). This map only carries the
*question → plugin-set* mapping and the ordering.

---

## Plugins (one-line pitch each)

| plugin | pitch |
| --- | --- |
| `docs-hub` | Provider-agnostic project docs: one `## docs configuration` block, a Backing Store outside the checkout, and a `.docs/vault` Docs Root every other plugin reads. The storage front door. |
| `docs-obsidian` | Obsidian driver for docs-hub: points the Backing Store at an Obsidian vault, scaffolds vault-global folders, and offers the optional Obsidian MCP add-on. |
| `spec` | Feature-spec workflow: `/spec:plan` writes a durable spec into your docs, `/spec:execute` runs handed-off plans. Needs docs configured first. |
| `conductor-kit` | Wires the repo into Conductor: personal-layer prompt overrides plus a workspace setup script that seeds `.docs/`, `CLAUDE.local.md`, and the graph into every new workspace. |
| `graphify-kit` | Code knowledge graph: AST graph + agent navigation protocol (symbol directory → explain → targeted Read), session sync hooks, worktree seeding. Requires the graphify CLI (its setup installs it). |

---

## Questions → plugin sets

Ask **one question at a time**, in order, **skipping any question whose gap is already satisfied**
(see "Skip-if-satisfied" per question). Each answer resolves to zero or more plugins; the union
of all answers is the chosen plugin set.

### Q1 — Where should this project's docs (specs, plans, ADRs, notes) live?

- **filesystem** (default) → `docs-hub`
- **obsidian** → `docs-hub` + `docs-obsidian` (highlight this option if a vault or a listening Obsidian REST port was detected)
- **skip docs** → (no plugins; also suppresses Q4)

Skip-if-satisfied: a `## docs configuration` block already exists in `CLAUDE.local.md`. If present,
report the configured provider and do not ask; treat docs as "not skipped" for Q4.

### Q2 — Do you use Conductor for this repo?

- **yes** (default if `.conductor/` exists or the path looks like a Conductor workspace) → `conductor-kit`
- **no** → (no plugins)

Skip-if-satisfied: a `.conductor/settings.local.toml` already exists (conductor-kit already wired).

### Q3 — Want a code knowledge graph?

- **yes** → `graphify-kit` (note: its setup installs the graphify CLI prerequisite if missing — maestro does not)
- **no** → (no plugins)

Skip-if-satisfied: `graphify-out/` already exists in the repo.

### Q4 — Feature-spec workflow (`/spec:plan` / `/spec:execute`)?

Only offered if docs were **not** skipped in Q1 (spec needs docs configured).

- **yes** → `spec`
- **no** → (no plugins)

Skip-if-satisfied: a `## spec configuration` block already exists in `CLAUDE.local.md`.

---

## Setup Order

When configuring (invoking the chosen plugins' setup skills), always run them in this dependency
order, skipping plugins not in the chosen set:

1. `docs-hub` — storage first; every other plugin reads the docs configuration.
2. `docs-obsidian` — driver; only when Obsidian was chosen, after docs-hub.
3. `spec` — needs docs configured.
4. `conductor-kit` — before-last; its setup script seeds a configured Docs Root, so docs/spec come first. Must land on the main checkout.
5. `graphify-kit` — last; indexes whatever exists.

Setup entry points (invoke by exact slash command once the skill is loaded this session):

- `docs-hub` → `/docs-hub:setup`
- `docs-obsidian` → `/docs-obsidian:setup` (normally pulled in by `/docs-hub:setup` when Obsidian is chosen; can be invoked directly)
- `spec` → `/spec:setup`
- `conductor-kit` → `/conductor-kit:setup`
- `graphify-kit` → `/graphify-kit:setup`

---

## Adding a new marketplace plugin

1. Ensure it has an entry in `marketplace.json` (the Dynamic Catalog picks up its name/version/description automatically).
2. Add it to the pitch table above.
3. Add (or extend) a question/option line that maps a plain-language choice to the new plugin.
4. Insert it at the correct position in the **Setup Order** if it has a dependency relationship.
5. List its setup entry point. No change to `skills/setup/SKILL.md` is required.
