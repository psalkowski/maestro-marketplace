---
name: setup
description: Use as the marketplace's front door / "start here" onboarding — when a new user (or a fresh repo) needs the right plugins installed and configured but shouldn't have to know docs-hub, docs-obsidian, spec, conductor-kit, or graphify-kit by name. Interviews in plain terms (where docs live, Conductor, knowledge graph, spec workflow), installs the matching plugins from this marketplace, and runs their setups in dependency order. Idempotent and restart-aware. Triggers on /maestro:setup.
---

# /maestro:setup

The single branded entry point for onboarding a repo to this marketplace. You interview the user
in plain terms, resolve which plugins they need, install the gaps, and delegate configuration to
each plugin's own setup skill **in dependency order**. You never inline another plugin's setup
logic and you never author any of their artifacts yourself.

**Read `${CLAUDE_PLUGIN_ROOT}/references/interview-map.md` first** — it carries the questions,
the option→plugin mapping, the **Setup Order**, and the per-plugin pitches. This SKILL.md is the
*flow*; the map is the *data*. When a new marketplace plugin ships, only the map changes.

Use `TodoWrite` to track the nine steps.

## Hard rules

- **You never write config yourself.** No `## docs configuration` block, no vault, no
  `settings.toml`/`settings.local.toml`, no `.graphifyignore` — every such artifact is produced by
  the **delegated** setup skill. Your only writes are `claude plugin install` / `update` calls and
  skill invocations.
- **Bash discipline.** Every command you RUN must be a single command — **no** loops (`for`/`while`),
  **no** subshells (`$(...)`), **no** heredocs (`<<`), **no** multi-line scripts, **no** `python -c`/`node -e`.
  Parse `marketplace.json` by **reading it with the Read tool and reasoning over it**, not jq-in-a-loop.
  Use dedicated tools (`Read`/`Grep`/`Glob`) over shell wherever possible.
- **Dual subscription.** Never hardcode `~/.claude`. All `claude plugin …` calls and cache reads
  honor the active `CLAUDE_CONFIG_DIR`. Resolve the marketplace clone path from
  `claude plugin marketplace list` output, not from a fixed home path. If which subscription is
  ambiguous, ask.

---

## Step 1 — Locate the marketplace & build the Dynamic Catalog

1. Run `claude plugin marketplace list`.
2. If `maestro-marketplace` is **not** listed: offer to add it with
   `claude plugin marketplace add psalkowski/maestro-marketplace`. If the user **declines**, you
   cannot proceed — exit, telling them the manual line to run (`claude plugin marketplace add psalkowski/maestro-marketplace`)
   and that `/maestro:setup` will work once it's added.
3. From the `marketplace list` output, **read the local clone path** for `maestro-marketplace`
   (do NOT hardcode `~/.claude`; the path lives in the command output and respects `CLAUDE_CONFIG_DIR`).
   `Read` that clone's `.claude-plugin/marketplace.json` and reason over it to build the
   **Dynamic Catalog**: the available plugins, their current versions, and descriptions. This is the
   source of *what exists* — never a baked-in list.
4. Run `claude plugin list` to learn *what is already installed* and at which version.

You now have: catalog (available + versions + descriptions) and installed state.

## Step 2 — Detect project state (read-only hints)

Inspect the repo so you only ask about genuine gaps. All read-only:

- **Docs configured?** `Read` `CLAUDE.local.md` (if present) and look for a `## docs configuration`
  fenced block. If present, note the provider; skip Q1.
- **Spec configured?** Same file — a `## spec configuration` block ⇒ skip Q4.
- **Conductor?** `Glob` for `.conductor/` and `.conductor/settings.local.toml`. A `.conductor/`
  dir (or a workspace-shaped path) defaults Q2 to yes; an existing `settings.local.toml` ⇒ skip Q2.
- **Knowledge graph?** `Glob` for `graphify-out/`. Present ⇒ skip Q3.
- **Obsidian hint (for Q1 only):** `lsof -nP -iTCP -sTCP:LISTEN` (single command; grep its output for
  port 27123/27124). A listener is a *hint* that Obsidian is in use — surface it when asking Q1, but
  never decide for the user.
- **Worktree vs main:** run `git rev-parse --git-dir` and `git rev-parse --git-common-dir`. Equal ⇒
  main checkout. Different ⇒ a linked worktree (note the derived main checkout path; the parent of
  the common git dir). Hold this for Step 6.

## Step 3 — Interview (one question at a time)

