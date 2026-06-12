# Execution modes — deciding how to run the work

Pick after the spec (and optional plan doc) is approved. Announce the choice in one sentence; the user can override.

## 1. Same-session (default)

Execute right here: derive the task list from the spec, enter plan mode, get approval, implement.

**Why it's the default:** the planning context — explored files, key facts, grilling outcomes — is reused at ~0.1× cost via prompt cache. A handoff pays full price to rebuild that context in a fresh session and loses the tacit parts entirely.

**Choose when** execution fits comfortably in the current context: roughly under ~15–20 working turns, and the context isn't already bloated.

**Keep it lean:** bulk file reading and test runs go to subagents; don't pull whole files into this context when an executor can read them in a throwaway one.

## 2. Same-session, subagent-driven

This session stays the orchestrator and dispatches per-task executors using the same policy table as `spec:execute` (authorship → `spec:plan-executor`, chores → `spec:plan-executor-light`, escalation → `spec:plan-executor-heavy`, review gate via `spec:plan-reviewer`).

**Choose when** tasks are independent enough to parallelize, heavy file churn would bloat this context, or the context is already heavy from planning.

No plan doc required — write each dispatch prompt as a self-contained brief: intent, files, key facts, constraints, acceptance criteria.

## 3. Fresh-session handoff (`spec:execute`)

Requires a plan doc (Phase 5).

**Choose when** the work spans sessions or days, execution is deferred ("run it tonight"), or the current context is near its limit.

**Economics, for calibration:** the handoff costs plan-writing output plus full-price re-ingestion in the new session (typically 30–100k+ token-equivalents). Carrying this session's planning context costs ~0.1× of it per further turn. Crossover is around 15+ turns of remaining work — below that, stay in-session.

## Every mode

- **Verification policy:** targeted tests per task; full build + lint + suite **once** at the end, or when the user asks for a PR.
- Escalation-only routing; never silently downgrade work to a cheaper model.
