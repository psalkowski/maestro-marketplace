---
type: note
---

# Plans

**Optional, ephemeral handoff artifacts** — created by `spec:plan` only when execution needs to cross a session boundary (multi-day work, deferred execution via `spec:execute`, parallel subagent fan-out). Most features skip this folder entirely: the spec is the durable document and execution happens in the planning session.

Plans are **lean**: goal, link to the spec, key facts, an execution-model policy table, and per-task intent + acceptance criteria. They carry **no implementation code** — executors write the code. After the branch merges, set `status: done`; plans are scaffolding, not documentation.

Filename format: `YYYY-MM-DD-<feature-name>.md`

## Frontmatter template (copy for a new plan)

```yaml
---
type: plan
status: draft # draft | active | done | superseded
date: YYYY-MM-DD
feature: "[[<feature-slug>]]" # Feature hub; null for infra/tooling plans
implements: "[[<spec-note-name>]]" # the spec this plan implements (exact note name)
contexts: ["[[<context-slug>]]"] # glossaries this plan relies on; [] if none
---
```

`implements` points to the spec's exact note name — specs use a `-design` suffix so the link stays unambiguous.
