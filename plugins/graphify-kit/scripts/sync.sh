#!/usr/bin/env bash
# graphify-kit sync: incremental knowledge-graph sync for the current checkout.
#
# repo mode   — cwd has graphify-out/graph.json: diff working tree against the
#               last-indexed SHA baseline, re-extract only changed files via
#               graphify's internal changed_paths API, then re-register into
#               the global graph when cwd is the registered main checkout.
# parent mode — cwd has no graph: sync every globally-registered repo located
#               under cwd (multi-repo sessions).
#
# Zero LLM calls. Always exits 0 (hook-safe).
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HELPER="$SCRIPT_DIR/sync_helper.py"
OUT="${GRAPHIFY_OUT:-graphify-out}"
export PYTHONHASHSEED=0

GRAPHIFY="$(command -v graphify || true)"
[ -n "$GRAPHIFY" ] || GRAPHIFY="$HOME/.local/bin/graphify"
[ -x "$GRAPHIFY" ] || exit 0

# Prefer the interpreter the graph was built with; fall back to the uv tool
# env, then any python3.
PY=""
[ -f "$OUT/.graphify_python" ] && PY="$(cat "$OUT/.graphify_python")"
[ -x "${PY:-/nonexistent}" ] || PY="$HOME/.local/share/uv/tools/graphifyy/bin/python"
[ -x "$PY" ] || PY="$(command -v python3 || true)"
[ -n "$PY" ] || exit 0

MANIFEST="${GRAPHIFY_GLOBAL_MANIFEST:-$HOME/.graphify/global-manifest.json}"

# ---------- parent mode ----------
if [ ! -f "$OUT/graph.json" ]; then
  [ -f "$MANIFEST" ] || exit 0
  jq -r '.. | objects | .source_path? // empty' "$MANIFEST" 2>/dev/null | sort -u | \
  while IFS= read -r SRC; do
    ROOT="${SRC%/graphify-out/graph.json}"
    case "$ROOT" in
      "$PWD"/*)
        if [ -d "$ROOT" ]; then
          ( cd "$ROOT" && bash "$SCRIPT_DIR/sync.sh" )
        fi
        ;;
    esac
  done
  exit 0
fi

# ---------- repo mode ----------
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

MARKER="$OUT/.graphify-baseline-sha"
HEAD_SHA="$(git rev-parse HEAD 2>/dev/null)" || exit 0

if [ ! -f "$MARKER" ]; then
  "$GRAPHIFY" update . >/dev/null 2>&1 && printf '%s' "$HEAD_SHA" > "$MARKER"
  "$PY" "$HELPER" --register-only >/dev/null 2>&1 || true
  exit 0
fi

BASE="$(cat "$MARKER")"
CHANGED_FILE="$(mktemp "${TMPDIR:-/tmp}/graphify-changed.XXXXXX")"
trap 'rm -f "$CHANGED_FILE" "$CHANGED_FILE.all" "$CHANGED_FILE.ignored"' EXIT

{
  git diff --name-only "$BASE" 2>/dev/null || true
  git ls-files --others --exclude-standard 2>/dev/null
} | grep -v "^${OUT}/" \
  | grep -E '\.(ts|tsx|js|jsx|mjs|vue|svelte|html|scss|css|md|mdx|json|java|kt|scala|sql|sh|py|go|rs|c|h|cpp|hpp|rb|php)$' \
  | sort -u > "$CHANGED_FILE.all" || true

if [ -f .graphifyignore ] && [ -s "$CHANGED_FILE.all" ]; then
  git -c core.excludesFile="$PWD/.graphifyignore" check-ignore --no-index --stdin \
    < "$CHANGED_FILE.all" 2>/dev/null | sort -u > "$CHANGED_FILE.ignored" || true
  comm -23 "$CHANGED_FILE.all" "$CHANGED_FILE.ignored" > "$CHANGED_FILE"
else
  cp "$CHANGED_FILE.all" "$CHANGED_FILE"
fi

[ -s "$CHANGED_FILE" ] || exit 0

if "$PY" "$HELPER" < "$CHANGED_FILE"; then
  printf '%s' "$HEAD_SHA" > "$MARKER"
fi
exit 0
