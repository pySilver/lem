# Notes of the step `land-base` for other steps

What `start`, `base` and carry need in files `land-base` does not own. Each item names the file,
what to change, and why. `model/landing/carry.py`, `rebased.py` and `resolution.py` give the
rules; the steps that read coverage call them.

## For `core` (`records/landing/`): what the task's branch took in from origin

`Landing` has no field for the commit of origin's task branch whose commits the branch took in
(`taken` in `Task.own_remote` on `main`). The journey
`test_a_teammates_commit_on_the_task_branch_is_refused_until_the_branch_holds_it` shows the
gap: `base` refuses a teammate's commit, the builder runs `git pull --rebase`, and `base` takes
the branch onto the base; the rebase rewrites the teammate's commit, so origin's branch is again
a commit the tip does not hold and Lem did not push, and `base` is due and refuses it once more.
Asked: `Landing.taken: Sha | None`, written by `base` when the tip holds origin's task branch
(`world.remote_in_tip`), read by `model/landing/base.foreign` beside `pushed`, and by `propose`
as the push's lease while it is newer than `pushed`. Until then a teammate's commit on the task
branch needs a second pull after the rebase, or the owner's push.

## For `core` (`ports/git.py`): the branch a checkout is on

`notes/slice-land.md` asked for `branch_of(where) -> str | None`. `start` and `base` need it to
refuse a HEAD off the task's branch, a detached HEAD at the branch's own commit among them
(`off-branch`), and `base_stops.left` to name where HEAD is after an abort. Until the port has
it, `app/landing/head.py` reads it from the files git keeps (the worktree's `.git`, then `HEAD`),
as `store.places` reads `.git`, `gitdir` and `commondir`. With `branch_of` the module goes.

## For `core` (`ports/git.py`): a branch moved back to a commit

`main` starts a second rebase in one landing from the tip before Lem's first one, when the tip is
that rebase's own and nobody published it (`land.cmd_base`, `made`): a rebase onto a base that
held a commit's edit leaves the commit out, and a second rebase of what it left loses it for good
once the base takes the edit out again (`tests/lem-land-shop.sh`, mb-probe). The port has no act
that moves a branch back. Until it has one (`reset(worktree, commit, expect)`), `base` refuses
`rebase-again` with the owner's `git reset --hard BEFORE`, and only when the first rebase left a
commit out (`base_facts.dropped`), so that a base that moved under a whole rebase rebases on.

## For `core` (`records/landing/start.py`): the reviewed tip a carry was judged for

`Based.carried` says that git's merge of the newest reviewed tip onto the base is the tip's tree,
and `carry.source` takes that review for the one `base` judged when it is older than `Based.at`.
A moment is to the second, so a review in the same second as `base` is no source (a needless read
again, never a wrong carry). Asked: `Based.reviewed: Sha | None`, the reviewed tip the carry was
judged for; `carry.source` then compares it.

## For `core` (`ports/git_facts.py`): a commit's author

`main` named a teammate's commits with their author (`Task.own_remote`). `Commit` has the sha, the
parents and the subject; the refusal names the sha and the subject. Asked: `Commit.author`.

## For `core` (`ports/git.py`, the `git` adapter is `land-base`'s): patch ids

`Commit.patch_id` is never filled by `git_cli` (nor by `ModelGit`). `main` named each commit a
rebase left out because the base holds its patch (`land.left_out`, `git log --cherry-mark`), in
the line of a rebase that could not be shown to keep the change and in the conflict's fix
(`git rebase --reapply-cherry-picks`). `model/landing/base.After.left_out` and
`rebased.why_unshown` take them; `app/landing/base_after.py` gives none. Filling `patch_id`
costs one `git log -p` and one `git patch-id` for every `commits` call; a port fact
`left_out(where, onto, tip) -> tuple[Commit, ...]` costs one `git log --cherry-mark`, only when
a rebase is not shown. Asked: the second.

## For the owner of `app/landing/world.py` and `model/landing/world.py`

1. **A branch that brings its own checks.** `branch_checks.gathered` supplies the first
   commands and marks `World.rules.own_checks`. The checks keep that fact in
   `Checked.own_checks`, and the proposal requires the owner to merge.
2. **The forge's call of a conflict.** `PullSeen` has no `mergeable`. `lem land start
   --conflicting` asks the forge itself (`app/landing/start.called`) and starts the new round
   whatever step was due. Asked: `PullSeen.mergeable`, so that `phases.opened` names
   `lem land start SLUG --conflicting` when the forge calls the pull request conflicting at its
   proposed head (`land-merge`), and the duty's wake reads the same fact (`board-duties`).

## For `land-review` (`model/landing/review.py`)

Review coverage over a rebase is `carry.covers(landing, world)`: the newest answered review of
the change read the tip now, or `base` showed by git's merge that the tip it read is the tip now
on this base (`carry.source`). `review.holds` compares `last.tip` with the tip only. A must-fix
the review left stays open through the carry: `review.holds` keeps refusing it. The resolution
of a conflict is `Landing.resolution`, written by `base` with `after == before` while a builder
resolves it and with his tip once he rebased; its one read is due while `read` is None (`landing.md`
E, "Conflicting PR on the forge"). Why no review carried is `rebased.why_unshown(landing.based)`.

## For `land-merge` (`model/landing/mergeread.py`, `phases.py`)

A merge read carries over a clean rebase by `carry.read_carries(landing, world)` and over a
conflict by `resolution.carries(landing, world, careful=...)`; each gives the `MergeRead` to
record, with `carried_from`, and each holds only for the merge agent's newest read of the tip
proposed before, when that read gave a real verdict (`carry.latest`: an older verdict never
stands in for a newer unusable answer). The count of rounds after the first is
`Landing.relands`, and each round's `LandAgain` entry is in the journal: the merge brief shows it
(`landing.md` E, "Relands"). `lem land start --conflicting` starts a round only while
`reconcile.pending` gives nothing and the forge's head is the proposed tip.

## For `land-propose`

- The owner's standing merge over a new round is `standing.standing(landing, digest,
  carried=...)`, with `carried` from `carry.proposed_carries(landing, world)` or
  `resolution.tip_carries(landing, world, careful=...)`: it stands only for his merge of the tip
  proposed before, that tip on the same base or carried onto the tip now, and the same reasons.
- The teammate's refusal of `propose` (`landing.md` E, "Teammate commit") reads the same commits
  `base_facts.teammates` names, and the push's lease waits for `Landing.taken` (above).

## For `land-checks`

`base` keeps a polish pass through its rebase: `polished.after` takes the name of the commit as
far from the new tip as it was from the tip before while the rebase kept each commit, and is
cleared when it dropped one (`app/landing/base_polish.py`); after a builder's resolution the tip
before is the conflict's. `checks.polished` (yours) holds while that commit is in the tip.

## For `task`

- `lem task move SLUG ready` from `landing` is refused by the slice's `move`; the journeys of
  `land-base` write the record back to `ready` themselves, as a red base does. A start over
  (`--start-over WHY`) is yours: `start` keeps `Started.start_over` and the round of a landing in
  `preparing` as they are, and starts a new round only from `open`.
- `start` refuses a task that any hold but its own block keeps (`held`), and clears only the
  block it set itself (`start_said.NO_CHECKS`).

## For `tree` (or whoever owns `tests/unit/landing/test_decisions.py`)

The cases of `start` and `base` moved out of `test_decisions.py` into `tests/unit/landing/
test_start.py` and `test_base.py`, since both decisions now read facts beside the world.
