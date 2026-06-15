# conductor-kit (v0.3.0)

Conductor integration for this marketplace's tooling: GUI/terminal-parity **Action Skills**, personal-layer prompt overrides, and generated workspace lifecycle scripts that seed docs and knowledge graphs into every new Conductor workspace, run its start command, and stop its processes on archive.

## Why

Conductor's action buttons (Create PR, Code Review, Fix Errors, …) are driven by prompt text in `settings*.toml`. That has two failure modes: the prompt text drifts per repo, and **terminal mode gets nothing** — the buttons don't exist there, so the behaviors are simply lost. conductor-kit moves each action's behavior into a versioned **Action Skill** and reduces every Conductor prompt to a one-liner that invokes it. The GUI button and a typed `/conductor-kit:create-pr` now run the identical, centrally updated implementation.

The action skills are **grounded in Conductor's real extracted defaults**, not invented from a one-line steer — each playbook adopts Conductor's actual default behavior for that action plus only a few named good-practice additions.

## The actions

Five map to Conductor's native actions; `address-cr` is additive (Conductor has no native "address review" button). There is **no `general` action** — `general` is the user's own preferences surface, which conductor-kit never ships or overrides.

| Skill                              | Conductor prompt key      | Does                                                                                  |
| ---------------------------------- | ------------------------- | ------------------------------------------------------------------------------------- |
| `/conductor-kit:create-pr`         | `create_pr`               | Commit, push, and open the PR; short human description of all workspace-diff changes  |
| `/conductor-kit:code-review`       | `code_review`             | Review the workspace diff; inline `DiffComment`s, else a structured review-store block |
| `/conductor-kit:fix-errors`        | `fix_errors`              | Resolve failing logs through the chain, fix root causes, re-run to green              |
| `/conductor-kit:resolve-conflicts` | `resolve_merge_conflicts` | Forge-aware rebase/merge conflict resolution, preserving both sides' intent           |
| `/conductor-kit:rename-branch`     | `rename_branch`           | Concise kebab-case branch name derived from the diff/work intent                      |
| `/conductor-kit:address-cr`        | *(none — terminal only)*  | Resolve review comments from args/GitHub/the review store and address them            |

## Discovery-first behavior

Each Action Skill is **thin**. Its `SKILL.md` does only four things: (1) resolve inputs via the action's **Fallback Chain**, (2) **discovery-first dispatch** — scan the skills already in session context for one whose *purpose* matches this action's domain (creating PRs, reviewing code, fixing CI, resolving conflicts, naming branches, addressing review comments), excluding conductor-kit's own, and if a clear match exists invoke it with the resolved inputs and stop, (3) only otherwise `Read` the action's `references/playbook.md` (the full default, kept out of context until needed), and (4) resolve outputs via the chain.

Discovery is **by capability, never by skill name** — this is a public marketplace, so a user who brought their own PR-creation or review-addressing skill wins, and conductor-kit names no specific skill as a delegation target. This generalizes the hook Conductor's own Create PR default already uses ("if you have skills for this, they take precedence").

## The Fallback Chain

Every Action Skill resolves its inputs and outputs through **Conductor-native → GitHub → docs/`.context`**, so the same skill behaves identically from a GUI button (Conductor MCP + attached files present) or a terminal command (neither present). Examples:

- **fix-errors logs:** attached → `mcp__conductor__GetTerminalOutput` → `gh run view --log-failed` → reproduce locally.
- **code-review diff:** `mcp__conductor__GetWorkspaceDiff` → `git diff <merge-base> HEAD`.
- **code-review output:** `mcp__conductor__DiffComment` → the Ephemeral Review Store.
- **address-cr comments:** args/attachments → GitHub PR reviews (`gh pr view --json reviews` / `gh api`) → the Ephemeral Review Store.

Each rung degrades gracefully — no PR, or `gh` missing/unauthenticated, simply skips that rung with a note.

## The `.context/reviews` round-trip

When the Conductor MCP isn't present, **code-review** persists its findings to the **Ephemeral Review Store** at `.context/reviews/<branch>.md` (Conductor's gitignored agent-collaboration dir, created if absent) instead of posting inline `DiffComment`s. **address-cr** reads that same file back as one of its comment sources, so a review done in terminal mode closes the loop: review → store → address — entirely offline. The block shape is a shared contract defined once in [`references/review-comment-format.md`](references/review-comment-format.md) and cited by both playbooks (`File:` / `Lines:` / body, plus `Comment ID:` / `Thread ID:` / `Remote URL:` when sourced from GitHub).

## Why the personal layer

Per [ADR 0003](../../.docs/vault/ADRs/0003-conductor-overrides-in-personal-layer.md): the overrides land in `.conductor/settings.local.toml` — per-user, per-repo, uncommitted. A committed "Invoke the conductor-kit … skill" would break every teammate without the plugin, and would reveal personal tooling in shared repos. The trade-off: each machine/repo pair runs `/conductor-kit:setup` once; overrides don't arrive via git.

## Setup

```
/plugin marketplace add psalkowski/maestro-marketplace
/plugin install conductor-kit
```

Then, in each repo (the skill insists on the **main checkout** — run from a worktree it asks whether to target main or stay):

```
/conductor-kit:setup
```

This writes:

- `.conductor/settings.local.toml` — the **five** native prompt overrides plus `scripts.setup` / `scripts.run` / `scripts.archive` wiring, merged idempotently (your other keys, including any `general`, survive untouched).
- `.conductor/setup.sh` — runs in every new Conductor workspace: seeds `.docs/vault` (symlink to the backing store read from the `## docs configuration` block in `CLAUDE.local.md`, **re-pointed if it's stale**), copies `CLAUDE.local.md` from the main checkout if absent, and runs graphify-kit's `scripts/graphify/worktree-setup.sh` when a graph exists on main.
- `.conductor/run.sh` — the workspace's start command, seeded on first creation from the detected stack (`yarn`/`npm`/`pnpm` `start`/`dev`, plus a couple of non-Node stacks; a clear TODO if nothing is detected).
- `.conductor/archive.sh` — stops only the processes started **from that workspace** (matched by argv or working directory), so archiving one workspace never disturbs another's dev servers; shared/external services are left alone.

All are self-contained — no plugin cache paths; all paths quoted (iCloud stores contain spaces) — and kept git-invisible (checked with `git check-ignore`, added to `.git/info/exclude` only when not already covered).

## Regeneration and the project-specific section

Each generated script ends with:

```bash
# --- project-specific (preserved) ---
```

Everything below that marker is yours — `setup.sh` repo bootstrap (env files, `npm install`, database seeds), `run.sh`'s start command, `archive.sh`'s extra teardown. Re-running `/conductor-kit:setup` regenerates only the managed part above the marker and carries your section over byte-for-byte.
