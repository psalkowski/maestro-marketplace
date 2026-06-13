---
description: Use when onboarding a repository to graphify (knowledge graph) or re-running onboarding after .graphifyignore changes — installs the CLI, analyzes the repo to propose exclusions, builds the AST graph, installs the agent navigation protocol (CLAUDE.md section + Explore override), and wires worktree seeding. Triggers on /graphify-kit:setup.
---

# /graphify-kit:setup

Onboard the current repository to graphify with the full battle-tested setup: exclusion analysis, AST graph, navigation protocol, Explore agent override, and worktree seeding. Idempotent — safe to re-run; re-running after a `.graphifyignore` change performs the required from-scratch rebuild.

Run from the repo root of the **main checkout** (not a worktree — `.git` must be a directory).

## Step 0 — Preflight

1. `git rev-parse --is-inside-work-tree` must succeed, and `.git` must be a directory (worktrees receive their graph via seeding, never their own setup).
2. CLI: `command -v graphify` — if missing, install with `uv tool install graphifyy` (fallback: `pipx install graphifyy`) and verify `graphify --version`.
3. `jq` must be available (the symbol directory depends on it).
4. If `graphify-out/graph.json` already exists, tell the user and ask whether they want a health check (`/graphify-kit:doctor`), a protocol refresh (steps 3–6 only), or a full rebuild (continue from step 1; `rm -rf graphify-out` first — preserve `graphify-out/cache/semantic/` if it exists, it holds paid LLM extractions keyed by content hash).

## Step 1 — Exclusion analysis (the step that makes or breaks graph quality)

A graph built without exclusion analysis reproduces every known failure mode: duplicate-name wrong-matches, god-node noise, and wasted LLM extraction. Analyze before building:

1. Inventory: `du -sh */ 2>/dev/null | sort -rh | head -20` and a file count per top-level dir. Read the repo README/CLAUDE.md for structure context.
2. Apply these evidence-based heuristics and build a proposed `.graphifyignore`:
   - **Always exclude:** package manager dirs and lockfiles (`node_modules/`, `package-lock.json`, vendor dirs), build output (`dist/`, `build/`, `coverage/`, `.nx/`, `storybook-static/`), tool metadata (`.git/`, `.vscode/`, `.idea/`, `playwright-report/`, `test-results/`), minified/generated artifacts (`*.min.js`, `*.map`), and **all images** (`*.webp *.png *.jpg *.jpeg *.gif *.svg *.ico` — they cost one vision subagent each at extraction time and have near-zero navigation value).
   - **Exclude name-duplicators:** design/mockup apps and prototype dirs that intentionally duplicate production component names — these cause the substring matcher to silently return the wrong node. Detect by looking for parallel implementations of the same component names.
   - **Exclude prose without linkage value:** marketing/site content (`content/`, `public/` of docs/landing apps — keep their `src/`), spec/plan archives superseded by other systems, blog posts. Every indexed doc costs recurring LLM extraction on change.
   - **Exclude harness config:** `.claude/` (the assistant already receives it through its own loading; indexing it is pure extraction cost), `.github/` workflows.
   - **KEEP tests that import production code** — e2e/integration suites contribute real cross-edges into production symbols, which is what makes `graphify affected` usable for test selection. Only exclude test _fixtures_ and _snapshots_.
3. Present the proposal as a table (path → reason → size/file count) and **get user approval before writing** `.graphifyignore`. Annotate the file with comments explaining each non-obvious exclusion.
4. Add `graphify-out/` to `.gitignore` (and `.graphifyignore` itself unless the team decides to share it).

## Step 2 — Build the AST graph (zero LLM)

```bash
graphify update .
git rev-parse HEAD > graphify-out/.graphify-baseline-sha
```

This is deterministic and free — no API keys needed for a code-only corpus. Report node/edge counts. If the user wants docs/knowledge-base content semantically indexed (LLM extraction), point them to `/graphify-kit:sync-docs` afterwards — never run semantic extraction inline here, and never with a top-tier model.

## Step 3 — Install the navigation protocol

Install `${CLAUDE_PLUGIN_ROOT}/templates/claude-md-section.md` as a managed block (wrapped in `<!-- graphify-kit:begin -->` / `<!-- graphify-kit:end -->` markers) into exactly ONE project-level memory file. Check both `CLAUDE.md` and `CLAUDE.local.md`, then pick the target in this order:

