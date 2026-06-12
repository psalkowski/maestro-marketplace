"""Incremental graph rebuild + conditional global re-registration.

Reads changed file paths from stdin (one per line), feeds them to graphify's
internal changed_paths rebuild (the same API its own git hooks use), then
re-registers this repo's subgraph into the global graph iff the cwd is the
checkout recorded in the global manifest (i.e. a main checkout, never a
worktree).

Sandboxed-HOME environments (where the harness rewrites $HOME) can set
GRAPHIFY_REAL_HOME so the global manifest resolves to the real home dir;
graphify.global_graph resolves its directory from $HOME at import time.

Usage:  sync_helper.py            (changed paths on stdin)
        sync_helper.py --register-only
"""

import json
import os
import sys
from pathlib import Path

REAL_HOME = os.environ.get("GRAPHIFY_REAL_HOME") or os.path.expanduser("~")
MANIFEST = Path(REAL_HOME) / ".graphify" / "global-manifest.json"


def reregister() -> None:
    if not MANIFEST.exists():
        return
    graph = (Path.cwd() / "graphify-out" / "graph.json").resolve()
    if not graph.exists():
        return
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except Exception:
        return
    entries = data.get("repos", data) if isinstance(data, dict) else {}
    for tag, meta in entries.items():
        if isinstance(meta, dict) and meta.get("source_path") == str(graph):
            os.environ["HOME"] = REAL_HOME
            from graphify.global_graph import global_add

            try:
                result = global_add(graph, tag)
                if not result.get("skipped"):
                    print(f"[graphify-sync] global graph: re-registered '{tag}'")
            except Exception as exc:
                print(f"[graphify-sync] global re-register failed: {exc}", file=sys.stderr)
            return


def main() -> int:
    if "--register-only" in sys.argv[1:]:
        reregister()
        return 0
    changed = [Path(line.strip()) for line in sys.stdin if line.strip()]
    if not changed:
        return 0
    from graphify.watch import _apply_resource_limits, _rebuild_code

    _apply_resource_limits()
    ok = _rebuild_code(Path("."), changed_paths=changed)
    if not ok:
        return 1
    reregister()
    return 0


if __name__ == "__main__":
    sys.exit(main())
