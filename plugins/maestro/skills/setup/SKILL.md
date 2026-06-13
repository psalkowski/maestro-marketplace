---
name: setup
description: Use as the marketplace's front door / "start here" onboarding — when a new user (or a fresh repo) needs the right plugins installed and configured but shouldn't have to know docs-hub, docs-obsidian, spec, conductor-kit, or graphify-kit by name. Interviews in plain terms (where docs live, Conductor, knowledge graph, spec workflow), installs the matching plugins from this marketplace, and runs their setups in dependency order. Idempotent and restart-aware. Triggers on /maestro:setup.
---

# /maestro:setup

The single branded entry point for onboarding a repo to this marketplace. You build a picture of
what the repo already uses, decide which plugins it needs, install the gaps, and delegate
configuration to each plugin's own setup skill **in dependency order**. You never inline another
plugin's setup logic and you never author any of their artifacts yourself.

**Read `${CLAUDE_PLUGIN_ROOT}/references/interview-map.md` first** — it carries the capabilities,
the artifact→plugin mapping, the **Setup Order**, and the per-plugin pitches. This SKILL.md is the
*flow*; the map is the *data*.

## The one rule that drives everything

**`claude plugin list` is the ONLY thing that decides "already handled."** A repo artifact —
`.conductor/`, `graphify-out/`, a legacy `## spec configuration`, a listening Obsidian port — is
evidence the repo **uses** that capability, which means you **propose the matching plugin**. An
artifact NEVER suppresses a plugin. So:

- Plugin **installed** (in `claude plugin list`) → it's handled; only offer an update.
- Plugin **not installed** but an artifact shows the capability is in use → **propose & install it**
  (its own setup will preserve/merge whatever the repo already has; legacy docs config gets migrated).
- Plugin **not installed** and no artifact → **ask** the user.

A repo that already uses Conductor + a graph + an Obsidian vault but has none of these plugins
installed must end up with **all of them proposed** — not skipped.

## Hard rules

- **You never write config yourself.** No `## docs configuration` block, no vault, no
  `settings.toml`/`settings.local.toml`, no `.graphifyignore` — every such artifact is produced by
  the **delegated** setup skill. Your only writes are `claude plugin install` / `update` calls and
  skill invocations.
- **Never stop mid-flow.** The interview (Phase 3) is the ONLY place you pause for input. Once you
  have the answers you MUST continue through install → configure → report in the same turn. Do not
  end your turn after asking a question without then acting on the answer. Do not end with an empty
  to-do.
- **Bash discipline.** Every command you RUN is a single command — **no** loops (`for`/`while`),
  **no** subshells (`$(...)`), **no** heredocs (`<<`), **no** multi-line scripts, **no** `python -c`/`node -e`.
  Parse `marketplace.json` by **reading it with the Read tool and reasoning over it**, not jq-in-a-loop.
- **Dual subscription.** Never hardcode `~/.claude`. All `claude plugin …` calls and cache reads
  honor the active `CLAUDE_CONFIG_DIR`. Resolve the marketplace clone path from
  `claude plugin marketplace list` output. If which subscription is ambiguous, ask.

---

## Phase 1 — Gather (always first; you cannot classify without this)

1. `claude plugin marketplace list`. If `maestro-marketplace` is **not** listed, offer
   `claude plugin marketplace add psalkowski/maestro-marketplace`. If the user declines, exit cleanly
   with that manual line — you cannot proceed.
2. From the list output, read the local clone path for `maestro-marketplace` (it respects
   `CLAUDE_CONFIG_DIR`; do not hardcode `~/.claude`). `Read` that clone's
   `.claude-plugin/marketplace.json` → the **Dynamic Catalog** (available plugins + versions +
   descriptions). Never a baked-in list.
3. **`claude plugin list`** → the **installed set** and versions. This is your skip gate; you must
   have it before Phase 2.

## Phase 2 — Classify each capability

For each capability in the map (docs, spec, Conductor, knowledge graph), inspect the repo
(read-only) and place it in exactly one bucket using the installed set from Phase 1:

Read-only signals:
- **Docs:** `## docs configuration` in `CLAUDE.local.md` (new contract) vs a **legacy**
  `## spec configuration` carrying `vault.*` keys (old Obsidian setup) vs neither.
- **Conductor:** `Glob` `.conductor/` and `.conductor/settings.local.toml`.
- **Graph:** `Glob` `graphify-out/`.
- **Obsidian hint:** `lsof -nP -iTCP -sTCP:LISTEN` (single command), grep output for 27123/27124.
- **Worktree:** `git rev-parse --git-dir` vs `--git-common-dir` (equal ⇒ main; different ⇒ worktree,
  note the derived main checkout path). Hold for Phase 5.

Buckets:
- **HANDLED** — the plugin is installed AND its config is present in the new form → nothing to do
  (note it for an update check in Phase 7).
