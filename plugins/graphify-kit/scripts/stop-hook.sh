#!/usr/bin/env bash
# Stop/SessionStart hook: fire-and-forget graph sync.
# Backgrounds the real work so the turn never waits; graphify's internal
# flock + .pending_changes queue make concurrent invocations safe.
# No-ops instantly in projects without a graph (and without a registered
# multi-repo parent), so the plugin is safe to enable globally.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${CLAUDE_PROJECT_DIR:-$PWD}" 2>/dev/null || exit 0
if [ ! -f "${GRAPHIFY_OUT:-graphify-out}/graph.json" ] && [ ! -f "${GRAPHIFY_GLOBAL_MANIFEST:-$HOME/.graphify/global-manifest.json}" ]; then
  exit 0
fi
nohup bash "$SCRIPT_DIR/sync.sh" >/dev/null 2>&1 &
exit 0
