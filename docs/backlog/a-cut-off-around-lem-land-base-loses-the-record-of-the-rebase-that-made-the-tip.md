---
worth: later
where: src/lem/land.py:cmd_base
added: 2026-11-24
---
# A cut-off around lem land base loses the record of the rebase that made the tip

A task lands again after its base moved. Its pull request proposed tip `P`, and `lem land base`
rebases `P` with no conflict to `T`. `cmd_base` keeps `rebase_carried` (`from: P, to: T`) in its
one `task.keep(**updates)` at the end, and `propose` reads it through `tip_carry`, so that the
merge review and the owner's standing merge carry from `P` to `T`.

The step is cut off after the rebase and before `task.keep(**updates)`. The branch is at `T` and
nothing of the rebase is kept. The next `lem land base`, with the base where it was, finds nothing
to rebase, so the tip does not move, and it keeps the notes of the rebase before it, which name no
rebase to `T`. Then `propose` of `T` reads no rebase, and `tip_carry` gives `(None, 'a commit came
after the tip proposed before')`. So the merge review does not carry, a fresh merge agent reads the
task, and the owner's standing merge ends, each with a reason that names a commit that never came;
the pull request says "checked again on main, with no rebase needed". Nothing unsafe merges: the
cost is one more read and one more act of the owner, under a false reason. Read in the code, not
run.

The other window, a `propose` cut off after its push, was fixed on 2026-11-24: a `base` that moves
nothing keeps the notes of the rebase before it (`rebase_notes`).

The same cut-off loses a change. An outside review (Astra, 2026-11-24, git 2.55.0) ran `lem land
base` at `289241ed` on this history: the task changes `f` to `on` in one commit, the base takes that
commit by its patch and reverts it (`F off; S; F on; C A; B; P A; git revert --no-edit HEAD`, in the
review's notation). The review stopped the process after git's rebase returned and before Lem kept
anything. The branch and the index were the base's, the worktree was clean, the record was as
before, and the next `base` said "nothing to land". With the plain rebase of 2026-11-24 the step
itself refuses that rebase and keeps the loss (`rebase_uncovered`), but only at its end: a cut-off
before that keep leaves the same branch on the base with no record, and the same "nothing to land".
Read in the code, not run, for the plain rebase.

Two more windows of the same class, from the same review, read at `7f980474`: after a push and a
`propose` cut off before it kept the proposal, the base goes back to its commit before; then
`sync_line` still prefers the review the cut-off proposal carried (`carry["review"]`) until the
next proposal works it out again. And a `propose` cut off after it kept the new proposal and the
owner's merge, before it wrote the task `open`, leaves `tip_carry` taking `old == new` as the same
tip, whatever the base did meanwhile.

- (a) Nothing now. Cost: as above, after each such cut-off.
- (b) A record of the rebase kept before it runs (`from` and `onto`), which the next run finishes
  when it finds the branch already on the base. Cost: one more key of `landing.json`, which the
  release before must read without harm, so two releases.

The unknown that settles (b): whether a landing's step is ever cut off between its rebase and its
keep; nobody has counted it.

Seen in a review of `cmd_base` by a backlog worker, 2026-11-24.
