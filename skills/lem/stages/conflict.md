<!-- lem: old form -->
# A pull request that became conflicting

A part of `stages/land.md`, read only when GitHub calls this task's open pull request conflicting.
Each step it names is a step of `stages/land.md`.

After another task's merge, GitHub may call this task's pull request conflicting: `conflict: true`
for it in `lem project waiting`, and the board's server wakes this session (`lem: SLUG conflict`),
or opens one for it. Bring it onto the base at once, and tell the owner the `why` in one line
first: the settings he approved are his word for this push. A pull request that is not conflicting
stays as it is: GitHub merges it as it is, and `/lem land` for it meets the moved base at step 8.
The steps:

- `lem land start SLUG --conflicting`, then `base`. Its conflict is step 2: a builder resolves
  it, and `base` runs again, finds the builder's rebase, and keeps the polish pass.
- `checks` on the new base; a red one is step 4.
- `lem land read SLUG` asks for one read of what the resolution changed (`resolution` in
  `read.json`), or the full set for a careful request; start it as step 5 says. That read is
  no round. A finding of it is a review's finding like any other: its fix, and the round that
  `read` then asks for, are step 5, before `propose`; a `due` of `owner` goes on to `propose`,
  not green, as step 5 says.
- `propose`, with the title of the last proposal (`title` in `landing.json`) and `notes.md`:
  it pushes with a lease and keeps the pull request. Its `synced` is your one line to the
  owner, as it is. With `"merge_review": "carried"` (the read found nothing, and no call makes
  the request careful) the merge review of the tip before carries onto the new one, as step 7
  says: start no merge agent. With `"merge_review": null`, step 7, a fresh merge agent's read of
  the new tip, for the reason `merge_review_why` gives.

The server wakes the session once for each head that conflicts.
