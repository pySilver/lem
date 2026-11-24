---
worth: later
where: src/lem/land.py:cmd_base
added: 2026-11-24
---
# A cut-off around lem land base loses the record of the rebase that made the tip

A task lands again after its base moved. Its pull request proposed tip `P`, and `lem land base`
rebases `P` with no conflict to `T`. `cmd_base` keeps `rebase_carried` (`from: P, to: T`) in its
one `task.keep(**updates)` at the end, and `propose` reads it through `tip_carry`, so that the
merge review and the owner's standing merge carry from `P` to `T`. Two cut-offs lose that record:

1. The step is cut off after the rebase and before `task.keep(**updates)`. The branch is at `T`
   and nothing of the rebase is kept. The next `lem land base`, with the base where it was, finds
   nothing to rebase, so the tip does not move, and `updates` writes `rebase_carried: None`.
2. `propose` pushes `T`, keeps `pushed: T`, and is cut off before it keeps `proposed`. A second
   `lem land base`, with the base where it was, skips the return to `made.from`, since the tip is
   the one pushed; the tip does not move, and `updates` writes `rebase_carried: None` over the
   record of `P` to `T`.

Then `propose` of `T` reads no rebase. `tip_carry` at c674b18d gives `('rebase', None)` with the
record and `(None, 'a commit came after the tip proposed before')` without it. So the merge review
does not carry, a fresh merge agent reads the task, and the owner's standing merge ends, each with
a reason that names a commit that never came. Nothing unsafe merges: the cost is one more read and
one more act of the owner, under a false reason. Both cut-offs were read in the code, not run.

- (a) Nothing now. Cost: as above, after each such cut-off.
- (b) A `base` whose tip does not move keeps `rebase_carried` and `rebase_uncovered` as they are,
  where today it writes None. It closes the second cut-off, since each record names its tips and a
  record of another tip carries nothing. Cost: a few lines and a case in `tests/lem-land-shop.sh`.
- (c) (b), and a record of the rebase kept before it runs (`from` and `onto`), which the next run
  finishes when it finds the branch already on the base. It closes the first cut-off too. Cost: one
  more key of `landing.json`, which the release before must read without harm.

Recommendation: (b). The unknown that settles (c): whether a landing's step is ever cut off between
its rebase and its keep; nobody has counted it.

Seen in a review of `cmd_base` by a backlog worker, 2026-11-24.
