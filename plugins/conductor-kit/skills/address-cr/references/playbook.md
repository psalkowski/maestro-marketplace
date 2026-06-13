# address-cr — playbook

The disciplined edit loop, loaded only when Discovery-first Dispatch found no user review-addressing
skill. Additive action — Conductor has no native button for it.

The skill body resolved and normalized the comments into the uniform block defined in
`../../../references/review-comment-format.md` (`File:` / `Lines:` / body, plus GitHub identifiers when
present). Work that block one comment at a time.

## The edit loop (per comment)

1. **Understand it.** Read the comment with its `File:` / `Lines:` anchor and the surrounding code.
   Be sure you know what the reviewer is actually asking for before changing anything.
2. **Decide: accept or push back.** Don't blindly implement. If the suggestion is wrong, would break
   something, or rests on a mistaken assumption, flag it and explain why instead of applying it. A
   suggestion block is a proposal, not an order — verify it before applying.
3. **Apply the change** when accepted — the minimal correct edit at the anchored location. No drive-by
   refactors beyond what the comment asked.
4. **Verify.** Run the targeted test / type-check / build covering the changed code and confirm it
   passes with real output. Don't mark a comment done on an unverified edit.
5. **Reply / resolve the thread** when the comment came from GitHub and is resolvable: use `gh api` to
   post a reply to the thread (referencing the `Thread ID:` / `Comment ID:`) and resolve it. For
   comments sourced from args/attachments or the Ephemeral Review Store, there is no thread to resolve
   — just note in the reply that it was addressed.

## Finish

Report, per comment: accepted vs pushed-back (with reason), the files changed, the verification
result, and which GitHub threads were replied to / resolved. List anything you deliberately did not
do and why.
