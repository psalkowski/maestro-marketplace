# spec (v0.3.0)

Provider-agnostic spec workflow for Claude Code. **`spec:plan` is the single front door** for feature work: it brainstorms (one-question-at-a-time), grills terminology against the project glossary, writes a durable **spec**, and then *decides* — based on the size of the work — whether a lean plan doc is needed and which execution mode to use (same-session by default). `spec:execute` runs handed-off plans in a fresh session through pinned subagents.

Self-contained — no superpowers dependency. Storage-agnostic: all docs are read and written with plain file tools (`Read`/`Write`/`Edit`/`Glob`) against the **Docs Root** (`.docs/vault/`), which `docs-hub` wires to a filesystem store, an Obsidian vault, or (later) a remote provider. This plugin never knows or cares which.

## Components

| Kind | Name | Role |
|---|---|---|
| skill | `spec:plan` | front door: understand → grill (`grill-with-docs`) → (design skill) → **spec** in the Docs Root → optional lean plan doc → execution-mode decision |
| skill | `spec:execute` | fresh-session plan runner: pinned subagents, per-task review gates, escalation-only routing |
| agent | `spec:plan-executor` | Fable, `high` — default executor for authorship tasks; receives intent + facts, writes the code itself |
| agent | `spec:plan-executor-light` | Sonnet, `medium` — no-authorship chores (verification runs, asset regeneration, exact-spec edits) |
| agent | `spec:plan-executor-heavy` | Fable, `xhigh` — escalation target: failed/stuck tasks, cross-cutting fallout |
| agent | `spec:plan-reviewer` | Opus, `high`, read-only — reviews each authorship task's diff against intent + acceptance criteria |
| command | `/spec:setup` | verifies the docs configuration exists, manages the spec-specific config (`designSkill`) |

## Design principles

- **Specs are durable, plans are scaffolding.** The spec carries intent, design decisions, and *key facts* (`file:line` anchors, existing helpers). A plan doc exists only when execution must cross a session boundary — and it carries **no implementation code**; executors write the code.
- **Same-session execution by default.** The planning context is reused at cache prices; handing off to a fresh session pays full price to rebuild it. Handoff is for multi-day work, deferred runs, and near-full contexts.
- **Escalation-only routing.** Tasks never get silently downgraded to a cheaper model; they escalate on evidence (a failed attempt).
- **Verification once.** Per-task verification is targeted tests only; the full build + lint + suite runs as the plan's final task (or pre-PR), never between tasks.
- **Storage belongs to docs-hub.** This plugin consumes the `## docs configuration` block and the Docs Root symlink; it owns no provider logic. The legacy pre-write guard is gone by design: the symlink pins the exact store path, so plain file tools can never write to the wrong place (ADR 0001 in the project docs).

## Configuration

Two blocks in `CLAUDE.local.md`:

- **`## docs configuration`** — owned by `docs-hub` (`/docs-hub:setup` writes it): `{ "project", "provider", "store" }`. Required; the skills STOP without it.
- **`## spec configuration`** — owned by this plugin (`/spec:setup` writes it), minimal and optional:

```json
{
  "designSkill": "your-design-skill"
}
```

Omit the block entirely when the project has no design skill — `spec:plan` skips the design step (and says so).

## Conventions live in the docs, not the skills

Each Docs Root folder's `_index.md` documents its purpose and the frontmatter template for notes in it. The skills **read the folder's `_index.md` before creating a note** and copy its template — so the note schema is owned by the project docs and stays per-project customizable.

See the repo root `README.md` for prerequisites and install.
