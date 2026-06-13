# maestro (v0.1.0)

**Start here.** maestro is the marketplace's front door — the one plugin you install to onboard a
repo without learning the others by name. Run `/maestro:setup` and it interviews you in plain terms,
then installs and configures the right plugins from this marketplace **in the right order**.

You don't need to know that docs storage comes before everything else, that `docs-obsidian` is a
driver, or that `spec` needs docs configured first — maestro encodes that and delegates the actual
work to each plugin's own setup skill.

## Getting started

```
claude plugin marketplace add psalkowski/maestro-marketplace
claude plugin install maestro@maestro-marketplace
/maestro:setup
```

If the marketplace isn't added yet, `/maestro:setup` offers to add it for you.

## What it asks (and what each answer installs)

maestro detects what's already configured and **only asks about genuine gaps**, one question at a time:

1. **Where should this project's docs live?** — filesystem (default) or Obsidian, or skip docs.
   → installs `docs-hub` (filesystem) or `docs-hub` + `docs-obsidian` (Obsidian).
2. **Do you use Conductor for this repo?** — defaults to yes when a `.conductor/` directory is found.
   → installs `conductor-kit`.
3. **Want a code knowledge graph?** → installs `graphify-kit` (its own setup installs the graphify CLI
   prerequisite if it's missing — maestro doesn't).
4. **Feature-spec workflow?** (only offered if you didn't skip docs) → installs `spec`.

After resolving your answers, maestro installs the gaps with
`claude plugin install <name>@maestro-marketplace`, then runs each plugin's setup skill in
dependency order: **docs-hub → docs-obsidian → spec → conductor-kit → graphify-kit**.

maestro never writes any configuration itself — every `## docs configuration` block, vault, or
`settings.toml` is produced by the plugin's own setup skill that maestro delegates to.

## The restart caveat

Claude Code loads a plugin's skills only at session start. So a **first-time** setup that installs new
plugins takes two passes:

1. **First pass** — maestro installs the new plugins and configures any that were already present,
   then reports which ones are *awaiting a restart*.
2. **Restart Claude Code**, then **re-run `/maestro:setup`** — now the freshly-installed plugins'
   setups are loaded, and maestro runs them in order.

Plugins that were already installed before you ran maestro are configured immediately, no restart
needed.

## Idempotent re-run

`/maestro:setup` is safe to run any number of times. It re-detects state each run, skips anything
already installed or configured, and converges on the desired state. Re-running with everything in
place reports **"setup complete"** and prompts nothing. It also offers
`claude plugin update <name>` when a newer version is available in the marketplace.

## Dual-subscription note

maestro never hardcodes `~/.claude`. All `claude plugin …` calls and marketplace-cache reads honor
the active `CLAUDE_CONFIG_DIR`, so installs land in **whichever subscription the current session is
using** (e.g. `~/.claude` for personal, `~/.claude-team` for team). If which subscription to target
is ambiguous, maestro asks.

## How it stays current

- **Dynamic Catalog** — maestro reads the live `marketplace.json` and `claude plugin list` at runtime
  for *what exists and what's installed*. New plugins and versions appear automatically.
- **Interview Map** (`references/interview-map.md`) — the hand-authored *which question implies which
  plugins* and *the setup order*. When a new marketplace plugin ships, this is the only file to touch;
  the setup flow doesn't change.
