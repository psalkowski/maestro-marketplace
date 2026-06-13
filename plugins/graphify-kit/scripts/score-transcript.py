#!/usr/bin/env python3
"""graphify-kit transcript scorecard — Conductor-agnostic.

Scores a Claude Code session transcript for graph-navigation health:
wall-clock, tokens, tool-mix, grep/find-by-role count, graphify usage, and
explain misses — across the main loop and any Explore/subagent transcripts.

These are the MECHANICAL metrics only. Answer correctness / fabrication is a
human or LLM spot-check; this script never claims to judge it.

Usage:
  score-transcript.py <transcript.jsonl | project-transcript-dir | cwd>

Resolution:
  - a .jsonl file            -> scored directly
  - a dir with *.jsonl       -> newest *.jsonl in it
  - any working-directory    -> encoded to ~/.claude/projects/<enc>/ (newest)

No Conductor knowledge: transcripts are a Claude Code primitive at
~/.claude/projects/<cwd-with-slashes-and-dots-as-dashes>/<uuid>.jsonl, with
subagents under <uuid>/subagents/agent-*.jsonl.
"""
import glob
import json
import re
import sys
from datetime import datetime
from pathlib import Path


def resolve_transcript(arg):
    p = Path(arg).expanduser()
    if p.is_file() and p.suffix == ".jsonl":
        return p
    if p.is_dir():
        js = sorted(p.glob("*.jsonl"), key=lambda f: f.stat().st_mtime)
        if js:
            return js[-1]
    abspath = str(Path(arg).expanduser().resolve())
    encoded = re.sub(r"[/.]", "-", abspath)
    proj = Path.home() / ".claude" / "projects" / encoded
    if proj.is_dir():
        js = sorted(proj.glob("*.jsonl"), key=lambda f: f.stat().st_mtime)
        if js:
            return js[-1]
    return None


