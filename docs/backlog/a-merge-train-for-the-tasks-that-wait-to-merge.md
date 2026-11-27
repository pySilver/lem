---
worth: later
where: src/lem/model/landing/merge_evidence.py:base_side
added: 2026-11-24
---
# A merge train for the tasks that wait to merge

Today Lem merges one task at a time under the workspace lock, and reads the base after it takes the
lock. When the base moved after a task's checks, the merge agent's merge waits until the agent reads
what moved and says `Base: safe.`; a task the owner approved instead runs the checks on the task
rebased onto that base before its merge (his ruling of 2026-11-25, the merge line); a pull request that GitHub calls conflicting lands again (`start
--conflicting`, `base`, the checks, the review that is due, `propose`). GitHub's merge queue is not
open to a repository a person owns (`docs/plans/2026-11-20-a-session-for-each-task.md`, "Lem is the
queue").

A merge train tests ahead: task B's checks run on the base with task A in it, task C's on the base
with A and B, all at the same time, and the tasks merge in that order. A red car leaves the train,
and the cars behind it are built again without it.

The numbers of this repository under Lem 0.3, from `.lem/state/events.jsonl`, 2026-11-17 to
2026-11-24 (the cutover of 2026-11-27 removed that file):

- 81 tasks reached `merge.start`; 42 of them landed again, 83 times (`land.again`).
- From `land.again` to the next `proposed` of the task: 26.4 minutes at the median, 84.4 at p90.
  This is the clock, with the waits of the load gate in it, and the tasks overlap.
- The merge agent's read of the base came first on 2026-11-22 at 21:55 UTC. Before it, 67 landings
  again, 55 of them with no conflict; after it, 16, 14 of them conflicting. Of 58 reads with a base,
  38 said safe and 2 another round.

A train takes away almost none of what is left: a conflict needs a builder's resolution in a train
too. What it adds is a run of the checks on the tree that lands, where `Base: safe.` is a read of a
diff and runs nothing. Two tasks green alone and red together pass that read when the reader misses
the link. Nothing on record shows that case yet: 8 tasks waited for a red base (`task.state` "the
base is red", 2026-11-19 to 2026-11-23), and the two repairs read for this item name timing races
in the tests, not two merges.

Options:

- (a) Nothing now; the base read stays the guard. Cost: none.
- (b) A train of one car: before a merge on a `Base: safe.` read, run the checks on the tip rebased
  onto the base now, with no new review, as the merge line already does for a task the owner
  approved. Cost: one run of the checks for each merge after a move.
- (c) The full train: the cars' checks in parallel under the load gate, the merges in order, a red
  car out and the cars behind it built again. Cost: a large change to the landing (17,781 lines in
  `src/lem/app/landing/` and `src/lem/model/landing/`, 2026-11-27), more load on a laptop, and the pull request's head has to be the car's tree, so each
  car's branch is pushed again before its merge.

Recommendation: (a). Take (b) when one red base goes back to a merge on a safe read. Take (c) only
when a project's checks are long enough that one run after another is the wait the owner feels
(unmeasured estimate: no project with Lem has such checks today).

Raised by the owner on 2026-11-24. His question of 2026-11-23 is the same one: "It should be smart
enought to postpone execution until the dependency is merged ... Is that smart? Or it will be
massive slowdown and PR/fix coflicts is a better design?"
