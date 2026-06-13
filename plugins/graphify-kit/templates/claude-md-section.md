<!-- graphify-kit:begin — managed by /graphify-kit:setup; edits inside this block are overwritten on re-run -->

## Graphify (knowledge graph)

`graphify-out/graph.json` indexes this repo (AST symbols + indexed docs). It is a **symbol navigator, not a search engine** — it complements grep, it does not replace it. Workflow: harvest real symbol names (symbol directory below, or one scoped Grep) → graphify to map relationships → Read only the files you will modify.

- **Cold start — concept word, no symbol yet?** List real names straight from the graph instead of guessing:
  `jq -r --arg t "<lowercase-term>" '.nodes[] | select((.label // "") | ascii_downcase | contains($t)) | ((.label | gsub("\\s+"; " "))[0:60]) + "  " + (.source_file // "?")' graphify-out/graph.json | sort -u`
  One lowercase term returns every symbol/file/doc note whose name contains it — exactly the names `explain` needs. The term is a LITERAL substring, not a regex (`repository` ≠ `repositories`, `\|` alternation matches nothing — one term per run). Run it once per concept; to enumerate what a known FILE contains, `explain` its underscore node ID instead of iterating jq filters.
- `graphify explain "<ExactSymbol>"` — the high-value verb. Returns a symbol's callers, callees, imports, and `file:line` in ~15 lines, far cheaper than reading the files. Also works per file via the underscore node ID (`<parent-dir>_<filename-stem>`, e.g. `explain "repositories_users"` for `src/repositories/users.ts`).
- `graphify affected "<ExactSymbol>"` — reverse-dependency impact: what is affected if X changes (`--depth N` to widen). Use before refactors.
- `graphify path "<SymbolA>" "<SymbolB>"` — how two known symbols connect.
- Matcher quirks: matching is case-folded substring over node labels. CamelCase symbols match; hyphenated file names do NOT (use a contained symbol or the underscore ID). A fuzzy name silently matches the wrong node — always verify the returned `Source:` path before trusting the answer.
- Never `explain` a guessed name — only names observed in symbol-directory, grep, or Read output. Opening a session with a chain of explains on guessed names is the classic failure: misses pile up and the graph gets abandoned. `No node matching` means your name is wrong, NOT that the graph lacks the area.
- **Re-entry is mandatory**: the moment grep/find output shows a function/class/component name, the next relationship question (who calls it, where is it used, what does it touch) goes to `graphify explain` — not another grep, not a full-file Read.
- **Evidence discipline**: cite only `file:line` you actually observed via `explain`/Read. Before asserting a cross-cutting behavior — caching, cache-busting, invalidation, a side effect, an auth check living elsewhere — `explain` or Read the code that implements it. Don't infer such a claim into a `file:line`-grounded answer; an unverified aside is the failure mode this protocol exists to prevent.
- Do not use `graphify query` — it has no semantic matching; it BFS-floods 2 hops from ~3 substring-matched seed nodes and returns their _neighborhoods_, never the matching names. The jq symbol directory replaces it.
- Triage with the graph BEFORE dispatching Explore or any search agent: symbol directory or one scoped Grep for real names, then `graphify explain`/`affected` yourself — that answers most relationship questions outright in main context. Dispatch Explore only for what the graph cannot answer (exhaustive enumeration, string-literal hunts).
- Subagents: `Explore` is overridden project-locally (`.claude/agents/explore.md`) with the graph protocol baked in. Other custom agent types do NOT inherit CLAUDE.md (general-purpose does), and PreToolUse hook nudges do NOT reach subagent tool calls — when dispatching any other agent toward code work, prepend the graph protocol to its prompt, and when you already know the relevant symbol, embed the ready-to-run `graphify explain "<Symbol>"` command.
- Graph freshness is automated (session hooks sync the AST layer; zero LLM). Never run `graphify update`/`extract` manually. After changing `.graphifyignore`, a from-scratch rebuild is required (re-run `/graphify-kit:setup`). Check graph health with `/graphify-kit:doctor`.
- Never commit `graphify-out/` or `.graphifyignore` unless this project explicitly decides to share them.

<!-- graphify-kit:end -->
