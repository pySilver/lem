# Notes of the step `land-propose`

What `land-propose` needs in files it does not own, the stand-in it built meanwhile, and the
facts the next steps take from it.

## For `core` (`ports/forge_facts.py`): the author of a pull request

Today's refusal of a pull request on the task's branch at a head Lem did not push names its
number and its author (`main:land.cmd_propose`, "pull request #N by AUTHOR is open on BRANCH").
`Pull` has no author. Asked: `Pull.author: str | None` (gh's `author.login`). Meanwhile the
refusal `foreign-pull` names the number and the head.

## For `core` (`tests/fakes/forge.py`): a squash keeps its given subject (done, on the orchestrator's word)

On real GitHub `gh pr merge --squash --subject S` keeps S as it is (trial-skeleton,
2026-11-25). `LocalForge.merged` added ` (#N)` to it. On the orchestrator's word `land-propose`
made the one change: a given subject is kept; with none, the forge's own is the title and
` (#N)`. The skeleton's case of the squash's subject now asserts the subject as given.

## For `land-merge`: what the adapter and the fake do now

- The squash's subject is kept as given (above): a merge that wants `(#N)` writes it itself.
- `forge_gh.merge(n, head, "rebase", text)` is built: `gh pr merge --rebase`, and the base is
  the commit before the first one the rebase replayed (the merge commit's first parent, as many
  times as the pull request has commits: `gh pr view N --json commits`). A pull request someone
  merged on GitHub is read with its merge commit's first parent, whatever the method: a rebase
  merge made outside Lem reports the parent of its last replayed commit. If `merged` needs the
  base of such a merge, `Forge.pull` needs to know the method; say so here.
- A text goes to `gh` on its standard input (`--body-file -`), the merge's body too.
- A `gh` that is not on the PATH is refused `no-gh`, one with no login `gh-login`, each with its
  fix; neither is ever read as "no pull request".
- `Proposed.text` cites the published body `pr-ROUND-DIGEST.md` once the forge took it;
  `text_waits` is left for `merged`'s edit (the seam `seam:pr-text-edit-fails`).
- `Proposed.merge_review` and `owner_merge` are never set by `propose`: they come from the
  carry over a moved base (`land-base`'s `carry`), which `propose` should call once it exists.
  Until then a new round always gets a fresh merge read, and no standing merge carries.

## For `land-base`: what a new round's proposal takes from the carry

`propose` reads `landing.pull` on record (or, with none, the open one at Lem's push), pushes
with the lease of `landing.pushed`, and edits the one pull request (journey
`test_a_new_round_edits_the_one_pull_request_and_opens_no_second`, where the test writes the
record of round 2 by hand, as `start` from `open` would). Today's text also has a line of what
bringing the task onto a moved base did (`main:land.synced`, `sync_line`) and the `proposed`
event's carried facts: both need the carry's result on the record (a field of `Based` or of
the round), which `pr_head.blocks` would print after the careful line.

## For `core` and `land-base` (`ports/git.py`, `adapters/git_cli_acts.py`): push the checked commit

The review of 2026-11-25 (finding 1) found again what the slice's review found: `Git.push(worktree,
branch, expect)` pushes `refs/heads/BRANCH:refs/heads/BRANCH`, the worktree's branch as it is at
the push. A builder's commit between `propose`'s read of the branch and the push goes to origin,
and, in a new round, becomes the open pull request's head. `propose` narrows it and never writes
it down as checked: it refuses when the branch is not the checked tip before the push, and after
it records the commit git sent and refuses when that is not the checked tip
(`app/landing/propose_push.py: sent`, `pushed`). Only the port closes it. Asked, as
`notes/slice-land.md` asked core first: `Git.push(worktree, branch, expect, commit: Sha)`, which
pushes `COMMIT:refs/heads/BRANCH` with the lease on the destination, and the same in `ModelGit`
and the Git contract. `propose` then passes `world.tip`.

## For `task`: a branch of the task's own

`main` read the worktree's current branch at each step, so its fix for somebody else's pull
request on the task's branch was `git branch -m NEW-NAME`. Here the branch is on the task's
record (`app/tasks/where.branch`), so a rename alone gives the task no other branch;
`foreign-pull`'s fix now asks the owner to close that pull request. A command that renames the
task's branch with its record (and `Git.branch_of`, asked in `notes/slice-land.md`) would let the
fix name it again.

## For `land-review`: Jev's adapter, and the floor of a careful change

- `propose` asks Jev through the `Judge` port once about each finding called under the bar (each
  item the branch adds with `worth: no`, each `under:` line of the parts that name a finding
  nobody filed), keeps its word in the task's `jev.json`, refuses once (`jev-over`) when Jev
  reads one at 0.7 or more, and ends each such line with `Jev: 0.85` or `Jev: not asked (why)`
  (`model/landing/propose_jev.py`, `app/landing/propose_jev.py`, `propose_marks.py`). With no
  adapter (`judge_jev` not built) each finding is "not asked" with that reason. A field of the
  record for Jev's words would replace `jev.json` (for core). `main`'s second refusal of an item
  that still says `worth: no` with no `Decided against:` line after Jev's refusal is not built.
- A careful request whose newest review was not the full set is refused `review-floor` by
  `propose`; `review.floor` knows only the shape's topics, so after that refusal `lem land read`
  is not due and asks for nothing (journey
  `test_an_edit_of_lems_settings_needs_the_full_set_and_the_owner_merges_it` writes the full
  set's record by hand). The floor wants every careful reason: `model/landing/propose_careful.why`.
- Two attempts nobody answered after an answered review of another tip are a reason of not green
  (`green.silent`); `review.holds` still asks for another read there, where `main`'s `due_of`
  sent it to the owner.
- A `same` finding whose open item left the tip is refused `item-gone`, and an over-bar one whose
  open item says `worth: no` at the tip is refused `item-refuted` with `lem land file SLUG
  --again`, which the filing step builds.

Also: `Reviewed` has no `verdict`; the text calls a review `must-fix` when it left one, else
`clean`, as `main` did with the counts.

## For `land-checks`: the edited tests and the kinds the bar does not cover

Today's checks say which existing tests, snapshots and test configurations the change edits
(`main:land.edited_line`) and the kinds of files the bar has no marks for
(`checks.bar.not_covered`). `Checked` has neither. Fields `edited` and `not_covered` on
`Checked` (or on its bar) let `app/landing/pr_checks.py` print both lines again.

## For `criteria`: three facts the text and the gates read from the record

1. **The moment of his word to skip the read.** `Criteria.skip` is `yes` with no moment, so
   `propose` cannot refuse a lead that started before the word itself (today's
   `read_skipped`); it refuses one that started before his approval after it (`skip-late`).
   Either `lem criteria skip SLUG yes` refuses a word after a lead started, or `Criteria` keeps
   `skip_at`.
2. **The wait for his yes.** Today's read line says when the criteria began to wait for his yes
   and the approval that ended it (`criteria_waited`, `approval_said`). A field, for example
   `Criteria.waited: (since, ended_by approval number)`, written when the criteria's hold of
   the owner begins and when an approval ends it.
3. **The changes from his notes after the read.** Today's line counts them
   (`changed_after_read`). `Criteria.change` keeps only the newest; a count, or the changes
   with their moments, on `Criteria`.

Close group A reads `Criteria.waited` and `Criteria.changed` in the proposal, and their
writers are built:

- `model/task/holds.waiting` begins `Criteria.waited` when its topic is `criteria`. The
  interview that a fast task takes after it grows is a separate hold, with no wait.
- `model/criteria/waits.asked` begins a new wait after the owner's note.
  `model/criteria/approve.recorded` writes the number of the first owner or alone approval
  that ends the newest wait. A later approval leaves that number in place.
- `model/criteria/change.changed` appends the moment of each accepted change;
  `app/criteria/change.changing` writes no change twice on a retry.
- `PersonaRead.changes` is the count of `Criteria.changed` when the read ended
  (`model/criteria/reads.ended`), so the proposal counts the changes after a read by their
  order, also in the same second.

`tests/unit/criteria/test_history.py` drives each through the commands.

## For `sessions`: a stand-in that gave an error itself

Today's line of a stand-in that failed in turn says "then Codex gave an error too: ..."
(`stand_ins_of`, `failed_too`). `StandIn` has no field for it. Asked: `StandIn.failed_too:
error and words | None`, written when the stand-in's own start fails.

## For `owner`: the spans a task ran without him

Today's head line names each span the task ran without the owner, with the words that began and
ended it (`without_owner`, from the owner's away and back). The text names only the time since
the task's `mode` became `alone` (`Task.mode_since`). The owner's `Presence.changes` holds the
spans; a function of `model/owner` that gives a task's spans without him would let
`app/landing/pr_head.alone` name each again.

## For every landing step: the slice's test of the plain decisions

`tests/unit/landing/test_decisions.py` held three cases of green and `propose`; they moved to
`tests/unit/landing/test_green.py` and `test_propose.py` with their new arguments, and one line
of a review's case calls `green.reasons(record, ())`.

## For `core` (`pyproject.toml`, `uv.lock`): two libraries

One commit (`build(deps)`) adds `markdown-it-py` (the notes' headings and code blocks, loaded
only when `propose` reads the notes) and `python-frontmatter` (an item's head) with `uv add`,
as part 7 of the design names them.
