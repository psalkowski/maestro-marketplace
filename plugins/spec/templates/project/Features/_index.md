---
type: note
---
# Feature Backlog

One file per candidate feature. Pick one, brainstorm via `spec:brainstorm`, spec to `Specs/`, plan to `Plans/`.

Status legend: `mvp` = first release; `post-mvp` = roadmap, anchored on MVP; `deferred` = valuable but not until the substance underneath exists.

## MVP

<!-- one bullet per feature: [[feature-slug]] — one-line description -->

## Post-MVP

<!-- roadmap features, anchored on MVP -->

## Deferred

<!-- valuable but blocked on something else -->

## Frontmatter template (copy for a new feature)

```yaml
---
type: feature
status: mvp        # mvp | post-mvp | deferred
source: new        # new | migration
date: YYYY-MM-DD
---
```

Features are hubs — no up-links in frontmatter. Specs/plans/brainstorms link UP via `feature: "[[<this-feature-slug>]]"`, so this note's backlinks gather them. List related features in a body `## Related` section with `[[wikilinks]]`. Add each new feature to the appropriate section above.
