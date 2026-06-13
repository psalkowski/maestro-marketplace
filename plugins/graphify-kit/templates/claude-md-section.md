<!-- graphify-kit:begin (managed; re-run /graphify-kit:setup to refresh) -->

## Graphify (knowledge graph)

`graphify-out/graph.json` is a symbol graph of this repo (AST symbols + indexed docs) — a navigator that complements grep, not a search engine that replaces it. Best with a capable main model; delegate broad navigation to the `Explore` agent, which carries the full protocol.

- **Map a known symbol with the graph, not `grep -r` or whole-file reads:** `graphify explain "<Symbol>"` (definition, callers, callees, imports, `file:line` in ~15 lines), `graphify affected "<Symbol>"` (reverse-dependency impact, `--depth N` to widen). Per file: the underscore node ID `<dir>_<stem>` (e.g. `repositories_users`). `graphify path "<A>" "<B>"` connects two known symbols.
- **`explain` any symbol — never `grep -n`/`find` for one:** `graphify explain "<S>"` returns the definition `file:line` for ANY symbol, including one surfaced mid-trace (a function inside another `explain`'s output, a symbol not in your concept harvest). So to locate where something is defined or used, `explain`/`affected` it — never `grep -n` a symbol's line or `find`/`ls` a file by role. (Fine: a literal-string grep — a UI label or error message — in one named file; and `find`/Read for non-code assets the graph skips: SQL migrations, framework templates, styles.)
- **No symbol yet (a concept word)?** Harvest names from the graph instead of guessing:
  `jq -r --arg t "<lowercase-term>" '.nodes[] | select((.label // "") | ascii_downcase | contains($t)) | ((.label | gsub("\\s+"; " "))[0:60]) + "  " + (.source_file // "?") + "  " + (.source_location // "?")' graphify-out/graph.json | sort -u`
  Columns are `symbol  file  line`, one LITERAL lowercase substring per run (not a regex — `\|` matches nothing). Read the whole list; don't `head`/`tail`-truncate it. Never `graphify query` (it floods seed neighbours, not the matching names).
- **Batch to save turns:** when you already hold several names (the directory lists every layer at once — UI, route, repo), issue the independent `explain`/`affected` calls in one step (`graphify explain "A"; graphify explain "B"` in one command, or parallel tool calls), then Read the cited files in one parallel batch — not one per turn.
- Verify the `Source:` path an `explain` returns — a fuzzy name silently hits the wrong node; `No node matching` means a wrong name, not missing coverage, so never `explain` a guessed name. Cite only `file:line` you actually observed.
- **Dispatching an agent toward code?** It does NOT inherit this section — prepend this protocol (and a ready-to-run `graphify explain "<Symbol>"` when you already know the symbol). Treat its findings as a map to spot-check, not a vetted answer.
- Freshness is automated (session hooks sync the AST layer; zero LLM) — never run `graphify update`/`extract` by hand. After a `.graphifyignore` change, rebuild via `/graphify-kit:setup`; check health with `/graphify-kit:doctor`. Never commit `graphify-out/` or `.graphifyignore` unless the project explicitly shares them.

<!-- graphify-kit:end -->
