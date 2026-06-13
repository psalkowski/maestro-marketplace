# graphify-kit (v0.5.0)

Battle-tested [graphify](https://github.com/safishamsi/graphify) setup for any repository — the full toolkit that makes a knowledge graph actually get used by coding agents, instead of being queried once and abandoned for grep.

Measured on a real production monorepo (identical prompt, identical model — Haiku 4.5): the graph-assisted session finished in **40% fewer turns at roughly half the cumulative tokens** of a no-graph control, with **0 factual errors vs 4** — and it was the only session that found the integration test proving the investigated behavior. Cheap models benefit the most: the graph replaces "skim three whole files and synthesize" with "ask one deterministic question, get 15 lines with file:line".

## Why a kit? Isn't `graphify install` enough?

A bare graph gets abandoned. Observed failure mode (repeatedly, in real transcripts): the agent guesses symbol names (`explain "CandidateRepository"` — plausible, nonexistent), misses 5 of 7 cold guesses, concludes the graph doesn't cover the area, and greps for the rest of the session. The fixes are protocol + delivery, not the graph itself:

1. **Symbol directory** — a deterministic jq enumeration over node labels that turns a concept word into real symbol names _before_ any `explain` (upstream feature request: [safishamsi/graphify#1296](https://github.com/safishamsi/graphify/issues/1296)).
2. **Anti-guessing + re-entry rules** — never explain an unobserved name; the moment grep shows a real name, the next relationship question goes to `explain`.
3. **Delivery to every context** — a `CLAUDE.md` section for the main loop, a shipped graph-aware `graphify-kit:Explore` agent for subagents (they don't inherit CLAUDE.md, and hook nudges don't reach them) plus an optional project-level `Explore` override, and PreToolUse nudges that fire at exactly the moment the agent reaches for grep.
4. **Exclusion analysis before the first build** — design mockups that duplicate production names, doc-site prose, and images poison the matcher and burn extraction tokens. The setup skill analyzes the repo and proposes a `.graphifyignore` before building. (Tests that import production code are deliberately KEPT — they power `affected`-based test selection.)
5. **`graphify query` is retired** — measured across two graphify versions: it BFS-floods 2-hop neighborhoods from ~3 substring-matched seeds (102–739 noise nodes per call) and never returns the matching names. Richer "natural language" prompts make it worse.

## Install

```
/plugin marketplace add psalkowski/maestro-marketplace
/plugin install graphify-kit
```

Then, in each repo to onboard (main checkout, not a worktree):

```
/graphify-kit:setup
```

## What's inside

| Component                 | Purpose                                                                                                                                                                                            |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/graphify-kit:setup`     | Guided onboarding: CLI install, exclusion analysis → `.graphifyignore` proposal, AST build (zero LLM), CLAUDE.md protocol section, shipped Explore agent (optional project copy), worktree seeding |
| `/graphify-kit:doctor`    | Health checks with prescribed repairs: baseline drift, manifest key hygiene (the double-extraction trap), ghost nodes, nested graphify-out, protocol presence, explain spot-checks                 |
| `/graphify-kit:sync-docs` | Deliberate LLM indexing of in-repo docs plus the project's Docs Root (`.docs/vault/`), with model discipline (mid-tier subagents only), semantic-cache reuse, and honest verification              |
| Hooks (automatic)         | SessionStart/Stop incremental AST sync (zero LLM, backgrounded); PreToolUse nudges steering grep→explain re-entry. All no-op instantly in repos without a graph                                    |
| `templates/`              | The CLAUDE.md protocol section (single source the setup skill installs); the graph-aware `graphify-kit:Explore` agent ships from `agents/`                                                         |
| `scripts/`                | Portable sync + worktree-seeding scripts; setup copies them into `<repo>/scripts/graphify/` so worktree bootstrap is committed with the repo, not coupled to a plugin cache path                   |

## Worktree managers

Seeding works with any worktree tool: Conductor is auto-detected (env vars honored, setup wires `.conductor/setup.sh`), and plain `git worktree` users run `bash scripts/graphify/worktree-setup.sh` once per worktree (or wire it into direnv / a post-checkout hook). A worktree seeds from the main checkout's graph in seconds — no rebuild, no LLM.

## Docs sync

`/graphify-kit:sync-docs` indexes two source kinds: in-repo markdown the AST walk already sees, and the project's **Docs Root** — `.docs/vault/`, discovered from the `## docs configuration` fenced JSON block (`{ project, provider, store }`) in `CLAUDE.local.md` (or `CLAUDE.md`). For local providers (filesystem, Obsidian) the Docs Root is indexed **directly through the symlink** — no `vault-mirror/` copy, no rsync, no gitignore bookkeeping; a sanity gate verifies the CLI traversed the symlink and falls back to a thin internal copy under `.docs/` only if it didn't. The legacy `## spec configuration` vault block still works, with a deprecation note pointing at `/docs-hub:setup`.

## The flow, one line

**symbol directory → `explain` → targeted Read** — harvest real names, map relationships in ~15 lines per question, read only for line-level evidence. `affected` before refactors; `path` to connect two known symbols; grep stays for string literals and exhaustive enumeration.

## Maintenance

- AST layer: synced automatically by the session hooks (zero LLM, zero attention).
- Docs semantics (in-repo + Docs Root): `/graphify-kit:sync-docs`, on demand.
- After editing `.graphifyignore`: re-run `/graphify-kit:setup` (from-scratch rebuild required; the semantic cache survives and re-merges at zero cost).
- Something off: `/graphify-kit:doctor`.
- graphify CLI upgrades: `uv tool upgrade graphifyy`, then `/graphify-kit:doctor`; rebuild via setup when release notes mention extractor improvements.
