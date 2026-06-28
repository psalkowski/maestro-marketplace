#!/usr/bin/env python3
# Reads a PreToolUse(Bash) payload on stdin. Emits a deny decision for an
# unambiguous by-role search (the leak the graph exists to prevent), a
# non-blocking nudge for other grep/find, or nothing. Never denies an
# extension sweep (*.ts), a path sweep (-path), or a string-literal grep.
import re, sys, json

NUDGE = ("graphify: LOCATE code through the graph, not this grep. Flow: no symbol yet -> "
         "run the jq symbol directory (harvests real names + file:line); have a name -> "
         "`graphify explain \"<Name>\"`; every usage / blast radius -> `graphify affected \"<Name>\"` "
         "(replaces `grep -rn`); connect two symbols -> `graphify path \"<A>\" \"<B>\"`. "
         "Grep is ONLY for raw text the graph cannot index (template markup, a string literal, a log line).")

PATHFILTER = ("jq -r --arg p \"<path-fragment>\" '.nodes[] | select((.source_file // \"\") | contains($p)) | "
              "((.label | gsub(\"\\\\s+\";\" \"))[0:60]) + \"  \" + (.source_file // \"?\") + \"  \" + "
              "(.source_location // \"?\")' graphify-out/graph.json | sort -u")


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
    rec = (bool(re.search(r'grep\s+[^|]*-[A-Za-z]*[rR]', c))
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
            tokens = [t for t in p.split("|") if t]
            if tokens and all(re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', t) for t in tokens):
                if any(_is_symbol(t) for t in tokens):
                    return ("deny", "grep", p)
    if re.search(r'grep|\brg\b|ripgrep|find\s|\bfd\s|\back\s|\bag\s', c):
        return ("nudge",)
    return ("allow",)


def main():
    try:
        d = json.load(sys.stdin)
    except Exception:
        return
    ti = d.get("tool_input", d)
    cmd = ti.get("command", "") if isinstance(ti, dict) else (ti if isinstance(ti, str) else "")
    act = classify(cmd)
    if act[0] == "deny":
        if act[1] == "find":
            reason = (f"graphify blocked `find -name \"{act[2]}\"` — locating a file by its ROLE is the leak the graph replaces. "
                      f"List every symbol in matching files with file:line via the on-graph path filter:\n{PATHFILTER}\n"
                      "`<path-fragment>` is any slice of the path (a directory, or the hyphenated filename `explain` rejected). "
                      "Enumerating a KNOWN dir by extension (`find <dir> -name \"*.ts\"`) is fine — that is not locating by role.")
        else:
            reason = (f"graphify blocked a recursive grep for the symbol `{act[2]}` — that is exactly what `graphify affected` is for. "
                      "Every usage/reference of a symbol across the repo -> `graphify affected \"<Symbol>\"` (complete caller list, "
                      "including re-exports a text grep misses). Its definition/members -> `graphify explain \"<Symbol>\"`. "
                      "Recursive grep is only for raw text the graph can't index (a UI label, an error string with spaces).")
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                                 "permissionDecision": "deny",
                                                 "permissionDecisionReason": reason}}))
    elif act[0] == "nudge":
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                                 "additionalContext": NUDGE}}))


if __name__ == "__main__":
    main()
