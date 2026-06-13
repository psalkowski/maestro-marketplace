<!-- graphify-kit:begin (managed; re-run /graphify-kit:setup to refresh) -->

## Graphify (knowledge graph)

`graphify-out/graph.json` indexes this repo (AST symbols + indexed docs). It is a **symbol navigator, not a search engine** — it complements grep, it does not replace it. Workflow: harvest a real symbol name → `graphify` to map relationships → Read only the files you'll change.

- **No symbol yet?** Harvest real names from the graph instead of guessing:
  `jq -r --arg t "<lowercase-term>" '.nodes[] | select((.label // "") | ascii_downcase | contains($t)) | ((.label | gsub("\\s+"; " "))[0:60]) + "  " + (.source_file // "?")' graphify-out/graph.json | sort -u`
  One LITERAL lowercase substring per run (not a regex); the second column is the file path, so don't re-`find` it.
- `graphify explain "<ExactSymbol>"` — callers, callees, imports, and `file:line` in ~15 lines (far cheaper than reading the files). Also works per file via the underscore node ID (`<parent-dir>_<filename-stem>`, e.g. `repositories_users`).
- `graphify affected "<ExactSymbol>"` — reverse-dependency impact before a refactor (`--depth N` to widen). `graphify path "<A>" "<B>"` — how two known symbols connect.
- Matching is case-folded substring over node labels: CamelCase matches, hyphenated file names do NOT (use a contained symbol or the underscore ID); a fuzzy name silently hits the wrong node, so verify the returned `Source:` path. `No node matching` means the name is wrong, not that the graph lacks the area — never `explain` a guessed name.
- **Re-entry:** the moment grep/Read surfaces a function/class/component name, the next relationship question goes to `graphify explain "<thatName>"` — not another grep, not a full-file Read. A _second_ grep on a file you just hit (to enumerate its exports) is the same trigger — `explain` its underscore node ID instead, so you never grep a file twice.
- **Need a file you can only describe, not name** (the impl behind an interface, the next hop in a trace)? Ask the graph: `graphify affected "<Interface>"` lists its dependents (the implementor is usually there), or re-run the `jq` harvest for the impl's scent (`endpoints`/`client`/`service`/`provider`) — and don't `head`-truncate it. `find`/`grep -r` to locate a file by its _role_ abandons the graph mid-trace and balloons cost — measured worse than no graph at all. (`find`/Glob stay correct for filename-pattern sweeps and exhaustive enumeration, never for finding a file by its role.)
- **Evidence discipline:** cite only `file:line` you actually observed via `explain`/Read. Before asserting a cross-cutting behavior (caching, a side effect, an auth check living elsewhere), `explain` or Read the code that implements it — don't infer it into a grounded answer. For a symbol's _definition_ line use `explain`/the directory, not a grep hit that may land on a call site.
- **Code only, not templates/styles:** the graph indexes `.ts`/`.js`/etc., NOT Angular `.html`/`.scss` or Vue SFC `<template>`. `explain` resolves a component _class_; the logic for _which view renders_ (`*ngIf`/`@if`, bindings) lives in the sibling template — grep/Read it directly (correct here, not a fallback).
- Never use `graphify query` — it floods seed neighborhoods, not the matching names; the jq directory replaces it.
- **Dispatching an agent toward code work?** It won't inherit this section — prepend this protocol (plus a ready-to-run `graphify explain "<Symbol>"` when you already know the symbol). Treat its returned findings as a map to spot-check — verify the load-bearing `file:line` before asserting — not a vetted answer.
- Freshness is automated (session hooks sync the AST layer; zero LLM) — never run `graphify update`/`extract` by hand. After a `.graphifyignore` change, rebuild via `/graphify-kit:setup`; check health with `/graphify-kit:doctor`.
- Never commit `graphify-out/` or `.graphifyignore` unless the project explicitly decides to share them.

<!-- graphify-kit:end -->
