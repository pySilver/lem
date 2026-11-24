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

- (a) Nothing now. Cost: as above, after each such cut-off.
- (b) A record of the rebase kept before it runs (`from` and `onto`), which the next run finishes
  when it finds the branch already on the base. Cost: one more key of `landing.json`, which the
  release before must read without harm, so two releases.

The unknown that settles (b): whether a landing's step is ever cut off between its rebase and its
keep; nobody has counted it.

Seen in a review of `cmd_base` by a backlog worker, 2026-11-24.
