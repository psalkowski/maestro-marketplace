#!/usr/bin/env python3
# Reads a PreToolUse(Bash) payload on stdin. For an unambiguous by-role search
# (the leak the graph exists to prevent) it RUNS the graph and embeds the result
# in the deny reason, so the model gets the complete answer in the SAME turn —
# no scold-then-retry round-trip. If the graph does not actually know the symbol
# (new code, external lib, string-ish name) it downgrades to a non-blocking
# nudge so the grep/find still runs. Other grep/find get the plain nudge.
# Detection logic lives in classify() (pure, unit-tested); main() does the I/O.
import re, sys, json, shutil, subprocess

NUDGE = ("graphify: LOCATE code through the graph, not this grep. Flow: no symbol yet -> "
         "run the jq symbol directory (harvests real names + file:line); have a name -> "
         "`graphify explain \"<Name>\"`; every usage / blast radius -> `graphify affected \"<Name>\"` "
         "(replaces `grep -rn`); connect two symbols -> `graphify path \"<A>\" \"<B>\"`. "
         "Grep is ONLY for raw text the graph cannot index (template markup, a string literal, a log line).")

PATHFILTER = ("jq -r --arg p \"<path-fragment>\" '.nodes[] | select((.source_file // \"\") | contains($p)) | "
              "((.label | gsub(\"\\\\s+\";\" \"))[0:60]) + \"  \" + (.source_file // \"?\") + \"  \" + "
              "(.source_location // \"?\")' graphify-out/graph.json | sort -u")

JQ_PATHFILTER = (r'.nodes[] | select((.source_file // "") | contains($p)) | '
                 r'((.label | gsub("\\s+";" "))[0:60]) + "  " + (.source_file // "?") + "  " '
                 r'+ (.source_location // "?")')

GREP_PREAMBLE = ("graphify intercepted this grep and ran the graph for you — the complete definition + "
                 "caller/import map is below, so there is NOTHING to re-run. When a symbol's connections "
                 "end with \"... and N more\", that is `explain`'s 20-connection cap: run "
                 "`graphify affected \"<Symbol>\"` for the COMPLETE usage list. Grep stays reserved for "
                 "raw text the graph can't index (a UI label / error string with spaces, template markup).\n\n")

FIND_PREAMBLE = ("graphify intercepted this by-role `find` and ran the on-graph path filter for you — every "
                 "symbol in files whose path contains \"%s\", with file:line, is below (nothing to re-run). "
                 "Narrow the fragment or `graphify explain \"<Symbol>\"` a specific row to go deeper. "
                 "Enumerating a KNOWN dir by extension (`find <dir> -name \"*.ts\"`) is fine and not blocked.\n\n")


def _is_symbol(t):
    if re.search(r'[a-z][A-Z]', t):
        return True
    if t[0].isupper() and any(c.islower() for c in t):
        return True
    if "_" in t and any(c.isalpha() for c in t):
        return True
    return False


def classify(cmd):
    c = cmd or ""
    if "graphify" in c:
        return ("allow",)
    for m in re.finditer(r'-i?name\s+(["\']?)([^"\'\s]+)\1', c):
        pat = m.group(2)
        if "*" not in pat:
            continue
        core = pat.strip("*")
        if core == "" or core.startswith("."):
            continue
        return ("deny", "find", pat)
    gm = re.search(r'\bgrep\b((?:\s+-{1,2}\S+)*)', c)
    gflags = gm.group(1) if gm else ''
    rec = (bool(re.search(r'(?:^|\s)-[a-zA-Z]*[rR]', gflags)) or 'recursive' in gflags
           or bool(re.search(r'\brg\b', c))
           or bool(re.search(r'\bgit\s+grep\b', c)))
    if rec:
        pats = [a or b for a, b in re.findall(r'"([^"]*)"|\'([^\']*)\'', c)]
        if not pats:
            m = re.search(r'(?:grep\s+(?:-\S+\s+)*|rg\s+(?:-\S+\s+)*)([A-Za-z_][A-Za-z0-9_|]*)', c)
            if m:
                pats = [m.group(1)]
        for p in pats:
            if not p or " " in p:
                continue
            tokens = [t.strip("\\") for t in re.split(r'\\?\|', p) if t.strip("\\")]
            if tokens and all(re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', t) for t in tokens):
                if any(_is_symbol(t) for t in tokens):
                    return ("deny", "grep", p)
    if re.search(r'grep|\brg\b|ripgrep|find\s|\bfd\s|\back\s|\bag\s', c):
        return ("nudge",)
    return ("allow",)


def _run(args):
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=8)
        return (r.stdout or "").strip()
    except Exception:
        return ""


def _symbols(pat):
    toks = [t.strip("\\") for t in re.split(r'\\?\|', pat) if t.strip("\\")]
    return [t for t in toks if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', t) and _is_symbol(t)]


def inject_grep(pat):
    if not shutil.which("graphify"):
        return None
    blocks = []
    for s in _symbols(pat)[:2]:
        out = _run(["graphify", "explain", s])
        if out and "No node matching" not in out:
            blocks.append("$ graphify explain \"%s\"\n%s" % (s, out))
    return GREP_PREAMBLE + "\n\n".join(blocks) if blocks else None


def inject_find(pat):
    frag = pat.strip("*")
    if not frag or not shutil.which("jq"):
        return None
    out = _run(["jq", "-r", "--arg", "p", frag, JQ_PATHFILTER, "graphify-out/graph.json"])
    if not out:
        return None
    lines = sorted(set(out.splitlines()))
    body = "\n".join(lines[:40])
    if len(lines) > 40:
        body += "\n... (%d more — narrow the fragment)" % (len(lines) - 40)
    return (FIND_PREAMBLE % frag) + body


def _deny(reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                             "permissionDecision": "deny",
                                             "permissionDecisionReason": reason}}))


def _nudge():
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": NUDGE}}))


def main():
    try:
        d = json.load(sys.stdin)
    except Exception:
        return
    ti = d.get("tool_input", d)
    cmd = ti.get("command", "") if isinstance(ti, dict) else (ti if isinstance(ti, str) else "")
    act = classify(cmd)
    if act[0] == "deny":
        inj = inject_grep(act[2]) if act[1] == "grep" else inject_find(act[2])
        if inj:
            _deny(inj)
        else:
            _nudge()
    elif act[0] == "nudge":
        _nudge()


if __name__ == "__main__":
    main()
