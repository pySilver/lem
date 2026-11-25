# A pull request that became conflicting

A part of `stages/land.md`, read only when GitHub calls this task's open pull request conflicting.
Each step it names is a step of `stages/land.md`.

After another task's merge, GitHub may call this task's pull request conflicting: `conflict` names
it in `lem waiting --task SLUG`, and the board's server wakes this session (`lem: SLUG conflict`),
or opens one for it. Bring it onto the base at once, and tell the owner the `why` in one line
first: the settings he approved are his word for this push. A pull request that is not conflicting
stays as it is: GitHub merges it as it is, and `/lem land` for it meets the moved base at step 8.
Run `lem land start SLUG --conflicting` first. Then use `lem land next SLUG` to find each step
that is due.

- `base`. Its conflict is step 2: a builder resolves it, and `base` runs again, finds the
  builder's rebase, and keeps the polish pass.
- `checks` on the new base; a red one is step 4.
- `lem land read SLUG` publishes the brief of one read of what the resolution changed
  (`resolution` and `range_diff` in the brief), or the full set for a careful request; start it as
  step 5 says. That read is no round. A finding of it is a review's finding like any other: its
  fix, and the round that `read` then asks for, are step 5, before `propose`; two rounds used go
  on to `propose`, not green, as step 5 says.
- `propose`, with the title of the last proposal (the pull request's title on GitHub, `pull.title`
  in the `result` of that `propose`) and `notes.md`: it pushes with a lease and keeps the pull request. Its
  `say` is your one line to the owner, as it is. Then `lem land next SLUG`: when it names the
  merge (the read of the resolution found nothing, and no call makes the request careful), the
  merge review of the tip before carried onto the new one, as step 7 says: start no merge agent.
  When it names `merge-review`, step 7, a fresh merge agent's read of the new tip.

The server wakes the session once for each head that conflicts.
