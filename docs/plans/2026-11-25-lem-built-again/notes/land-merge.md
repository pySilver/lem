# Notes of the step `land-merge`

What the merge's end of the landing needs in files it does not own. Each item names the file,
what to change, and why, and what `land-merge` does meanwhile.

## For `core` (`records/landing/merge.py`)

1. **`MergeAccepted` keeps no `by` and no `via`.** When the forge's queue merges, `lem land
   merged` cannot say who asked for the merge, so it writes it `by: owner, via: github`, as the
   slice did; a queue's end is written with the proposal's `who_acts` as `by`. Asked: `by` and
   `via` on `MergeAccepted`, written from the intent it replaces (`app/landing/merge_called.py:
   held`), which `app/landing/merged.py: adopted` then reads.
2. **The owner's explicit word after his check of GitHub** needs no new field: with an intent
   on record and only an open pull request visible, a new call goes only on `lem land merge
   SLUG --by owner --tip TIP --checked MOMENT`, the moment of that call, which the refusal
   that asks him to check GitHub prints and the first command cannot carry
   (`app/landing/merge_word.py`). The word is noted as an `OwnerAct` with what the forge
   showed. `--checked` is a new option of `lem land merge`; `tests/unit/cli/tree.json` is
   written again for it (for `tree`, and `surfaces.md` A's row of `land merge`).
3. **`Checked` has the base's sha, not its tree.** A move of the base is read by tree
   (`landing.md` D: a revert or an empty commit moves nothing), so each merge step reads
   `git.tree(checked.base)` again (`app/landing/merge_world.py: checks_tree`). A `base_tree`
   on `Checked`, which `checks` writes, saves that call and lets `phases.due` say it.

## For the owner of `model/landing/world.py` and `app/landing/world.py` (no step's row names them)

4. **`PullSeen` drops the forge's `dequeued` and `mergeable`.** `ports.forge_facts.Pull` has
   both; `app/landing/world.py: seen` copies neither. Meanwhile the merge's end asks the forge a
   second time for `dequeued`, only for an open request that waits in no queue
   (`app/landing/merge_world.py: dequeued_of`). Asked: both fields on `PullSeen`, copied by
   `seen`; then `dequeued_of` reads `world.pull.dequeued`.

## For `land-propose` (`adapters/forge_gh_pulls.py`)

5. **A merge that keeps the branch's commits.** `branch.history = "keep"` calls the forge with
   the method `rebase` and an empty subject and body (`model/landing/merge_call.py`). The gh
   adapter refuses every method but its `METHODS` by name, naming `land-merge`: it needs
   `--rebase` with no `--subject` and no `--body`. `LocalForge` takes it already, so the journey
   `test_a_merge_that_keeps_the_branchs_commits_rebases_and_its_parent_is_the_old_base` passes on
   the stand-in only.
6. **The fixes made on the way in the one commit.** `main:land.squash_body` copied the lines
   under `## Fixed on the way` of the pull request's text into the squash's body before the
   moved line. The section is propose's; `merge_lines.squash_body(slug, moved)` takes no lines
   of it. A function of propose that gives those lines from the proposal's text, which
   `merge_call.merging` puts first, closes it.
7. **The subject of a squash is kept as given** (the trial of the skeleton on GitHub, 2026-11-25):
   `LocalForge.merged` adds ` (#N)`, GitHub does not. The journeys of `land-merge` read only
   `startswith(SUBJECT)`.

## For the owner of `app/landing/say.py` and `app/landing/step.py` (the slice's, no row names them)

