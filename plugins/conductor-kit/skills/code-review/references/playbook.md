# code-review — playbook

The default reviewer behavior, loaded only when Discovery-first Dispatch found no user code-review
skill. Grounded in Conductor's extracted Code Review default (`N3t`).

The diff was already resolved by the skill body; review that diff. Read surrounding code when the diff
alone is ambiguous — never guess what a changed function's callers expect.

## Is it a bug worth a comment?

Output a finding only when it meets all of these:

- It impacts accuracy, performance, security, or maintainability.
- It is discrete and actionable (not a vague "consider refactoring").
- It was introduced in this change (not pre-existing unrelated debt).
- The author would actually fix it if they saw it.
- It is on code provably affected by this diff, not a hypothetical.
- It is not intentional behavior the author clearly chose.

**Output all findings the author would fix; if there are none, prefer to output nothing.** Do not
manufacture findings to look thorough.

## Comment-construction rules

- State clearly **why** it is a problem.
- Use accurate severity — don't inflate a nit into a blocker.
- At most one paragraph per comment.
- No code chunks longer than 3 lines inside a comment.
- State the required inputs/scenario that triggers the issue when relevant.
- Matter-of-fact tone. No flattery ("Great job…", "Nice work…").
- One comment per unique issue — never bundle several issues into one comment.
- Use a ```suggestion block **only** for a concrete, ready-to-apply replacement, preserving the exact
  leading whitespace of the lines it replaces.

## What to review for

Correctness (logic errors, broken edge cases, wrong input assumptions, race conditions, swallowed
errors), consistency with neighbouring code and repo conventions (CLAUDE.md / AGENTS.md for touched
files), safety (secrets in the diff, injection, missing validation on new surfaces), and scope
(changes unrelated to the branch's apparent intent). Skip style nits a formatter or linter would catch.

## Output

The skill body resolves the output channel. Two cases:

- **`mcp__conductor__DiffComment` available:** post one comment per unique issue, anchored to the most
  relevant changed line, plain-text body. Then give a one-paragraph summary in the reply.
- **Terminal mode (no DiffComment):** write each finding to the Ephemeral Review Store
  `.context/reviews/<branch>.md` using the shared block shape defined in
  `../../../references/review-comment-format.md` — one `## Comment` section per finding with `File:` /
  `Lines:` / body, so address-cr can consume them. Create `.context/reviews/` with `mkdir -p` if it
  is absent. Then give the same one-paragraph summary in the reply. Optionally, when a GitHub PR
  exists and the user wants it, also post the findings to the PR via `gh`.

If the diff is clean, say so explicitly rather than inventing findings.
