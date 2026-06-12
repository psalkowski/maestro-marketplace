#!/usr/bin/env bash
# Worktree bootstrap: seed the worktree's knowledge graph from the main
# checkout, fix the non-portable metadata, then incrementally sync to the
# worktree's branch state (usually a handful of files, often a no-op).
#
# Works with any worktree manager. Conductor's env vars are honored when
# present (CONDUCTOR_WORKSPACE_PATH / CONDUCTOR_ROOT_PATH); otherwise the
# main checkout is derived from the worktree's shared git dir, so the same
# script works for plain `git worktree` and other tools.
#
# /graphify-kit:setup copies this script (plus sync.sh and sync_helper.py)
# into <repo>/scripts/graphify/ so worktree bootstrap is committed with the
# repo and does not depend on a machine-local plugin cache path.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS="${CONDUCTOR_WORKSPACE_PATH:-$PWD}"
cd "$WS"

GRAPHIFY="$(command -v graphify || true)"
[ -n "$GRAPHIFY" ] || GRAPHIFY="$HOME/.local/bin/graphify"
if [ ! -x "$GRAPHIFY" ]; then
  echo "[graphify-worktree-setup] graphify CLI not installed — skipping (run /graphify-kit:setup)"
  exit 0
fi

ROOT="${CONDUCTOR_ROOT_PATH:-}"
if [ -z "$ROOT" ]; then
  COMMON="$(git rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)"
  [ -n "$COMMON" ] && ROOT="$(dirname "$COMMON")"
fi

# Main checkout (or not a worktree): nothing to seed — just sync.
if [ -z "$ROOT" ] || [ "$ROOT" = "$WS" ] || [ "$ROOT" = "$(pwd -P)" ]; then
  exec bash "$SCRIPT_DIR/sync.sh"
fi

SRC="$ROOT/graphify-out"
DST="$WS/graphify-out"

# Already seeded: don't clobber the worktree's graph state — incremental sync.
if [ -f "$DST/graph.json" ] && [ -f "$DST/.graphify-baseline-sha" ]; then
  echo "[graphify-worktree-setup] already seeded — incremental sync only"
  exec bash "$SCRIPT_DIR/sync.sh"
fi

# Machine-local companions the worktree needs but git does not carry.
if [ -f "$ROOT/.graphifyignore" ] && [ ! -f "$WS/.graphifyignore" ]; then
  cp "$ROOT/.graphifyignore" "$WS/.graphifyignore"
fi
if [ -f "$ROOT/.claude/settings.local.json" ] && [ ! -f "$WS/.claude/settings.local.json" ]; then
  mkdir -p "$WS/.claude"
  cp "$ROOT/.claude/settings.local.json" "$WS/.claude/settings.local.json"
fi

if [ ! -f "$SRC/graph.json" ]; then
  if [ ! -f "$WS/.graphifyignore" ]; then
    echo "[graphify-worktree-setup] repo not bootstrapped (no graph on main, no .graphifyignore) — skipping."
    echo "[graphify-worktree-setup] run /graphify-kit:setup on the main checkout first."
    exit 0
  fi
  echo "[graphify-worktree-setup] no source graph at $SRC — AST-only build"
  "$GRAPHIFY" update .
  git rev-parse HEAD > "$DST/.graphify-baseline-sha"
  exit 0
fi

rsync -a "$SRC/" "$DST/"
rm -f "$DST/cost.json"
printf '%s' "$WS" > "$DST/.graphify_root"

bash "$SCRIPT_DIR/sync.sh"
echo "[graphify-worktree-setup] done"
