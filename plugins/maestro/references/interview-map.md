# Interview Map

The hand-authored knowledge maestro relies on: the per-capability signals, which capability maps to
which plugin set, the dependency Setup Order, and a one-line pitch per plugin. This is the **single
maintenance surface** when a new marketplace plugin ships — add a capability/signal block here and an
entry to the catalog (`marketplace.json`); `skills/setup/SKILL.md` reads its intent from this file
and needs no change.

Maestro never hardcodes the installable plugin list — that comes from the **Dynamic Catalog** (the
live `marketplace.json` + `claude plugin list`). This map carries the _signal → plugin-set_ mapping
and the ordering.

## The skip gate

**The ONLY thing that marks a capability "already handled" is the plugin being installed
(`claude plugin list`).** The repo artifacts below are evidence the capability is **in use** — they
make maestro **propose** the plugin, they never suppress it. Classify each capability:

- plugin **installed** + config present → **HANDLED** (update check only);
- plugin **not installed** + an in-use artifact → **PROPOSE** (install + configure); a legacy docs
  block → **MIGRATE**;
- plugin **not installed** + no artifact → **ASK**.

---

## Plugins (one-line pitch each)

| plugin          | pitch                                                                                                                                                                                    |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `docs-hub`      | Provider-agnostic project docs: one `## docs configuration` block, a Backing Store outside the checkout, and a `.docs/vault` Docs Root every other plugin reads. The storage front door. |
| `docs-obsidian` | Obsidian driver for docs-hub: points the Backing Store at an Obsidian vault, scaffolds vault-global folders, and offers the optional Obsidian MCP add-on.                                |
| `spec`          | Feature-spec workflow: `/spec:plan` writes a durable spec into your docs, `/spec:execute` runs handed-off plans. Needs docs configured first.                                            |
| `conductor-kit` | Wires the repo into Conductor: personal-layer prompt overrides plus a workspace setup script that seeds `.docs/` and `CLAUDE.local.md` into every new workspace.                         |

---

## Capabilities → signals → plugin sets

For each, the **HANDLED gate** is the plugin in `claude plugin list`. Below that gate, the listed
artifact decides PROPOSE/MIGRATE vs ASK.

### Docs — where specs, plans, ADRs, notes live

- **HANDLED gate:** `docs-hub` installed AND a `## docs configuration` block in `CLAUDE.local.md`.
- **MIGRATE:** a legacy `## spec configuration` block with `vault.*` keys exists (old Obsidian setup)
  → propose `docs-hub` + `docs-obsidian`; `/docs-hub:setup` migrates the block, vault content untouched.
- **PROPOSE:** a listening Obsidian REST port (27123/27124) or an obvious vault, but no docs block →
  propose `docs-hub` + `docs-obsidian`.
- **ASK Q1 — Where should this project's docs live?** filesystem (default) → `docs-hub`; obsidian
  (highlight if a port/vault was detected) → `docs-hub` + `docs-obsidian`; skip docs → none (also
  suppresses spec).

### Spec — feature-spec workflow

- **HANDLED gate:** `spec` installed AND a (new, minimal) `## spec configuration` block.
- **PROPOSE/MIGRATE:** a legacy `## spec configuration` exists but `spec` isn't installed → propose
  `spec` (alongside the docs migration).
- **ASK Q3** (only if docs were not skipped): Feature-spec workflow (`/spec:plan` / `/spec:execute`)?
  yes → `spec`; no → none.

### Conductor

- **HANDLED gate:** `conductor-kit` installed.
- **PROPOSE:** `.conductor/` exists (even with a hand-written `settings.local.toml` — that is the
  user's own config, NOT proof conductor-kit is wired) → propose `conductor-kit`; its setup merges
  idempotently and preserves the user's keys.
- **ASK Q2** (default yes if `.conductor/` exists): Do you use Conductor for this repo? yes →
  `conductor-kit`; no → none.

---

## Setup Order

When configuring (invoking the chosen plugins' setup skills), always run them in this dependency
order, skipping plugins not in the chosen set:

1. `docs-hub` — storage first; every other plugin reads the docs configuration.
2. `docs-obsidian` — driver; only when Obsidian was chosen, after docs-hub.
3. `spec` — needs docs configured.
4. `conductor-kit` — last; its setup script seeds a configured Docs Root, so docs/spec come first. Must land on the main checkout.

Setup entry points (invoke by exact slash command once the skill is loaded this session):

- `docs-hub` → `/docs-hub:setup`
- `docs-obsidian` → `/docs-obsidian:setup` (normally pulled in by `/docs-hub:setup` when Obsidian is chosen; can be invoked directly)
- `spec` → `/spec:setup`
- `conductor-kit` → `/conductor-kit:setup`

---

## Adding a new marketplace plugin

1. Ensure it has an entry in `marketplace.json` (the Dynamic Catalog picks up name/version/description automatically).
2. Add it to the pitch table above.
3. Add a capability block: the HANDLED gate (its installed name + config artifact), the in-use
   artifact that triggers PROPOSE, and the ASK question that maps a plain choice to the plugin.
4. Insert it at the correct position in the **Setup Order** if it has a dependency relationship.
5. List its setup entry point. No change to `skills/setup/SKILL.md` is required.
