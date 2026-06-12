#!/usr/bin/env bash
# PreToolUse(Read|Glob|Grep) nudge: before whole-file reads of code/docs in a
# repo with a graph, remind the agent that explain is cheaper for mapping a
# known symbol. Fires only when graphify-out/graph.json exists; never blocks.
cd "${CLAUDE_PROJECT_DIR:-$PWD}" 2>/dev/null || exit 0
[ -f graphify-out/graph.json ] || exit 0

HIT=$(python3 -c "import json,sys;d=json.load(sys.stdin);t=d.get('tool_input',d);fp=str(t.get('file_path') or t.get('path') or '').lower().replace(chr(92),'/');pat=str(t.get('pattern') or '').lower();exts=('.py','.js','.ts','.tsx','.jsx','.go','.rs','.java','.rb','.c','.h','.cpp','.hpp','.cc','.cs','.kt','.swift','.php','.scala','.lua','.sh','.md','.rst','.txt','.mdx');sys.stdout.write('1' if 'graphify-out/' not in fp and (d.get('tool_name')=='Grep' or fp.endswith(exts) or pat.endswith(exts)) else '')" 2>/dev/null || true)

if [ "$HIT" = 1 ]; then
  printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"graphify: mapping callers/callees/imports of a known symbol? `graphify explain \"<ExactSymbol>\"` returns them with file:line, cheaper than reading whole files; `graphify affected \"<Symbol>\"` for change impact. Do not use `graphify query` — it BFS-floods seed neighborhoods and never returns the matching names. Read files to modify or debug code."}}'
fi
exit 0
