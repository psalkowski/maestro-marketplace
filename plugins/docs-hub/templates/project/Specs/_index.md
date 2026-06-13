---
type: note
---
# Specs

Finalised feature specs ready to plan against. Promote from `Brainstorms/` when the shape is stable.

## Frontmatter template (copy for a new spec)

```yaml
---
type: spec
status: draft                       # draft | active | done | superseded
date: YYYY-MM-DD
feature: "[[<feature-slug>]]"       # Feature hub; null for infra/tooling specs
contexts: ["[[<context-slug>]]"]    # glossaries this spec relies on; [] if none
related: ["[[<feature-slug>]]"]     # related features; [] if none
ships-with: "[[<feature-slug>]]"    # co-shipped feature; null if none
---
```

Links point child → parent. Reference glossary terms in the body as `[[<context-slug>#Term]]`. Specs from `spec:plan` carry a `-design` suffix and a `## Design` section.
