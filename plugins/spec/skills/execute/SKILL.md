---
description: Use when executing an implementation plan stored in the project's Docs Root in a fresh session, or when the user invokes /spec:execute. Subagent-driven with pinned models, per-task review gates, and escalation-only routing.
---

# spec:execute

Runs a plan from the Docs Root task-by-task through pinned subagents. Self-contained — no superpowers skills required. This is the **fresh-session handoff** path; if you are still in the session that wrote the spec, prefer same-session execution (see `spec:plan` → execution modes).

## Docs protocol (read this first)

1. **Resolve the Docs Configuration.** Read the fenced ```json under `## docs configuration` in `CLAUDE.local.md` — it provides `project`, `provider`, and `store`. **If the block is absent, STOP** and tell the user to run `/docs-hub:setup`.
2. **All doc operations are plain file tools.** Read and write docs with `Read`/`Write`/`Edit`/`Glob` against the Docs Root: `.docs/vault/...`. No MCP tools, no size workarounds — plain `Read` has no truncation limits.
3. **Respect `_index.md` on every new note** — copy the target folder's frontmatter template; never invent frontmatter.
4. **Missing or dangling Docs Root.** If `.docs/vault` is missing or a dangling symlink, **STOP** and point the user at `/docs-hub:setup` (or conductor-kit worktree seeding in a Conductor workspace).

For future remote providers (Notion, GDrive), the Docs Root is a read-only mirror: write via the driver API and re-sync (ADR 0001).

## Workflow

1. **Load the plan.** Read the plan from `.docs/vault/Plans/` and its linked spec's **Key facts** section. The plan's **Execution model policy** table is the routing source of truth. Agents are namespaced — use `spec:plan-executor`, `spec:plan-executor-light`, `spec:plan-executor-heavy`, `spec:plan-reviewer`; map bare or legacy names from older plans onto these.

2. **Track tasks.** Create one task-list item per plan task; mark in_progress/completed as you go.

3. **Dispatch loop — per task:**

   - Dispatch by **explicit** `subagent_type` from the policy table — never auto-select by description. The dispatch prompt must be self-contained: the task's full text, the plan's Conventions, and the relevant Key facts. Executors write the code themselves; do not write it for them and do not expect the plan to contain it.
   - **Review gate (authorship tasks only):** when the executor returns, dispatch `spec:plan-reviewer` on the task's diff. On **CHANGES-NEEDED**, re-dispatch the **same** executor with the ordered fix list, then review again. On **APPROVE**, move on. Light (no-authorship) tasks skip review.
   - **Escalation-only routing:** a task that failed, is stuck on a red test, or uncovered cross-file fallout gets re-dispatched to `spec:plan-executor-heavy` with the failure evidence attached. Never downgrade a task below its pin, and never "fix it quickly" in the orchestrator — that bypasses the review gate.

4. **Honour stop gates.** If the plan says "stop and ask" before a task, stop and ask.

5. **Verification policy.** Executors run **targeted tests only**. The full verification (build + lint + full suite) is the plan's **final task**, run once — do not insert extra full runs between tasks; they make execution take ages for no added signal.

6. **Keep the orchestrator lean.** Do not read changed files into this context — work from executor and reviewer reports. Relay a one-line progress note to the user after each task.

## Requires

The agents `spec:plan-executor`, `spec:plan-executor-light`, `spec:plan-executor-heavy`, `spec:plan-reviewer` (ship with this plugin) and a configured Docs Root (via `docs-hub:setup`).
