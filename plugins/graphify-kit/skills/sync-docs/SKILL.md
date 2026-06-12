---
description: Use to semantically (re-)index this repo's docs into the graphify knowledge graph — in-repo markdown/prose PLUS an external Obsidian vault auto-detected from project memory (CLAUDE.local.md / CLAUDE.md). The single deliberate, LLM-costing doc sync; supersedes ad-hoc per-project vault-sync commands. Run after authoring or editing docs, or when doc knowledge is missing from the graph. Triggers on /graphify-kit:sync-docs.
---

# /graphify-kit:sync-docs

Semantically index every doc this repo can see — in-repo prose AND an external Obsidian vault if one is configured — into the knowledge graph. This is the **single** deliberate, LLM-costing sync; the AST layer is refreshed automatically by hooks. It is generic and self-contained: discover the doc sources here and index them — **never defer the vault to a separate per-project sync command.**

## Hard rules

- **Model discipline:** dispatch extraction subagents with a mid-tier model (`model: "sonnet"` or cheaper). Never run semantic extraction in the top-tier main loop — extraction is mechanical schema-following, and a single full-corpus pass on a premium model can burn an entire day's budget.
- **Always run to completion.** The AST pass clears `semantic_hash` markers for changed docs BEFORE extraction re-stamps them. Nothing retries automatically — an aborted run leaves those docs silently stale until the next full run.
- **Never re-extract because verification shows pending entries** right after extraction merged. That signature means the manifest write landed on different keys (absolute vs relative — see `/graphify-kit:doctor` check 4). Repair the manifest; never dispatch extraction subagents twice for the same content.
- **Images are excluded by policy** (the setup-generated `.graphifyignore` covers `*.webp *.png *.jpg` etc.). If detection flags ANY image, the ignore file regressed — stop and restore the patterns instead of dispatching vision agents.
- **The vault mirror is read-only.** Never Write/Edit anything under the mirror dir — the next rsync clobbers it and the change never reaches the real vault. Author vault content exclusively via `mcp__obsidian__*` tools or the vault app. Run this skill only on the main checkout, never a worktree.

## Steps

### 0 — Discover doc sources

Two kinds, both discovered generically — no hardcoded paths:

1. **In-repo docs** — every non-gitignored, non-`.graphifyignore`d markdown/prose file the AST walk already sees (`README.md`, `AGENTS.md`, `docs/` kept by the exclusion policy, ADRs, `*.md` beside code, etc.). Nothing to configure; steps 2–4 cover them.
2. **External Obsidian vault (optional)** — read project memory for a vault config. Check `CLAUDE.local.md` first, then `CLAUDE.md`, for the spec-plugin **`## spec configuration`** fenced JSON block:
   ```json
   { "vault": { "root": "<absolute vault path>", "subpath": "Projects/<project>" } }
   ```
   `vault.root` + `vault.subpath` locate this project's slice of an Obsidian vault. Also honor any other explicitly documented vault/docs path if a project uses a different convention. **No vault configured → skip step 1 and go to step 2.** That is the common case, not an error.

### 1 — Mirror the external vault (only if a vault was found in step 0)

Mirror the project's vault slice into a gitignored, **non-`.graphifyignore`d** dir inside the repo, so the same graph build indexes it:

```bash
rsync -a --delete --exclude=".*" "<vault.root>/<vault.subpath>/" <mirror-dir>/
```

- **`<mirror-dir>`** defaults to `vault-mirror/` at the repo root (override with a `vault.mirror` key in the config). If `subpath` is absent, mirror the whole `vault.root`.
- It MUST be **gitignored** but **NOT** in `.graphifyignore`:
  - `git check-ignore -q <mirror-dir>`; if not already ignored, append `<mirror-dir>/` to `.git/info/exclude` (per-repo, never committed). Never commit mirrored vault content.
  - The graph has to see it. Because it is gitignored, the git-based session hooks cannot — which is exactly why this manual flow is the only thing that refreshes it.
- `--exclude=".*"` drops `.obsidian/`, `.trash/`, `.DS_Store`, and iCloud placeholders.
- If rsync errors on vanished files, the vault is partially evicted from iCloud — open it in the vault app to force a download, then re-run.

### 2 — AST pass (deterministic, zero LLM)

```bash
graphify update .
```

Stamps `ast_hash` for changed files (including the freshly mirrored vault docs) and clears `semantic_hash` on content-changed entries — the deliberate "LLM layer is stale" marker the semantic pass reads.

### 3 — Backfill code entries (kill false positives)

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

### 4 — Semantic pass

Invoke the `graphify` skill with args `. --update`. Detection should now flag only docs whose content drifted since their last extraction. The skill's cache check (`check_semantic_cache`) runs before any subagent dispatch — unchanged content is restored from `graphify-out/cache/semantic/` at zero LLM cost, so preserve that cache across rebuilds.

**Sanity guard — BEFORE dispatching extraction subagents:** the **first** sync after mirroring a vault legitimately flags the whole vault as new — confirm the flagged count matches the mirror's doc-file count and proceed. Otherwise, if detection flags more than ~100 files you did not expect, STOP and investigate (mass doc churn the user must confirm, or steps 2–3 didn't run). Each subagent handles ~20–25 docs; dispatch with a mid-tier model per the hard rule.

### 5 — Verify

All must pass (the first three are the exact checks from `/graphify-kit:doctor` 4–6, plus coverage):

```bash
jq -r '[to_entries[] | select((.value.semantic_hash // "") == "")] | length' graphify-out/manifest.json   # 0 (or known stragglers explained)
jq -r '[keys[] | select(startswith("/"))] | length' graphify-out/manifest.json                            # 0 — absolute keys = the double-extraction trap
jq -r '[.nodes[] | select((.source_file // "") | startswith("/"))] | length' graphify-out/graph.json      # 0 — abs-path ghost nodes
```

If a vault was mirrored: graph doc-file coverage includes the mirror's file count, and `git status --short` shows no `<mirror-dir>` entries (proves it is gitignored). Spot-check one vault concept with the symbol directory (`jq` over node labels) — it should surface mirrored doc nodes with a `<mirror-dir>/...` source.

Do NOT verify with `graphify query` — its matcher rarely surfaces doc nodes even when fresh, so a query check passes or fails regardless of the sync's actual outcome.
