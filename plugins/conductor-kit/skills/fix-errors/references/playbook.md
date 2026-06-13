# fix-errors — playbook

The default behavior, loaded only when Discovery-first Dispatch found no user error-fixing skill.
Grounded in Conductor's extracted Fix Errors default (`I3t`), expanded with the named intrinsic
additions.

Conductor's bare default is *"fix the failing CI actions from the attached logs."* That assumes
Conductor attached the logs. The skill body's Fallback Chain already resolved the failing logs even
when nothing was attached (terminal output, then `gh run view --log-failed`, then local reproduction);
this playbook fixes whatever those logs show.

## Steps

1. **Read the error end to end** before touching code — the root cause is usually named in it.
2. **Trace the failure to its cause** in the source (use the repo's navigation tooling where
   available). Distinguish "the code is wrong" from "the test/expectation is wrong" — fix whichever is
   actually incorrect, and say which it was.
3. **Apply the minimal correct fix.** Fix the root cause — never silence, skip, or `|| true` an error
   away. No drive-by refactors, no broad rewrites to dodge a narrow bug.
4. **Re-run to confirm green.** Run the same targeted command (the single failing test file, the one
   package's build, the specific type-check — not the whole suite) and confirm it passes with real
   output. Redirect long output to a file under `/tmp` and read that rather than re-running. If the
   fix surfaced a second failure, repeat — do not declare success on a partial fix.

## Edge cases

- **No PR / no `gh` / nothing attached:** the chain already fell through to local reproduction — run
  the project's CI command yourself to surface the failure, then fix it.
- **Genuinely out-of-scope red:** if a failure is unrelated to the work and out of scope, report it
  explicitly rather than papering over it.
