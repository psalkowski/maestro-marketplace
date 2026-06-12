# Plan format — lean handoff artifact

A plan doc exists for exactly one reason: to let a session that wasn't present at planning execute the work. It is **ephemeral** — nobody reads it after merge. The spec is the durable document; the plan is scaffolding. Optimize for token economy.

## What a plan carries

**Header:** goal (one sentence), `implements: [[<spec-note>]]` frontmatter link, and — verbatim from the spec — the `## Design` reference if there is one.

**Execution model policy** — paste the template below.

**Conventions** — a handful of lines that apply to every task: commit format, TDD expectation, `.claude/rules/*.md` files to honor.

**Key facts** — copy from the spec and extend with anything new found while planning: `file:line` anchors, existing helpers, persistence paths, gotchas. Executors get dispatched with these; they should never re-derive them.

**Tasks** — for each task:

- **Intent** — 2–4 sentences: what changes and why
- **Files** — create/modify, exact paths
- **Constraints / invariants** that aren't obvious from the intent
- **Acceptance criteria** — checkable
- **Test cases described in prose** (input → expected behaviour), not coded
- **Verification** — the _targeted_ command(s) only
- **Executor** — pin from the policy table

## What a plan must NOT contain

- **Implementation code.** No fenced blocks of the code to be written — writing it is the executor's job, and code in the plan gets paid for twice (planner output, executor re-emission). Exception: a snippet is allowed only when exactness _is_ the requirement (a config key, an exact command, a wire format) — max ~5 lines.
- **Full test files.** Describe the cases; the executor writes them.
- **Restated spec content** beyond Key facts — link to the spec, don't duplicate it.
- **Keystroke-level steps** ("write the failing test, run it, watch it fail…") — state TDD once under Conventions.

## Execution model policy — template

```markdown
## Execution model policy

Dispatch by **explicit** `subagent_type` (never by description matching); model + effort pins live in the agent definitions.

| Work                                                                                          | `subagent_type`            |
| --------------------------------------------------------------------------------------------- | -------------------------- |
| Authorship (default — anything that writes or changes code)                                   | `spec:plan-executor`       |
| No-authorship chores (run verification, regenerate assets, exact-spec mechanical edits)       | `spec:plan-executor-light` |
| Escalation only — a task that failed, is stuck on a red test, or uncovered cross-file fallout | `spec:plan-executor-heavy` |

Routing is **escalation-only**: never downgrade a task below its pin; escalate on evidence (a failed attempt), not prediction.

**Review gate:** after every authorship task, dispatch `spec:plan-reviewer` on the diff. CHANGES-NEEDED → re-dispatch the **same** executor with the ordered fix list, review again. APPROVE → next task. Light tasks skip review.

**Verification policy:** per-task verification is **targeted tests only**. Full verification (build + lint + full test suite) is its own **final task** — run once, before PR/sign-off, never between tasks.
```

The final task of every plan is the full-verification task.

## Self-review (after writing the plan)

1. **Spec coverage** — every spec requirement maps to a task; list gaps.
2. **Code scan** — any fenced implementation block over ~5 lines is a plan failure; replace it with intent + acceptance criteria.
3. **Consistency** — names, paths, and signatures referenced in later tasks match earlier tasks.
4. **Final task** is the full-verification task, and no other task runs the full suite.
