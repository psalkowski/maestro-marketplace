---
type: note
---

# Contexts — Domain Glossary Map

The bounded-context glossaries for this project. This is the single entry point: read it first when resolving domain terminology, then open the specific glossary you need. Each note follows the grill-with-docs `CONTEXT-FORMAT.md` structure (term + 1–2 sentence definition + *Avoid*).

New contexts are created **lazily** — add a glossary note here only when a genuinely distinct bounded context gets grilled.

## Contexts

<!-- one bullet per glossary: [[context-slug]] — what this bounded context covers -->

## Relationships

<!-- how contexts relate / overlap / differ in grain -->

## Frontmatter template (copy for a new context glossary)

```yaml
---
type: context
status: active                            # active | deprecated
date: YYYY-MM-DD
context: <context-slug>                   # bounded-context name (matches filename)
related-contexts: ["[[<other-context>]]"] # [] if none
---
```

Body follows grill-with-docs `CONTEXT-FORMAT.md` (term + definition + *Avoid*). Reference a term elsewhere as `[[<context-slug>#Term]]`, and add the new glossary to the Contexts list above.