Walk the **Interview Map** questions Q1→Q4 **in order**, asking one at a time and **skipping any
question whose gap Step 2 already satisfied**. Honor each question's defaults and highlights (e.g.
default Obsidian-friendly phrasing only when a vault/REST port was detected; default Q2 yes when
`.conductor/` exists; Q4 only offered when docs were not skipped). If every question is already
satisfied, say so and jump toward Step 9 ("nothing to do").

## Step 4 — Resolve plugin set + Setup Order

Take the union of the plugins implied by the answers (per the map): filesystem→`docs-hub`;
obsidian→`docs-hub`+`docs-obsidian`; Conductor→`conductor-kit`; graph→`graphify-kit`; spec→`spec`.
Order them by the map's **Setup Order**: `docs-hub` → `docs-obsidian` → `spec` → `conductor-kit`
→ `graphify-kit` (skipping any not chosen).

## Step 5 — Install the gaps

Cross-reference the chosen set against `claude plugin list` (Step 1). For each chosen plugin **not
already installed**, run one command:

```
claude plugin install <name>@maestro-marketplace
```

(Default scope is **user**, which respects the active `CLAUDE_CONFIG_DIR`.) Installing an
already-installed plugin would be redundant — skip those by checking the installed list first;
never treat a present plugin as an error. **Track which plugins you freshly installed this run** —
their skills are not loaded yet (no in-session skill reload), so they cannot be configured until a
restart.

## Step 6 — Worktree-vs-main decision (asked once)

If Step 2 found you are in a **linked worktree** and any chosen plugin's setup writes repo-level
config (docs-hub, spec, conductor-kit), ask the **single** main-vs-here question now — show the
derived main checkout path and ask whether to configure **the main checkout** (recommended;
worktrees are then seeded by conductor-kit's script) **or this worktree**. Thread this one decision
to every setup you invoke in Step 7 — do **not** let each plugin re-prompt. conductor-kit
specifically must land on the main checkout; enforce that by passing the decision, not by
re-asking. On a main checkout, skip this question.

## Step 7 — Configure what's loaded; defer the rest

Walk the chosen plugins **in Setup Order**. For each:

- **Setup skill already available this session** (the plugin was installed before this run) → invoke
  its real setup skill, passing the Step 6 worktree decision: `/docs-hub:setup`, `/docs-obsidian:setup`,
  `/spec:setup`, `/conductor-kit:setup`, `/graphify-kit:setup`. Let that skill own all config writing.
- **Freshly installed this run** (skills not yet loaded) → do **not** try to invoke it. Add it to the
  **restart / re-run** list.

(docs-obsidian is normally pulled in by `/docs-hub:setup` when Obsidian was chosen; if it is loaded
you may also invoke it directly, but never duplicate its work.)

## Step 8 — Offer updates (re-run flow)

Compare the Dynamic Catalog version against the installed version for each already-installed chosen
plugin. Where the catalog version is **higher**, offer `claude plugin update <name>` (note: an update
needs a restart to apply). Fold this into the same pass.

## Step 9 — Report

Summarize precisely:

- **Installed** this run (and at what version).
- **Configured now** (which setup skills you invoked, in order, and the worktree decision applied).
- **Awaiting restart** — the freshly-installed plugins whose setups will run on the next pass.
- **Updates offered/applied** (if any) and that they need a restart.
- **Next command** — if anything awaits a restart or update, tell the user to **restart Claude Code
  and re-run `/maestro:setup`** (it is idempotent and converges). If nothing remains, say
  **"setup complete."**

For graphify-kit, if it was chosen and the graphify CLI may be missing, surface a one-line note that
`/graphify-kit:setup` handles the CLI install — you do not.

---

## Edge cases (must all hold)

- **Marketplace not added & user declines** → exit cleanly with the manual `marketplace add` line; do not proceed.
- **Everything already installed & configured** → report "nothing to do"; prompt nothing.
- **Partial prior run** (installed-but-unconfigured, e.g. after a restart) → skip install, go straight
  to configuring the now-loaded plugins. This is the second half of the restart flow.
- **Obsidian chosen but no vault/REST detected** → still proceed; `/docs-obsidian:setup` handles vault
  entry and the no-listener pointer. You just install and delegate.
- **graphify-kit chosen without the CLI present** → install the plugin; let `/graphify-kit:setup` own
  the CLI prerequisite. Only surface the note.
- **Dual subscription** → never hardcode `~/.claude`; honor `CLAUDE_CONFIG_DIR`. If ambiguous, ask.
- **Idempotent install** → a present plugin is a skip, not an error — always check `claude plugin list` first.