1. **Markers already present** — if either file already contains a `graphify-kit:begin` block, replace that block in place and stop. Never write the block to both; if both somehow have it, keep the one in the file chosen by the rules below and delete the other.
2. **`CLAUDE.md` already documents graphify** — if `CLAUDE.md` mentions graphify outside our markers (a `## Graphify` heading, `graphify-out`, `graphify explain`, or a leftover `graphify claude install` section), install/replace the block in `CLAUDE.md` so all graphify guidance lives in one shared, committed place.
3. **Default → `CLAUDE.local.md`** — otherwise install into `CLAUDE.local.md` (create it if missing). This is the preferred target: the protocol describes a local, uncommitted graph, so its guidance belongs alongside `graphify-out/` and `.graphifyignore` rather than in committed memory. Ensure the file is git-ignored: `git check-ignore -q CLAUDE.local.md`; if it is NOT already ignored, append `CLAUDE.local.md` to `.git/info/exclude` (the per-repo, never-committed ignore file). Report which mechanism already covered it, or that you added the exclude.

Idempotency: re-running replaces the block in whichever file currently holds it; it does not migrate the block between files on its own.

Note: if the repo previously ran `graphify claude install`, its query-centric section and PreToolUse hook are superseded by this plugin — remove them (the upstream section steers agents to `graphify query`, which returns BFS neighborhoods, not matches; see the protocol for the measured evidence). That legacy section satisfies rule 2, so install the managed block into `CLAUDE.md` and delete the legacy lines.

## Step 4 — The graph-aware Explore agent

This plugin **ships** a graph-aware Explore agent (`graphify-kit:Explore`, at `${CLAUDE_PLUGIN_ROOT}/agents/explore.md`). It is available in every repo with the plugin installed, updates with `/plugin marketplace update`, and self-degrades to plain Grep/Glob/Read where no graph exists. The CLAUDE.md block (Step 3) carries the rule that routes the main loop to it.

Plugin agents are **namespaced** (`graphify-kit:Explore`), so the shipped agent cannot _shadow_ the built-in `Explore` by name — the prefer-rule is what makes the main loop dispatch it instead of the bare native Explore. For the stronger guarantee of shadowing the native `Explore` by name (it intercepts even "use Explore" muscle memory), or for a hand-tuned, repo-specific superset, **optionally** copy the agent to the project:

```bash
cp "${CLAUDE_PLUGIN_ROOT}/agents/explore.md" .claude/agents/explore.md
```

A project-level agent named `Explore` shadows the built-in at session start. **If `.claude/agents/explore.md` already exists with richer, project-tuned content, leave it** — never flatten a superset to the generic agent; hand-port any new protocol rules into it instead, and show a diff before any overwrite.

The agent file (plugin or project copy) is the **only** channel that carries the protocol into a subagent: subagents do not inherit CLAUDE.md, and PreToolUse hook nudges do not reach subagent tool calls — which is why the rules in it are mechanical and action-triggered (pre-Read explain gate).

## Step 5 — Worktree seeding

Copy `${CLAUDE_PLUGIN_ROOT}/scripts/worktree-setup.sh`, `${CLAUDE_PLUGIN_ROOT}/scripts/sync.sh`, and `${CLAUDE_PLUGIN_ROOT}/scripts/sync_helper.py` into `<repo>/scripts/graphify/` and mark the shell scripts executable. Committing them with the repo keeps worktree bootstrap independent of any machine's plugin cache path, and teammates without the plugin still get seeded graphs.

Then wire the bootstrap for the worktree manager in use:

- **Conductor** (`.conductor/` exists): ensure the repo's setup script calls it once the worktree is ready:
  ```bash
  bash scripts/graphify/worktree-setup.sh || true
  ```
  Guard against double-seeding races: if the setup script also copies/rsyncs files into the worktree, the graphify call must come AFTER those steps, and nothing else should copy `graphify-out` (a `cp -R` racing an rsync produces a nested `graphify-out/graphify-out`).
- **Plain `git worktree` / other managers:** tell the user to run `bash scripts/graphify/worktree-setup.sh` once in each new worktree, or wire it into their bootstrap of choice (direnv, post-checkout hook, Makefile target).

## Step 6 — Hooks check

The plugin ships session hooks automatically (SessionStart/Stop AST sync + PreToolUse nudges); they no-op in repos without a graph, so nothing needs installing per project. Check `.claude/settings.json` and `.claude/settings.local.json` for pre-existing graphify hooks from a manual setup and tell the user to remove duplicates (double-nudging trains agents to ignore the nudge).

## Step 7 — Verify

Run the `/graphify-kit:doctor` checks (graph exists, baseline == HEAD, manifest clean, symbol directory returns results for a real domain term from this repo). Then demonstrate value in one shot: pick a central symbol from the directory output and show `graphify explain "<Symbol>"` resolving with file:line.

Report what was installed, what was skipped, and the one-line usage summary: _symbol directory → explain → targeted Read_.