8. **`next` names inputs its command does not hold, and repeats a brief's command.** `say.py`
   adds `INPUTS` ("TITLE and SUBJECT ..., FILE ...") to the why of any command with words, and
   after a brief names the bare command again (the trial's finding 1). The merge's four steps and
   `lem land next` no longer use it: `app/landing/following.py` names, for each step, only the
   placeholders of its own command, a merge that keeps the branch's commits with no
   `--message`, and after the merge agent's brief the form that writes its reply down with the
   brief's own `--tip` and `--base` (`act: spawn`, `job: merger`). `lem land read`'s brief is
   `land-review`'s; `say.following` can call `following.following` once the other steps take it.
9. **A step the record alone refuses still looks at the forge.** `step.landed` gathers the world
   (a fetch, `gh pr view`) before it checks the due step. The merge's steps use
   `app/landing/merge_step.py`, which refuses from the record alone first (`phases.settled`: a
   task not ready, one that ended, a landing after the forge's merge), and `lem land next`
   answers those from the record (`app/landing/next.py`). `step.landed` can do the same.

## For `land-text` (`skills/lem/prompts/merge.md`, `stages/land.md`)

10. **The brief.** Its first line names `skills/lem/prompts/merge.md` under `lem version`'s
    `root`, and the facts are main's keys (`task`, `worktree`, `task_directory`,
    `pull_request` with its address, `tip`, `range`, `diff`, `changed`, `track`, `files`,
    `reviews`, `decisions`, `green`, `not_green`, `careful`, `land`, `owner_merges`,
    `relands`, `pictures`, `filed`, `stand_ins`, `try`, `base`, `moved`). Not given yet: `time`,
    `tokens`, `bar` and the seat (`merge_seats`). The reply is `Verdict: merge.` or `Verdict:
    call.` with a sentence; on a moved base, `Base: safe.` or `Base: another round.` with one.
    `lem land merge-review SLUG --no-answer --tip T --base B` writes an agent that ended with
    none.
11. **A moved base.** A merge on a base that moved after the read is tried and refused `base`
    (`Refused` of Lem kept for the tip, and the owner's merge standing); then `merge-review` is
    due. After GitHub refused a tip, `next` names the owner's merge (a wait): only his word
    (`--by owner --tip TIP`) merges that tip.

## For `addons-flow` and `sessions`

12. The removal of a reviewer's item at the landing (`main:land.remove_item`) and the merge
    agent's seat with its stand-in on the same brief (`merge_seats`, `merger_noted`) were not
    built here; their ledger rows are in `tests/ledger/moves/land-merge.tsv`.

## After the join of `rebuild` (land-base, land-propose, criteria, land-review, settings)

13. **For `land-propose`: the carried merge read and the standing merge are written at the
    proposal.** `carry.read_carries(landing, world)` and `resolution.carries(landing, world,
    careful=...)` read `landing.proposed` as the tip proposed before, so only `propose`, before
    it writes the new proposal, can call them. Asked: `propose` appends the read they give to
    `landing.reads` (with `carried_from`) and sets `Proposed.merge_review = "carried"`; the
    merge's end then takes it as the read that covers the base (`mergeread.latest(landing,
    base_tree)`), with no new brief. Likewise `standing.standing(landing, digest, carried=...)`
    at the proposal: `propose` writes its `OwnerMerge` into `Proposed.owner_merge`. The merge's
    end reads that judgment for a standing merge of an earlier tip
    (`merge_standing.standing_of`), and for the same tip calls `standing.standing` itself with
    the reasons read again now. Only the owner's own word makes a `Standing`
    (`merge_standing.kept`): `standing.py` judges one, it never makes one.
14. **For `core` and `land-propose`: the criteria's contract mark on the proposal.**
    `criteria`'s `contract.moved(task, seen)` needs the mark the proposal was made under
    (`Proposed.contract`, asked in `notes/criteria.md`). Until it exists, the merge agent's
    authority is refused when the newest approval of the criteria is later than the proposal
    (`merge_asked.contract_moved`); with the field, it calls `contract.moved(task,
    proposed.contract)` instead.
15. **The green reasons under the lock.** `green.reasons(record, careful)` takes the careful
    reasons that only `propose` reads (the settings' edit); the merge's end reads them again
    with the fast track's careful lines taken from the proposal (`merge_standing.reasons_now`).
