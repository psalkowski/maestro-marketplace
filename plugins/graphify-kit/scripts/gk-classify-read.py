#!/usr/bin/env python3
# PreToolUse(Read|Glob|Grep) for a repo with a graphify graph:
#  - Grep TOOL with a by-role SYMBOL pattern (camelCase / PascalCase /
#    SCREAMING_SNAKE, including regex alternation A|B|C) -> DENY and redirect to
#    `graphify affected`/`explain`.
#  - otherwise the existing non-blocking nudge for code reads / greps.
# Never denies a string-literal pattern (has a space), a kebab-case selector
# (app-foo-bar), or a lone word (todo, TODO). Logic in decide(); unit-tested.
import re, sys, json

CODE_EXTS = ('.py', '.js', '.ts', '.tsx', '.jsx', '.go', '.rs', '.java', '.rb', '.c', '.h',
             '.cpp', '.hpp', '.cc', '.cs', '.kt', '.swift', '.php', '.scala', '.lua', '.sh',
             '.md', '.rst', '.txt', '.mdx')

NUDGE = ("graphify: mapping callers/callees/imports of a known symbol? `graphify explain \"<ExactSymbol>\"` "
         "returns them with file:line, cheaper than reading whole files; `graphify affected \"<Symbol>\"` for "
         "change impact. Do not use `graphify query` — it BFS-floods seed neighborhoods and never returns the "
         "matching names. Read files to modify or debug code.")


def _is_symbol(t):
    if re.search(r'[a-z][A-Z]', t):
        return True
    if t[0].isupper() and any(c.islower() for c in t):
        return True
    if "_" in t and any(c.isalpha() for c in t):
        return True
    return False


def grep_is_by_role(pat):
    p = pat or ""
    if not p or " " in p:
        return False
    tokens = [t for t in re.split(r'[|]', p) if t]
    cleaned = []
    for t in tokens:
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
    fp = str(ti.get('file_path') or ti.get('path') or '').lower().replace('\\', '/')
    if 'graphify-out/' in fp:
        return ("allow",)
    if fp.endswith(CODE_EXTS):
        return ("nudge",)
    return ("allow",)


def main():
    try:
        d = json.load(sys.stdin)
    except Exception:
        return
    act = decide(d)
    if act[0] == "deny":
        reason = (f"graphify blocked a Grep for the symbol `{act[1]}` — that is what `graphify affected`/`explain` are for. "
                  "Every usage/reference across the repo -> `graphify affected \"<Symbol>\"` (complete list, including re-exports a "
                  "text grep misses). Its definition/members -> `graphify explain \"<Symbol>\"`. The Grep tool is only for raw text "
                  "the graph can't index (a UI label or error string with spaces, a kebab-case template selector).")
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                                 "permissionDecision": "deny",
                                                 "permissionDecisionReason": reason}}))
    elif act[0] == "nudge":
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": NUDGE}}))


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
