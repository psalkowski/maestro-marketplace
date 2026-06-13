---
type: note
---

# {{PROJECT_NAME}}

{{DESCRIPTION}}

Repo: `{{REPO}}`

## Folders

- **Features/** — backlog of candidate features, one short file each; pick → brainstorm → spec → plan
- **Brainstorms/** — `spec:plan` exploratory output, thinking that hasn't reached spec stage
- **Specs/** — finalised specs ready for implementation
- **Plans/** — `spec:plan` handoff output, lean per-task scaffolding for cross-session execution
- **Contexts/** — grill-with-docs glossaries, one note per bounded context, mapped by `Contexts/_index.md`
- **ADRs/** — grill-with-docs architecture decision records, `NNNN-<slug>.md`
- **Notes/** — WIP, meeting notes, scratch

## Frontmatter conventions

Every note carries `type` (`feature | brainstorm | spec | plan | context | adr | note`). Content notes carry the **full key set for their type** (copy the template in each folder's `_index.md`); index/map notes (`type: note`) carry only `type`. Keys are always present even when empty — an empty scalar link is `null`, an empty list of links is `[]` (e.g. a tooling spec with no product feature has `feature: null`, `contexts: []`). `status` values vary by type — workflow notes use `draft | active | done | superseded`, feature backlog notes use their maturity (`mvp | post-mvp | deferred`). Relations are **wikilinks** in frontmatter so they resolve in graph + backlinks in tools that support them. Links point child → parent (plan → spec → feature; any doc → context); the reverse is free via backlinks, so no reciprocal fields.

- **spec**: `feature`, `contexts`, `related`, `ships-with`
- **plan**: `feature`, `implements` (→ spec), `contexts`
- **context**: `context` (slug), optional `related-contexts`
- **adr**: `feature`, `contexts`, `status`
- **feature**: hub — no up-links; gathers backlinks
