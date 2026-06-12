---
description: Use when the repo's docs, knowledge base, or an external notes vault should be (re-)indexed into the graphify knowledge graph semantically — after authoring or editing docs, or when doc knowledge is missing from the graph. Runs LLM extraction with strict model and token discipline. Triggers on /graphify-kit:sync-docs.
---

# /graphify-kit:sync-docs

Semantically index doc content (in-repo markdown, or an external notes vault mirrored into the repo) into the knowledge graph. The AST layer is synced automatically by hooks; THIS flow is the only one that costs LLM tokens — run it deliberately, never automatically.

## Hard rules

- **Model discipline:** dispatch extraction subagents with a mid-tier model (`model: "sonnet"` or cheaper). Never run semantic extraction in the top-tier main loop — extraction is mechanical schema-following, and a single full-corpus pass on a premium model can burn an entire day's budget.
- **Always run to completion.** The AST pass clears `semantic_hash` markers for changed docs BEFORE extraction re-stamps them. Nothing retries automatically — an aborted run leaves those docs silently stale until the next full run.
- **Never re-extract because verification shows pending entries** right after extraction merged. That signature means the manifest write landed on different keys (absolute vs relative — see `/graphify-kit:doctor` check 4). Repair the manifest; never dispatch extraction subagents twice for the same content.
- **Images are excluded by policy** (the setup-generated `.graphifyignore` covers `*.webp *.png *.jpg` etc.). If detection flags ANY image, the ignore file regressed — stop and restore the patterns instead of dispatching vision agents.
- **External vault mirrors are read-only.** If this repo mirrors an external notes vault (rsync'd into a gitignored dir), never Write/Edit inside the mirror — author content in the source system. Run this skill only on the main checkout, never a worktree.

## Steps

### 0 — Mirror external docs (only if configured)

If the project documents an external docs source (check the project's CLAUDE.md / CLAUDE.local.md for a docs-mirror or vault config), rsync it into the repo first, excluding dotfiles:

```bash
rsync -a --delete --exclude=".*" "<external-docs-path>/" <mirror-dir>/
```

The mirror dir must be gitignored but must NOT be in `.graphifyignore` (the graph has to see it; because it is gitignored, the git-based session hooks cannot see its changes — this skill is the only thing that refreshes it).

### 1 — AST pass (deterministic, zero LLM)

```bash
graphify update .
```

Stamps `ast_hash` for changed files and clears `semantic_hash` on content-changed entries — the deliberate "LLM layer is stale" marker the semantic pass reads.

### 2 — Backfill code entries (kill false positives)

Code files never get LLM extraction in this flow — AST is their full representation — so an empty `semantic_hash` on a code entry is noise that would dispatch pointless subagents. Backfill code-extension entries only; NEVER backfill doc/paper entries (that would permanently swallow the refresh):

```bash
$(cat graphify-out/.graphify_python) -c "
import json
from pathlib import Path
from graphify.detect import CODE_EXTENSIONS
p = Path('graphify-out/manifest.json')
m = json.loads(p.read_text(encoding='utf-8'))
n = 0
for key, entry in m.items():
    if (isinstance(entry, dict) and not entry.get('semantic_hash') and entry.get('ast_hash')
            and Path(key).suffix.lower() in CODE_EXTENSIONS):
        entry['semantic_hash'] = entry['ast_hash']
        n += 1
p.write_text(json.dumps(m, indent=1, ensure_ascii=False), encoding='utf-8')
print(f'backfilled {n} code entries')
"
```

### 3 — Semantic pass

Invoke the `graphify` skill with args `. --update`. Detection should now flag only docs whose content drifted since their last extraction. The skill's cache check (`check_semantic_cache`) runs before any subagent dispatch — unchanged content is restored from `graphify-out/cache/semantic/` at zero LLM cost, so preserve that cache across rebuilds.

**Sanity guard — BEFORE dispatching extraction subagents:** if detection flags more than ~100 files after the code backfill, STOP and investigate (mass doc churn the user must confirm, or steps 1–2 didn't run). Each subagent handles ~20–25 docs; dispatch with a mid-tier model per the hard rule.

### 4 — Verify

All four must pass (these are the exact checks from `/graphify-kit:doctor` 4–6, plus coverage):

```bash
jq -r '[to_entries[] | select((.value.semantic_hash // "") == "")] | length' graphify-out/manifest.json   # 0 (or known stragglers explained)
jq -r '[keys[] | select(startswith("/"))] | length' graphify-out/manifest.json                            # 0 — absolute keys = the double-extraction trap
jq -r '[.nodes[] | select((.source_file // "") | startswith("/"))] | length' graphify-out/graph.json      # 0 — abs-path ghost nodes
```

If a docs mirror is configured: graph doc-file coverage equals the mirror's file count, and `git status --short` shows no mirror entries.

Do NOT verify with `graphify query` — its matcher rarely surfaces doc nodes even when fresh, so a query check passes or fails regardless of the sync's actual outcome.
