---
description: Use for any non-trivial feature work — scoping, designing, specifying, or planning a feature, page, component, or behaviour change — or when the user invokes /spec:plan. Produces a durable spec in the project's Docs Root; adds a plan doc and picks an execution mode only when the size of the work warrants it.
---

# spec:plan

The single front door for feature work. It always produces a **Spec** — the durable intent + design document — in the Docs Root. A separate **Plan doc** and the execution mode are decisions this skill makes based on the size of the work; most features need neither a plan doc nor a session handoff.

Self-contained: no superpowers skills required.

## Docs protocol (read this first)

1. **Resolve the Docs Configuration.** Read the fenced ```json under `## docs configuration` in `CLAUDE.local.md` — it provides `project`, `provider`, and `store`. **If the block is absent, STOP** and tell the user to run `/docs-hub:setup`.
2. **All doc operations are plain file tools.** Read, write, and edit docs with `Read`/`Write`/`Edit`/`Glob` against the Docs Root: `.docs/vault/...`. No MCP tools, no size workarounds — plain `Read` has no truncation limits.
3. **Respect `_index.md` on every new note.** Before creating a note in any folder, read that folder's `_index.md` and **copy its frontmatter template** — never invent frontmatter. If the folder keeps a list, add the new note's entry.
4. **Missing or dangling Docs Root.** If `.docs/vault` is missing or a dangling symlink (`test -d` fails through the link), **STOP** and point the user at `/docs-hub:setup` (or conductor-kit worktree seeding in a Conductor workspace) — never write into an unlinked `.docs/`.

For future remote providers (Notion, GDrive), the Docs Root is a read-only mirror: write via the driver API and re-sync (ADR 0001).

The optional `designSkill` (Phase 3) comes from the fenced ```json under `## spec configuration` in `CLAUDE.local.md`, if present.

## Scale check (before anything else)

Trivial work — a bugfix with an obvious cause, a one-file tweak, a mechanical rename — does **not** need this workflow. Say so in one sentence and proceed directly. Use this skill when the work involves design decisions, new behaviour, or touches more than a couple of files.

## Phase 1 — Understand

- Explore project context **through Explore subagents**, not by reading piles of files into this session. The main context must stay lean — execution will usually happen here, and every file you read now is carried for the rest of the session.
- Check `.docs/vault/Features/`, `Specs/`, `ADRs/`, and the relevant `Contexts/` glossary for prior art before asking anything.
- Ask clarifying questions **one at a time** (multiple-choice when possible). Focus: purpose, constraints, success criteria.
- If the request spans multiple independent subsystems, stop and decompose first — one spec per sub-project.
- Propose **2–3 approaches** with trade-offs; lead with your recommendation. YAGNI ruthlessly.

## Phase 2 — Grill

Invoke `grill-with-docs` on the chosen approach — always, not "if terms look unsettled". Its domain docs live in the Docs Root: read `.docs/vault/Contexts/_index.md` first, then only the relevant glossary note(s); resolve terms inline into `.docs/vault/Contexts/<context-slug>.md`; write any ADR to `.docs/vault/ADRs/NNNN-<slug>.md` (number by Glob-scanning `ADRs/` for the highest `NNNN`). Revise the design with whatever the grilling surfaces.

## Phase 3 — Design skill (only if `designSkill` is set)

When `designSkill` names a skill, invoke it **by that name** once the questions are answered — REQUIRED for any feature with a UI surface. Get visual approval and capture the **design reference** it reports (route to run, source file, states shown). If absent or the feature has no rendered surface, skip **and say so**.

## Phase 4 — Write the spec

Write `.docs/vault/Specs/<topic>-design.md` per the folder's `_index.md` template. Scale each section to its complexity:

- **Summary / intent** — what and why, a few sentences
- **Design decisions** — chosen approach, and why not the obvious alternatives
- **Key facts** — everything discovered during exploration an implementer would otherwise re-derive: exact `file:line` anchors, existing helpers, persistence paths, conventions. This is the highest-value section — be generous here.
- **Edge cases / invariants**
- **Acceptance criteria** — checkable statements of done
- **Out of scope**
- **Verification** — how the result will be checked (commands, scenarios)
- **`## Design`** — the design reference verbatim, if Phase 3 produced one

The spec carries **decisions and facts, not implementations**: algorithm steps in prose are good; fenced blocks of the code to be written are not.

**Self-review** (fix inline, no re-review): placeholders, internal contradictions, scope (one plan-able unit?), ambiguity. Then ask the user to review the spec before continuing.

## Phase 5 — Plan doc: usually not

Default: **no plan doc — the spec is enough.** Create `.docs/vault/Plans/YYYY-MM-DD-<slug>.md` ONLY when execution genuinely needs a handoff artifact:

- the work won't fit one session (multi-day, > ~10 substantial tasks), or
- execution is deferred or will run in a fresh session via `spec:execute`, or
- tasks will fan out to parallel subagents that each need a self-contained brief, or
- the user asks for one.

If yes, **read `references/plan-format.md` now** and follow it — plans are lean (no implementation code). Announce the decision in one sentence; the user can override.

## Phase 6 — Pick the execution mode

Read `references/execution-modes.md`, pick same-session (default) / same-session subagent-driven / handoff to `spec:execute`, announce the choice in one sentence, and start (or stop, if execution is deferred).

## Red flags — STOP, you're about to regress

| Rationalization                                                               | Reality                                                                                                              |
| ----------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| "I'll put the implementation code in the plan so the executor can't go wrong" | That pays for the code twice and turns the executor into a typist. Plans carry intent + facts; executors write code. |
| "Terms look settled, I'll skip grill-with-docs"                               | Grill is mandatory — terms get verified against the project glossary in the Docs Root, not assumed.                  |
| "The feature is big, so the plan should be detailed"                          | Big → plan doc, yes. Detailed → no. Lean format always.                                                              |
| "I'll run the full build/lint/test suite after this task"                     | Full verification runs **once at the end** (or pre-PR). Per-task verification is targeted tests only.                |
| "Sonnet is cheaper, I'll dispatch implementation to it"                       | Sonnet (`plan-executor-light`) only takes no-authorship chores. Authorship goes to the default executor.             |
| "I'll read those files myself real quick"                                     | Bulk reading goes to subagents; this context must stay lean for execution.                                           |

## Requires

`grill-with-docs`, a configured Docs Root (via `docs-hub:setup`), and — if configured — the project's `designSkill`. If one is missing, tell the user before relying on the step that needs it.
