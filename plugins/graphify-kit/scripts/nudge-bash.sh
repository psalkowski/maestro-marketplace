#!/usr/bin/env bash
# PreToolUse(Bash) nudge: when the agent reaches for grep/find in a repo that
# has a graph, remind it to re-enter graphify the moment it has a symbol name.
# Fires only when graphify-out/graph.json exists; never blocks the tool call.
cd "${CLAUDE_PROJECT_DIR:-$PWD}" 2>/dev/null || exit 0
[ -f graphify-out/graph.json ] || exit 0

CMD=$(python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('tool_input',d).get('command',''))" 2>/dev/null || true)

case "$CMD" in
  *graphify*) exit 0 ;;
esac

case "$CMD" in
  *grep*|*rg\ *|*ripgrep*|*find\ *|*fd\ *|*ack\ *|*ag\ *)
    printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"graphify: LOCATE code through the graph, not this grep. Flow: no symbol yet → run the jq symbol directory (harvests real names + their file:line); have a name → `graphify explain \"<Name>\"` (definition, callers, callees, imports); every usage / \"where is X used\" / blast radius → `graphify affected \"<Name>\"` (this replaces `grep -rn`); how two symbols connect → `graphify path \"<A>\" \"<B>\"`. Verify the returned Source: path; never `graphify query` (it floods). Grep is ONLY for raw text the graph cannot index — template HTML/markup, a string literal, a log line — never a symbol, its definition, or its usages."}}'
    ;;
esac
exit 0
