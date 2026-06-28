#!/usr/bin/env bash
# PreToolUse(Read|Glob|Grep) hook for a repo with a graphify graph:
#  - DENY a Grep TOOL by-role symbol search (redirect to graphify affected/explain).
#  - NUDGE whole-file code reads / other greps toward explain, without blocking.
# Decision logic lives in gk-classify-read.py (unit-tested). Fires only when
# graphify-out/graph.json exists; emits JSON on stdout, always exits 0.
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "${CLAUDE_PROJECT_DIR:-$PWD}" 2>/dev/null || exit 0
[ -f graphify-out/graph.json ] || exit 0
python3 "$DIR/gk-classify-read.py" 2>/dev/null || true
exit 0
