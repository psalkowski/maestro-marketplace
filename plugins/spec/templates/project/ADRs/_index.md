---
type: note
---
# ADRs

Architecture Decision Records from grill-with-docs. One file per decision, `NNNN-<slug>.md`, numbered by scanning this folder for the highest `NNNN` and incrementing. Body keeps the grill-with-docs `ADR-FORMAT.md` shape — short (1–3 sentences); the value is recording THAT a decision was made and WHY.

## Frontmatter template (copy for a new ADR)

```yaml
---
type: adr
status: accepted                    # proposed | accepted | deprecated | superseded by [[NNNN-slug]]
date: YYYY-MM-DD
feature: "[[<feature-slug>]]"       # the feature this decision concerns; null if cross-cutting
contexts: ["[[<context-slug>]]"]    # glossaries it touches; [] if none
---
```

Reference an ADR elsewhere as `[[NNNN-slug]]`.

## ADRs

<!-- one bullet per ADR: [[NNNN-slug]] — the decision, in a sentence -->