def load(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return rows


def classify(tool, inp):
    """Return (bucket, detail). Buckets drive the scorecard counts."""
    if tool == "Read":
        return "read", str(inp.get("file_path", ""))
    if tool in ("Agent", "Task"):
        return "agent", str(inp.get("description", ""))
    if tool == "Grep":
        # the Grep tool is a recursive content search by nature
        return "grep_byrole", "Grep tool: " + str(inp.get("pattern", ""))
    if tool == "Glob":
        return "glob", str(inp.get("pattern", ""))
    if tool != "Bash":
        return "other", tool
    c = str(inp.get("command", "")).strip()
    low = c.lower()
    if re.match(r"graphify\s+explain", c):
        return "explain", c
    if re.match(r"graphify\s+affected", c):
        return "affected", c
    if re.match(r"graphify\s+path\b", c):
        return "path", c
    if re.match(r"graphify\s+query", c):
        return "query_BAD", c
    if "graph.json" in c and ("jq " in low or low.startswith("jq")):
        return "jq_directory", c
    has_find = re.search(r"(^|\|\s*|&&\s*|;\s*)find\s", c) is not None
    has_grep = re.search(r"\b(grep|rg|ripgrep)\b", c) is not None
    if has_find:
        # a pure extension sweep (find -name "*.ext" only) is sanctioned
        names = re.findall(r"-i?name\s+['\"]?([^'\" ]+)", c)
        only_ext = bool(names) and all(n.startswith("*.") for n in names)
        return ("find_extsweep" if only_ext else "find_byrole"), c
    if has_grep:
        # grep in a pipe filtering jq/ls output is benign
        if "|" in c and ("graph.json" in c or re.search(r"\bls\b", c)):
            return "grep_pipe", c
        # recursive grep, or grep over a directory path = by-role search
        if re.search(r"grep\s+-\w*r", c) or re.search(r"\b-r\b|\b-R\b|--recursive", c):
            return "grep_byrole", c
        return "grep_scoped", c
    return "bash_other", c


def score_one(rows, label):
    asst = [r for r in rows if r.get("type") == "assistant"]
    models = sorted({r.get("message", {}).get("model", "?") for r in asst})
    ts = [r.get("timestamp") for r in rows if r.get("timestamp")]
    wall = None
    if len(ts) >= 2:
        try:
            t0 = datetime.fromisoformat(ts[0].replace("Z", "+00:00"))
            t1 = datetime.fromisoformat(ts[-1].replace("Z", "+00:00"))
            wall = (t1 - t0).total_seconds()
        except ValueError:
            pass
    out = cw = cr = 0
    for r in asst:
        u = r.get("message", {}).get("usage", {}) or {}
        out += u.get("output_tokens", 0) or 0
        cw += u.get("cache_creation_input_tokens", 0) or 0
        cr += u.get("cache_read_input_tokens", 0) or 0
    buckets = {}
    seq = []
    reads = {}
    for r in asst:
        for blk in r.get("message", {}).get("content", []) or []:
            if isinstance(blk, dict) and blk.get("type") == "tool_use":
                b, d = classify(blk.get("name", ""), blk.get("input", {}) or {})
                buckets[b] = buckets.get(b, 0) + 1
                seq.append((b, d))
                if b == "read":
                    reads[d] = reads.get(d, 0) + 1
    misses = 0
    for r in rows:
        if r.get("type") == "user":
            for blk in r.get("message", {}).get("content", []) or []:
                if isinstance(blk, dict) and blk.get("type") == "tool_result":
                    txt = blk.get("content", "")
                    if isinstance(txt, list):
                        txt = " ".join(
                            x.get("text", "") for x in txt if isinstance(x, dict)
                        )
                    if isinstance(txt, str) and re.search(
                        r"no node matching", txt, re.I
                    ):
                        misses += 1
    dup_reads = {f: n for f, n in reads.items() if n > 1}
    head_dir = any(b == "jq_directory" and "head" in d for b, d in seq)
    return {
        "label": label, "models": models, "wall": wall, "turns": len(asst),
        "out": out, "cw": cw, "cr": cr, "buckets": buckets, "seq": seq,
        "explain_misses": misses, "dup_reads": dup_reads, "head_dir": head_dir,
    }


def fmt_wall(s):
    if s is None:
        return "n/a"
    return f"{int(s // 60)}m {int(s % 60):02d}s"


def byrole(b):
    return b.get("find_byrole", 0) + b.get("grep_byrole", 0)


def report(scores):
    line = "─" * 60
    print(line)
    print("graphify-kit transcript scorecard")
    print(line)
    total = {"out": 0, "cw": 0, "cr": 0}
    agg_byrole = 0
    query_used = False
    for s in scores:
        b = s["buckets"]
        total["out"] += s["out"]; total["cw"] += s["cw"]; total["cr"] += s["cr"]
        agg_byrole += byrole(b)
        query_used = query_used or b.get("query_BAD", 0) > 0
        print(f"\n▸ {s['label']}  [{', '.join(s['models'])}]")
        print(f"  wall {fmt_wall(s['wall'])} · turns {s['turns']}")
        print(f"  tokens  out {s['out']:,} · cache-write {s['cw']:,} · cache-read {s['cr']:,}")
        nav = (f"explain {b.get('explain',0)} · affected {b.get('affected',0)} · "
               f"path {b.get('path',0)} · jq-directory {b.get('jq_directory',0)}")
        print(f"  graph   {nav}")
        srch = (f"find(by-role) {b.get('find_byrole',0)} · find(ext-sweep) {b.get('find_extsweep',0)} · "
                f"grep(by-role) {b.get('grep_byrole',0)} · grep(scoped) {b.get('grep_scoped',0)} · "
                f"grep(pipe) {b.get('grep_pipe',0)} · glob {b.get('glob',0)}")
        print(f"  search  {srch}")
        print(f"  reads   {b.get('read',0)} · agent dispatches {b.get('agent',0)}")
        flags = []
        if b.get("query_BAD", 0):
            flags.append(f"✗ graphify query used ×{b['query_BAD']}")
        if byrole(b):
            flags.append(f"✗ by-role find/grep ×{byrole(b)}")
        if s["explain_misses"]:
            flags.append(f"⚠ explain misses ×{s['explain_misses']}")
        if s["dup_reads"]:
            flags.append(f"⚠ duplicate reads: {len(s['dup_reads'])} file(s)")
        if s["head_dir"]:
            flags.append("⚠ jq directory head-truncated")
        print("  flags   " + ("; ".join(flags) if flags else "✓ none"))
    print(f"\n{line}")
    print("COMBINED")
    print(f"  output {total['out']:,} · cache-write {total['cw']:,} · cache-read {total['cr']:,}")
    verdict = []
    verdict.append("✓ no graphify query" if not query_used else "✗ graphify query used")
    verdict.append("✓ zero by-role find/grep" if agg_byrole == 0
                   else f"✗ {agg_byrole} by-role find/grep (the leak metric)")
    print("  verdict " + " · ".join(verdict))
    print("  NOTE: correctness/fabrication is a manual spot-check — not scored here.")
    print(line)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    t = resolve_transcript(sys.argv[1])
    if not t:
        print(f"Could not resolve a transcript from: {sys.argv[1]}", file=sys.stderr)
        print("Pass a .jsonl path, a project-transcript dir, or a workspace cwd.",
              file=sys.stderr)
        sys.exit(1)
    scores = [score_one(load(t), "main loop")]
    sub_dir = t.parent / t.stem / "subagents"
    for sf in sorted(glob.glob(str(sub_dir / "agent-*.jsonl"))):
        meta = Path(sf).with_suffix(".meta.json")
        atype = "subagent"
        if meta.is_file():
            try:
                atype = json.loads(meta.read_text()).get("agentType", "subagent")
            except (json.JSONDecodeError, OSError):
                pass
        scores.append(score_one(load(sf), f"{atype} subagent"))
    print(f"transcript: {t}")
    report(scores)


if __name__ == "__main__":
    main()
