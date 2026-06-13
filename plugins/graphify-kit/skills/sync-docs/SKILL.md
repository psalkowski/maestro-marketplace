---
description: Use to semantically (re-)index this repo's docs into the graphify knowledge graph — in-repo markdown/prose PLUS the project's Docs Root (.docs/vault/) discovered from the docs configuration in CLAUDE.local.md / CLAUDE.md. The single deliberate, LLM-costing doc sync; supersedes ad-hoc per-project vault-sync commands. Run after authoring or editing docs, or when doc knowledge is missing from the graph. Triggers on /graphify-kit:sync-docs.
---

# /graphify-kit:sync-docs

Semantically index every doc this repo can see — in-repo prose AND the project's Docs Root (`.docs/vault/`) if docs are configured — into the knowledge graph. This is the **single** deliberate, LLM-costing sync; the AST layer is refreshed automatically by hooks. It is generic and self-contained: discover the doc sources here and index them — **never defer the docs to a separate per-project sync command.**

## Hard rules

- **Model discipline:** dispatch extraction subagents with a mid-tier model (`model: "sonnet"` or cheaper). Never run semantic extraction in the top-tier main loop — extraction is mechanical schema-following, and a single full-corpus pass on a premium model can burn an entire day's budget.
- **Always run to completion.** The AST pass clears `semantic_hash` markers for changed docs BEFORE extraction re-stamps them. Nothing retries automatically — an aborted run leaves those docs silently stale until the next full run.
- **Never re-extract because verification shows pending entries** right after extraction merged. That signature means the manifest write landed on different keys (absolute vs relative — see `/graphify-kit:doctor` check 4). Repair the manifest; never dispatch extraction subagents twice for the same content.
- **Images are excluded by policy** (the setup-generated `.graphifyignore` covers `*.webp *.png *.jpg` etc.). If detection flags ANY image, the ignore file regressed — stop and restore the patterns instead of dispatching vision agents.
- **Indexed docs content is read-only from this skill.** Never Write/Edit anything under `.docs/vault/` (or a fallback copy under `.docs/`) as part of a sync — for the Obsidian provider the Docs Root IS the live vault through a symlink, so a stray edit lands in the user's real notes; fallback copies get clobbered by the next sync. Authoring docs is a separate activity. Run this skill only on the main checkout, never a worktree.

## Steps

### 0 — Discover doc sources

Two kinds, both discovered generically — no hardcoded paths:

1. **In-repo docs** — every non-gitignored, non-`.graphifyignore`d markdown/prose file the AST walk already sees (`README.md`, `AGENTS.md`, `docs/` kept by the exclusion policy, ADRs, `*.md` beside code, etc.). Nothing to configure; steps 2–4 cover them.
2. **Docs Root (optional)** — read project memory for the docs-hub **`## docs configuration`** fenced JSON block. Check `CLAUDE.local.md` first, then `CLAUDE.md`:
   ```json
   { "project": "<name>", "provider": "filesystem|obsidian", "store": "<absolute local path>" }
   ```
   The configured docs live at the **Docs Root** — `.docs/vault/`, a symlink to `store`.
   **Legacy:** a `## spec configuration` block with `vault.root` / `vault.subpath` is still accepted — `store` is the two joined — but print one line: `Deprecated: '## spec configuration' vault block — run /docs-hub:setup to migrate to '## docs configuration'.`
   **No config block and no `.docs/vault` → skip step 1 and go to step 2.** That is the common case, not an error.

### 1 — Resolve the Docs Root (only if docs were configured in step 0)

For local providers (`filesystem`, `obsidian`) the graph indexes **`.docs/vault/` directly through the symlink** — no mirror copy, no rsync, no gitignore bookkeeping (`.docs/.gitignore` containing `*` already keeps the whole directory self-ignored). Checks before indexing:

- **Symlink resolves:** `test -d .docs/vault` (this follows the link). Missing or dangling — the store moved, or the repo never finished onboarding — STOP indexing the docs and point the user at `/docs-hub:setup`; never silently create or write into an unlinked `.docs/`.
- **`.graphifyignore` must not exclude it:** `grep -E '\.docs' .graphifyignore` should match nothing. If a pattern excludes `.docs/`, remove it (remember: a `.graphifyignore` change requires a from-scratch rebuild — `/graphify-kit:setup`).
- Because `.docs/` is gitignored (self-ignoring), the git-based session hooks never see its changes — this manual flow is the only thing that refreshes the docs' semantic layer.

Remote providers (future: `notion`, `gdrive`) are the one place a synced read-only mirror remains the documented path; no such provider exists yet.

### 2 — AST pass (deterministic, zero LLM)

```bash
graphify update .
```

Stamps `ast_hash` for changed files (including the Docs Root content) and clears `semantic_hash` on content-changed entries — the deliberate "LLM layer is stale" marker the semantic pass reads.

**Symlink sanity gate (only when a Docs Root is configured) — BEFORE any extraction:** confirm the CLI actually traversed the symlink:

```bash
jq -r '[keys[] | select(startswith(".docs/vault/"))] | length' graphify-out/manifest.json
```

Must be **> 0** (a scaffolded Docs Root always holds at least the seven `_index.md` files). If it is 0 while `.docs/vault/` has files, the CLI did not follow the symlink — fall back to a thin internal copy, contract unchanged:

```bash
mkdir -p .docs/index-cache
rsync -a --delete --exclude=".*" "<store>/" .docs/index-cache/
graphify update .
```

(Ensure `.docs/.gitignore` contains `*` — it should already.) Re-check the manifest for `.docs/index-cache/` entries, and state clearly in the final output that the fallback copy is in use.

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

**Sanity guard — BEFORE dispatching extraction subagents:** the **first** sync after a Docs Root is linked legitimately flags all of its docs as new — confirm the flagged count matches the Docs Root's doc-file count and proceed. Otherwise, if detection flags more than ~100 files you did not expect, STOP and investigate (mass doc churn the user must confirm, or steps 2–3 didn't run). Each subagent handles ~20–25 docs; dispatch with a mid-tier model per the hard rule.

### 5 — Verify

All must pass (the first three are the exact checks from `/graphify-kit:doctor` 4–6, plus coverage):

```bash
jq -r '[to_entries[] | select((.value.semantic_hash // "") == "")] | length' graphify-out/manifest.json   # 0 (or known stragglers explained)
jq -r '[keys[] | select(startswith("/"))] | length' graphify-out/manifest.json                            # 0 — absolute keys = the double-extraction trap
jq -r '[.nodes[] | select((.source_file // "") | startswith("/"))] | length' graphify-out/graph.json      # 0 — abs-path ghost nodes
```

If a Docs Root was indexed: graph doc-file coverage includes its file count, and `git status --short` shows no `.docs/` entries (proves the self-ignoring `.docs/.gitignore` is intact). Spot-check one docs concept with the symbol directory (`jq` over node labels) — it should surface doc nodes with a `.docs/vault/...` source (or `.docs/index-cache/...` when the fallback is in use).

Do NOT verify with `graphify query` — its matcher rarely surfaces doc nodes even when fresh, so a query check passes or fails regardless of the sync's actual outcome.