- **PROPOSE** — the plugin is **not installed** but an artifact shows the capability is in use
  (`.conductor/` → conductor-kit; `graphify-out/` → graphify-kit; an Obsidian port/vault → docs on
  Obsidian). Confirm with the user in one line rather than asking open-ended ("This repo already uses
  Conductor and a graph — I'll install conductor-kit and graphify-kit. OK?").
- **MIGRATE** — a **legacy `## spec configuration`** exists → docs are on Obsidian via the old
  contract. Propose `docs-hub` + `docs-obsidian` (and `spec`); `/docs-hub:setup` performs the legacy
  → `## docs configuration` migration. Tell the user their vault content is untouched.
- **ASK** — no artifact and the plugin isn't installed → a genuine unknown; ask in Phase 3.

## Phase 3 — Interview (only the ASK buckets, one question at a time)

Ask the Interview Map questions **only for capabilities that landed in ASK**, one at a time, honoring
each question's defaults/highlights. PROPOSE and MIGRATE items are confirmed (a yes/no), not asked
open-ended; HANDLED items are silent. If every capability is HANDLED, jump to Phase 8 ("nothing to
do"). **After the answers come back, do not stop — go straight to Phase 4.**

## Phase 4 — Resolve set + install gaps

Union the plugins from every PROPOSE / MIGRATE / confirmed-ASK answer (per the map:
filesystem→`docs-hub`; obsidian→`docs-hub`+`docs-obsidian`; Conductor→`conductor-kit`;
graph→`graphify-kit`; spec→`spec`). For each chosen plugin **not in the installed set**, run one
command:

```
claude plugin install <name>@maestro-marketplace
```

(Default scope **user**, respecting `CLAUDE_CONFIG_DIR`.) **Track which you freshly installed this
run** — their skills are not loaded yet (no in-session skill reload), so they cannot be configured
until a restart.

## Phase 5 — Worktree-vs-main decision (asked once)

If Phase 2 found a **linked worktree** and any chosen plugin writes repo-level config (docs-hub,
spec, conductor-kit), ask the **single** main-vs-here question now (show the derived main checkout
path; recommend the main checkout — worktrees are then seeded by conductor-kit's script). Thread this
one decision into every setup in Phase 6; conductor-kit must land on the main checkout. On a main
checkout, skip this.

## Phase 6 — Configure what's loaded; defer the rest

Walk the chosen plugins **in Setup Order** (docs-hub → docs-obsidian → spec → conductor-kit →
graphify-kit, skipping unchosen). For each:

- **Setup skill already available this session** (installed before this run) → invoke its real setup,
  passing the Phase 5 decision: `/docs-hub:setup`, `/docs-obsidian:setup`, `/spec:setup`,
  `/conductor-kit:setup`, `/graphify-kit:setup`. That skill owns all config writing (including the
  legacy migration and merging the user's existing `.conductor` settings).
- **Freshly installed this run** (skills not loaded yet) → do not invoke; add to the **restart /
  re-run** list.

(docs-obsidian is normally pulled in by `/docs-hub:setup` when Obsidian was chosen.)

## Phase 7 — Offer updates

For each HANDLED or already-installed chosen plugin whose Catalog version exceeds the installed
version, offer `claude plugin update <name>` (needs a restart to apply). Same pass.

## Phase 8 — Report (always reached; never skipped)

Summarize precisely:
- **Installed** this run (and versions).
- **Configured now** — which setup skills you invoked, in order, the worktree decision applied, and
  any legacy migration performed.
- **Awaiting restart** — freshly-installed plugins whose setups run on the next pass.
- **Updates** offered/applied (need a restart).
- **Next command** — if anything awaits a restart/update: **restart Claude Code and re-run
  `/maestro:setup`** (idempotent, converges). If nothing remains: **"setup complete."**

If graphify-kit was chosen and the graphify CLI may be missing, note in one line that
`/graphify-kit:setup` installs it — you do not.

---

## Edge cases (must all hold)

- **Marketplace not added & user declines** → exit cleanly with the manual `marketplace add` line.
- **Repo already uses tools but no marketplace plugins installed** (the common real case) → every
  in-use capability is PROPOSE/MIGRATE, so all the matching plugins get installed — never "nothing
  to do." This is the bug class this skill exists to avoid: an artifact is never a skip.
- **Legacy `## spec configuration`** → MIGRATE: install docs-hub + docs-obsidian + spec; let
  `/docs-hub:setup` convert the block and leave vault content untouched.
- **Existing hand-written `.conductor/settings.local.toml`** → it is NOT proof conductor-kit is set
  up; if conductor-kit isn't installed, PROPOSE it. `/conductor-kit:setup` merges idempotently and
  preserves the user's keys (including any `general`).
- **Everything genuinely installed & configured** (every capability HANDLED) → "nothing to do".
- **Partial prior run** (installed-but-unconfigured after a restart) → skip install, go straight to
  configuring the now-loaded plugins.
- **Dual subscription** → never hardcode `~/.claude`; honor `CLAUDE_CONFIG_DIR`. If ambiguous, ask.
- **Idempotent install** → a present plugin is a skip, not an error — always check `claude plugin list` first.
