#!/usr/bin/env python3
# PreToolUse(Read|Glob|Grep) for a repo with a graphify graph:
#  - Grep TOOL with a by-role SYMBOL pattern (camelCase / PascalCase /
#    SCREAMING_SNAKE, including regex alternation A|B|C) -> RUN the graph and
#    embed `graphify explain` output in the deny, so the model gets the complete
#    answer in the SAME turn. If the graph does not know the symbol, downgrade to
#    a non-blocking nudge so the Grep still runs.
#  - otherwise a non-blocking nudge for code reads / greps.
# Never denies a string-literal pattern (has a space), a kebab-case selector
# (app-foo-bar), or a lone word (todo, TODO). decide() is pure + unit-tested.
# Whole-file reads are NOT blocked: an A/B run showed forcing windowed reads
# fragmented them into extra turns with no accuracy gain — reading a file you
# need is legitimate, and the grep->explain injection already prevents the
# read-to-find-relationships anti-pattern.
import re, sys, json, shutil, subprocess

CODE_EXTS = ('.py', '.js', '.ts', '.tsx', '.jsx', '.go', '.rs', '.java', '.rb', '.c', '.h',
             '.cpp', '.hpp', '.cc', '.cs', '.kt', '.swift', '.php', '.scala', '.lua', '.sh',
             '.md', '.rst', '.txt', '.mdx')

NUDGE = ("graphify: mapping callers/callees/imports of a known symbol? `graphify explain \"<ExactSymbol>\"` "
         "returns them with file:line, cheaper than reading whole files; `graphify affected \"<Symbol>\"` for "
         "change impact (the COMPLETE usage list when explain shows \"... and N more\"). Do not use "
         "`graphify query` — it BFS-floods seed neighborhoods and never returns the matching names. "
         "Read files to modify or debug code.")

GREP_PREAMBLE = ("graphify intercepted this Grep and ran the graph for you — the complete definition + "
                 "caller/import map is below, so there is NOTHING to re-run. When a symbol's connections "
                 "end with \"... and N more\", that is `explain`'s 20-connection cap: run "
                 "`graphify affected \"<Symbol>\"` for the COMPLETE usage list. Grep stays reserved for "
                 "raw text the graph can't index (a UI label / error string with spaces, template markup).\n\n")


def _is_symbol(t):
    if re.search(r'[a-z][A-Z]', t):
        return True
    if t[0].isupper() and any(c.islower() for c in t):
        return True
    if "_" in t and any(c.isalpha() for c in t):
        return True
    return False


def _tokens(pat):
    return [t.strip("\\") for t in re.split(r'\\?\|', pat or "") if t.strip("\\")]


def grep_is_by_role(pat):
    p = pat or ""
    if not p or " " in p:
        return False
    cleaned = []
    for t in _tokens(p):
        m = re.fullmatch(r'[\\^$.*+?()\[\]{}]*([A-Za-z_][A-Za-z0-9_]*)[\\^$.*+?()\[\]{}]*', t)
        if not m:
            return False
        cleaned.append(m.group(1))
    return bool(cleaned) and any(_is_symbol(t) for t in cleaned)


def decide(d):
    tool = d.get('tool_name', '')
    ti = d.get('tool_input', d)
    if not isinstance(ti, dict):
        ti = {}
    if tool == 'Grep':
        pat = ti.get('pattern') or ti.get('query') or ''
        return ("deny", pat) if grep_is_by_role(pat) else ("nudge",)
    raw = str(ti.get('file_path') or ti.get('path') or '')
    fpl = raw.lower().replace('\\', '/')
    if 'graphify-out/' in fpl:
        return ("allow",)
    if fpl.endswith(CODE_EXTS):
        return ("nudge",)
    return ("allow",)


def _run(args):
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=8)
        return (r.stdout or "").strip()
    except Exception:
        return ""


def inject_grep(pat):
    if not shutil.which("graphify"):
        return None
    syms = [t for t in _tokens(pat) if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', t) and _is_symbol(t)]
    blocks = []
    for s in syms[:2]:
        out = _run(["graphify", "explain", s])
        if out and "No node matching" not in out:
            blocks.append("$ graphify explain \"%s\"\n%s" % (s, out))
    return GREP_PREAMBLE + "\n\n".join(blocks) if blocks else None


def _emit(obj):
    print(json.dumps({"hookSpecificOutput": dict({"hookEventName": "PreToolUse"}, **obj)}))


def main():
    try:
        d = json.load(sys.stdin)
    except Exception:
        return
    act = decide(d)
    if act[0] == "deny":
        inj = inject_grep(act[1])
        if inj:
            _emit({"permissionDecision": "deny", "permissionDecisionReason": inj})
        else:
            _emit({"additionalContext": NUDGE})
    elif act[0] == "nudge":
        _emit({"additionalContext": NUDGE})


TESTS = [
    ({"tool_name": "Grep", "tool_input": {"pattern": "VariableStrategy|variableStrategy|VariableTypeStrategy"}}, "deny"),
    ({"tool_name": "Grep", "tool_input": {"pattern": "VariableStrategy"}}, "deny"),
    ({"tool_name": "Grep", "tool_input": {"pattern": "VARIABLE_STRATEGIES"}}, "deny"),
    ({"tool_name": "Grep", "tool_input": {"pattern": "getVariableType"}}, "deny"),
    ({"tool_name": "Grep", "tool_input": {"pattern": "Save changes"}}, "nudge"),
    ({"tool_name": "Grep", "tool_input": {"pattern": "todo"}}, "nudge"),
    ({"tool_name": "Grep", "tool_input": {"pattern": "TODO"}}, "nudge"),
    ({"tool_name": "Grep", "tool_input": {"pattern": "app-condition-right"}}, "nudge"),
    ({"tool_name": "Grep", "tool_input": {"pattern": "error: \\d+"}}, "nudge"),
    ({"tool_name": "Read", "tool_input": {"file_path": "/x/foo.ts"}}, "nudge"),
    ({"tool_name": "Read", "tool_input": {"file_path": "/x/graphify-out/graph.json"}}, "allow"),
    ({"tool_name": "Read", "tool_input": {"file_path": "/x/data.csv"}}, "allow"),
]

if __name__ == "__main__":
    if "--test" in sys.argv:
        bad = 0
        for payload, exp in TESTS:
            got = decide(payload)[0]
            ok = got == exp
            bad += 0 if ok else 1
            print(("PASS" if ok else "FAIL") + f"  exp={exp:5} got={got:5}  {json.dumps(payload.get('tool_input'))}")
        print(f"\n{len(TESTS)-bad}/{len(TESTS)} passed")
        sys.exit(1 if bad else 0)
    else:
        main()
