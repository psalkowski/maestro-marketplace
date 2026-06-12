---
description: Use when the graphify knowledge graph misbehaves (explain misses known symbols, stale results, sync errors, suspicious node counts) or after upgrades and bulk operations — runs the full health-check suite against graphify-out and prescribes the repair for each failure. Triggers on /graphify-kit:doctor.
---

# /graphify-kit:doctor

Health-check the repo's graphify state. Run every check; report PASS/FAIL per check with the prescribed repair. Never "fix" a failure by re-running LLM extraction unless the check explicitly prescribes it — most failures here are bookkeeping, and re-extraction burns paid tokens to mask them.

## Checks

### 1 — Graph exists and is non-trivial

```bash
jq -r '.nodes | length' graphify-out/graph.json
```

Missing file → not onboarded (or a worktree that never seeded): run `/graphify-kit:setup` on the main checkout, or `bash scripts/graphify/worktree-setup.sh` in a worktree. A node count wildly below expectation for the repo size → check `.graphifyignore` for an over-broad pattern (a bare `docs/` matches at any depth; anchor to root with `/docs/`).

### 2 — No nested graphify-out

```bash
ls graphify-out/graphify-out 2>/dev/null
```

Anything found → two bootstrap mechanisms raced (e.g. a `cp -R` in a setup script racing the seeding rsync). Delete the nested dir, then find and remove the duplicate copy step from the worktree bootstrap.

### 3 — Baseline tracks HEAD

```bash
cat graphify-out/.graphify-baseline-sha; git rev-parse HEAD
```

A small lag is normal (hooks sync on session boundaries). A missing marker or large lag → run `bash scripts/graphify/sync.sh` (zero LLM) and re-check.

### 4 — Manifest key hygiene (the double-extraction trap)

```bash
jq -r '[keys[] | select(startswith("/"))] | length' graphify-out/manifest.json
```

Must print `0`. Absolute-path keys mean a rootless `save_manifest` wrote legacy-format entries that duplicate every relative key. Symptom chain: semantic stamps land on the absolute twins → verification sees the relative entries as pending → naive repair re-extracts docs that were just extracted, burning a full LLM round. **Repair (no LLM):** normalize keys to relative and merge twins, preferring the entry with non-empty `semantic_hash`:

```bash
cp graphify-out/manifest.json /tmp/manifest-backup.json
jq --arg p "$(pwd)/" 'to_entries | map(.key |= sub("^" + $p; "")) | group_by(.key) | map((map(select((.value.semantic_hash // "") != "")) + .)[0]) | from_entries' /tmp/manifest-backup.json > graphify-out/manifest.json
```

### 5 — No absolute source paths in graph nodes

```bash
jq -r '[.nodes[] | select((.source_file // "") | startswith("/"))] | length' graphify-out/graph.json
```

Must print `0`. LLM extraction agents sometimes write absolute paths into `source_file` despite the spec; these dodge the relative-prefix pruner (immortal ghost nodes) and make exclusion verification false-clean. Repair: rewrite the prefix to relative with jq (back up first), drop nodes whose normalized source matches `.graphifyignore`, and filter links/hyperedges to surviving node ids.

### 6 — Pending-extraction markers are honest

```bash
jq -r '[to_entries[] | select((.value.semantic_hash // "") == "") | .key] | length' graphify-out/manifest.json
```

Non-zero is only legitimate for doc/paper files awaiting `/graphify-kit:sync-docs`. Code files pending → the code backfill didn't run (see sync-docs step 3). Doc files that were _just_ extracted still pending → check 4's key-form trap; stamp, never re-extract.

### 7 — Protocol installed

- Exactly one of `CLAUDE.md` or `CLAUDE.local.md` contains the `graphify-kit:begin` marker (the block in both files is a misconfiguration — remove the stale copy, keeping `CLAUDE.local.md` unless `CLAUDE.md` independently documents graphify).
- `.claude/agents/explore.md` exists with `model: haiku` frontmatter.
- The symbol directory returns results for a domain term that certainly exists in this repo (pick one from the README).

Any missing → re-run `/graphify-kit:setup` (steps 3–6 are idempotent).

### 8 — Spot-check explain quality

Pick 2 symbols from the symbol directory output and `graphify explain` each. Both must resolve with a correct `Source:` path. A miss on a directory-supplied name (not a guessed one) indicates a stale graph → run `bash scripts/graphify/sync.sh`, re-check; if still missing, the file may be newly `.graphifyignore`d or the graph needs a rebuild (`/graphify-kit:setup`).

## Report

End with a table: check → PASS/FAIL → action taken or prescribed. If everything passes, say so plainly and remind the one-line flow: _symbol directory → explain → targeted Read_.
