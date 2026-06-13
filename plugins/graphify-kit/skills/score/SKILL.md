---
name: score
description: Use to score a Claude Code session transcript for graphify navigation health — wall-clock, tokens, tool-mix, the by-role grep/find leak count, graphify-verb usage, and explain misses, across the main loop and any subagents. The mechanical half of an eval run (correctness stays a human/LLM spot-check). Triggers on /graphify-kit:score. Conductor-agnostic — works on any Claude Code transcript.
---

# /graphify-kit:score

Produce the mechanical scorecard for a session transcript so you don't have to read it by hand. Use it to validate a navigation-protocol change, catch a regression, or compare two runs of the same prompt. It scores the **main loop plus every subagent** and prints a combined verdict.

This is **mechanical metrics only** — wall-clock, tokens, tool-mix, the by-role `grep`/`find` count (the leak metric), graphify-verb usage, explain misses, duplicate reads, and `head`-truncated directories. **Answer correctness and fabrication are NOT scored** — they remain a quick human or LLM spot-check (open the final answer, verify the load-bearing `file:line`, look for untraced cross-cutting claims).

## Run it

Transcripts are a Claude Code primitive — there is no Conductor dependency. The script resolves any of:

- a transcript `.jsonl` path,
- a project-transcript directory (`~/.claude/projects/<encoded>/`),
- or a **working-directory path** (a repo/workspace root) — it encodes that to the project-transcript dir and picks the newest session.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/score-transcript.py" <transcript.jsonl | project-dir | workspace-cwd>
```

If the user named a workspace (e.g. a path under their worktree manager), pass that path directly — the script finds the session. With no graph-specific args, pass the workspace root they're asking about.

## Read the result

A healthy graph-navigation run shows:

- **`verdict: ✓ zero by-role find/grep`** — the headline. By-role `find`/`grep` (locating a file by its _role_, e.g. `find "*provider*"`, `grep -r`) is the leak the protocol exists to prevent. Scoped greps (string-hunt in a known file) and extension sweeps (`find -name "*.sql"`) are sanctioned and counted separately.
- **`✓ no graphify query`** — `graphify query` returns neighborhood noise, never matching names; any use is a flag.
- **graph verbs present** — `explain`/`affected`/`jq-directory` should carry the navigation; if these are ~0 while reads are high, the run skipped the graph.
- **cache-read in range** — compare against a known-good baseline for the same prompt. A run whose cache-read exceeds the no-graph control means it paid for the graph _and_ a grep sweep (the classic regression).

Flags to investigate: `jq directory head-truncated` (the harvest was cut off, hiding the symbol the run later hunted for); `duplicate reads` (re-reading a file `explain` would have mapped once); `explain misses` (guessed names — should be 0 if names came from the directory).

## As a gate

The same script is the basis for a regression gate: re-run a fixed prompt in a fresh session after a protocol change, score it, and assert `by-role find/grep == 0`, `no graphify query`, and `cache-read < <baseline×1.3>`. Running the session itself needs a real Claude Code run (not CI-automatable on its own), but scoring the resulting transcript is one deterministic command.
