#!/usr/bin/env bash
# PreToolUse(Bash) hook for a repo with a graphify graph:
#  - DENY an unambiguous by-role search (find -name "*role*", recursive CamelCase
#    grep) and redirect to the on-graph path filter / `graphify affected`.
#  - NUDGE other grep/find (ext-sweeps, string-literal greps) without blocking.
# Decision logic lives in gk-classify-bash.py (unit-tested). Fires only when
# graphify-out/graph.json exists; emits JSON on stdout, always exits 0.
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "${CLAUDE_PROJECT_DIR:-$PWD}" 2>/dev/null || exit 0
[ -f graphify-out/graph.json ] || exit 0
python3 "$DIR/gk-classify-bash.py" 2>/dev/null || true
exit 0
