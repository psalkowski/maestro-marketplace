# spec

Vault-backed spec workflow for Claude Code. **`spec:plan` is the single front door** for feature work: it brainstorms (one-question-at-a-time), grills terminology against the vault, writes a durable **spec**, and then *decides* — based on the size of the work — whether a lean plan doc is needed and which execution mode to use (same-session by default). `spec:execute` runs handed-off plans in a fresh session through pinned subagents.

Self-contained — no superpowers dependency. Generic and config-driven: per-project settings live in a JSON block in `CLAUDE.local.md`.

## Components

| Kind | Name | Role |
|---|---|---|
| skill | `spec:plan` | front door: understand → grill (`grill-with-docs`) → (design skill) → **spec** in the vault → optional lean plan doc → execution-mode decision |
| skill | `spec:execute` | fresh-session plan runner: pinned subagents, per-task review gates, escalation-only routing |
| agent | `spec:plan-executor` | Fable, `high` — default executor for authorship tasks; receives intent + facts, writes the code itself |
| agent | `spec:plan-executor-light` | Sonnet, `medium` — no-authorship chores (verification runs, asset regeneration, exact-spec edits) |
| agent | `spec:plan-executor-heavy` | Fable, `xhigh` — escalation target: failed/stuck tasks, cross-cutting fallout |
| agent | `spec:plan-reviewer` | Opus, `high`, read-only — reviews each authorship task's diff against intent + acceptance criteria |
| command | `/spec:setup` | writes config + scaffolds the vault (idempotent) |
| templates | `templates/vault`, `templates/project` | the Obsidian vault skeleton `/spec:setup` materializes |

## Design principles

- **Specs are durable, plans are scaffolding.** The spec carries intent, design decisions, and *key facts* (`file:line` anchors, existing helpers). A plan doc exists only when execution must cross a session boundary — and it carries **no implementation code**; executors write the code.
- **Same-session execution by default.** The planning context is reused at cache prices; handing off to a fresh session pays full price to rebuild it. Handoff is for multi-day work, deferred runs, and near-full contexts.
- **Escalation-only routing.** Tasks never get silently downgraded to a cheaper model; they escalate on evidence (a failed attempt).
- **Verification once.** Per-task verification is targeted tests only; the full build + lint + suite runs as the plan's final task (or pre-PR), never between tasks.

## Configuration

`/spec:setup` writes this into `CLAUDE.local.md` under `## spec configuration`:

```json
{
  "project": "your-repo",
  "vault": { "name": "YourVault", "root": "/Users/you/Documents/Vault", "subpath": "Projects/YourVault" },
  "designSkill": "your-design-skill"
}
```

- `vault.subpath` is **required** — the project's space inside the vault.
- `designSkill` is **optional** — omit it and `spec:plan` skips the design step (and says so).

## Conventions live in the vault, not the skills

Each vault folder's `_index.md` documents its purpose and the frontmatter template for notes in it. The skills **read the folder's `_index.md` before creating a note** and copy its template — so the note schema is owned by the vault and stays per-project customizable.

See the repo root `README.md` for prerequisites and install.
