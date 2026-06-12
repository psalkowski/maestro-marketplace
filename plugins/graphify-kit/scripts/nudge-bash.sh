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
    printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"graphify: once grep gives you a symbol name, switch — `graphify explain \"<ExactSymbol>\"` maps callers/callees/imports with file:line in ~15 lines; `graphify affected \"<Symbol>\"` shows change impact. Verify the returned Source: path. No symbol yet? Run the symbol directory from the Graphify section of CLAUDE.md to enumerate real names. Never run `graphify query` (BFS flood, returns neighborhoods, not matches). grep stays right for string literals and exhaustive enumeration."}}'
    ;;
esac
exit 0
