# Annex: the landing

An annex of `docs/plans/2026-11-25-lem-built-again.md`: the landing's tables, for the builders
of `slice-land`, `land-base`, `land-checks`, `land-review`, `land-propose`, `land-merge` and
`land-text`. Each row is one rule of the proof of concept on `main` at `bf6d2836`
(`skills/lem/stages/land.md` steps 1 to 9, `stages/conflict.md`, `stages/polish.md` or
`src/lem/land.py`, the symbol named), unless it is marked **new**. This annex is a map, not the
complete list: the behavior ledger is (the design's part 8). A builder takes the ledger rows of
its sources; a row this annex misses goes into the builder's fates file with its proof. Each row
of part E is also a `path` row of `tests/ledger/extra.tsv`, proved by its journey.

## A. The landing record (`records/landing.py`, frozen in `core`)

| Struct | Fields | Written by |
| --- | --- | --- |
| `Landing` | `round`, `relands`, `phase` (`preparing`, `open`, `merged`, `ended`), `pull` (number, url, title), `pushed` (the head Lem pushed last, or None), `started`, `based`, `polished`, `checked`, `reviews`, `filed`, `resolution`, `proposed`, `reads`, `standing`, `refused`, `intent`, `accepted`, `merged`, `cleaned`, `archived` | the steps |
| `Started` | `round`, `branch`, `base_ref`, `conflicting`, `start_over` (why, or None) | `start` |
| `Based` | `tip`, `base`, `before`, `carried`, `unshown` (paths, commits, or None) | `base` |
| `Polished` | `before`, `after`, `run` (the five inputs and the outcome of the pass's test run) | `polish --done` |
| `Checked` | `tip`, `tree`, `base`, `inputs` (one digest of commands, serial, setup, plan file), `outcomes` (command, last line, output path, passed), `criteria` (each: red on base, green on tip, or taken from polish at commit), `bar` (lowered files and reasons), `size`, `own_checks`, `removed` (untracked, bytecode), `items_after` (backlog item paths that `file` committed after it) | `checks`, `file` |
| `Reviewed` | `attempt`, `tip`, `of` (`change`, `resolution`), `floor`, `kind`, `careful`, `answered`, `silent`, `findings` (id, level, where, title, cheap), `to_file`, `scope` (`resolution` or `whole`) | `read --record` |
| `Filed` | `finding`, `disposition` (`item`, `same`, `cheap-fixed`, `seen`), `path`, `worth`, `cites` (an older `worth: no` item a new `worth: later` item names), `jev`, `commit` | `file`, `propose` |
| `Proposed` | `tip`, `base`, `green`, `reasons`, `careful`, `notes_path`, `merge_review` (`carried` or None and why), `owner_merge` (`stands: why`, `ended: why`, or None), `who_acts` | `propose` |
| `MergeRead` | `tip`, `base`, `base_tree`, `verdict` (`merge`, `call`, or None), `base_call` (`safe`, `another round`, or None), `why`, `carried_from`, `attempts`, `no_answer` | `merge-review`, `propose` (carried) |
| `Standing` | `tip`, `reasons_digest`, `by_act` | the owner's merge refused for the base |
| `Refused` | `tip`, `source` (`github`, `lem`), `kind` (`rule`, `tip`, `base`, `target`), `line`, `by` | `merge` |
| `MergeIntent` | `tip`, `by`, `via`, `at` | `merge`, under the merge lock, before the forge call |
| `MergeAccepted` | `tip`, `at`, `queued` (the forge's own word: a queue or an automatic merge that waits) | `merge`, when the forge took the call and the pull request is not merged yet |
| `Merged` | `by`, `via`, `commit`, `merged_head` (the forge's head at the merge), `parent`, `destination` (the forge's base, read from the forge), `base_checked`, `base_merged`, `base_read` or `uncovered`, `left_behind`, `text_updated` | `merge`, `merged` |
| `Cleaned` | `worktree_gone`, `branch_gone`, `forge_branch_gone`, `branch_left`, `rebased` | `clean` |

Lem-written artifacts that the record cites by digest are at distinct paths (`reviews/review-N`,
`merge-brief-TIP-BASE`, `checks/ROUND-N-COMMAND.log`, `pr-ROUND.md`); a cut-off update never
changes a cited file. Agent-written prose (`handoff.md`, `report.md`, `notes.md`) is read as it is
and never cited by digest. **[pair-settled]**

## B. The phases

| Phase | Entered by | Left by |
| --- | --- | --- |
| `preparing` | `start` (from `ready`, or from `open` on a new round) | `propose`: `open`; a red base: task `ready`, hold `blocked: the base is red, after: SLUG`; a fast task that needs the full track: `shaping`; a missed plan talk: `planned` with `needs a session: careful` or `large, N tasks`; his drop: `ended` |
| `open` | `propose` | `merged`; a new round; closed on the forge or his drop: `ended` |
| `merged` | the forge's merge into the task's base, seen by `merge` or `merged` | `clean`: task `landed` |
| `ended` | `clean`, or a drop's `clean` | none |

## C. The due step (`model/landing/phases.py: due(landing, task, world) -> Due`)

`world` is gathered fresh: the worktree's tip, tree and cleanness, origin's base, the remote task
branch, the forge's pull request (state, head, base, mergeable, merge commit and parent), the
settings of the main checkout, the load, the clock.

In `preparing`, the first row whose evidence does not hold is due:

| Order | Step | Holds while |
| --- | --- | --- |
| 1 | `start` | `started.round == round`, the worktree clean, `checks.commands` not empty or `own_checks` |
| 2 | `base` | origin's base is `based.base`; the remote branch holds no commit Lem did not push; no rebase in progress |
| 3 | `polish` (full track) | `polished.after` is in the tip |
| 4 | `checks` | check definitions as now, and `checked.tip == tip` or the commits after it only add `items_after` (`gate_holds`) |
| 5 | `review` | the newest answered review covers the change (D) and left no must-fix; or two rounds are used; or two attempts were silent |
| 6 | `file` | every finding has a disposition (D, filing) |
| 7 | `propose` | `proposed.tip == tip`, the forge's head is `tip`, `pushed == tip` |

In `open`: when `intent` is set, `reconcile` is due first (part E, the three intent rows): it
reads the forge and ends with `Merged`, `MergeAccepted`, a definite `Refused`, or the intent
cleared; it never sends a second merge call (`merge_locked`). When `accepted` is set, `merged`
is due while the forge says the pull request is queued; else `mergeread` when no usable read covers (tip, base now); else
`merge` when invariant 2's authority holds; else `wait`. In `merged`: `clean`. `next` names the
due step or the wait and its why.

## D. Carry and coverage (`model/landing/carry.py`, pure)

| Rule | Holds when | Source |
| --- | --- | --- |
| Review coverage | the reviewed tip is the tip; or the tip only adds `items_after`; or a clean rebase: `git merge-tree` of the reviewed tip onto the new base gives the new tree, with no commit after. Matching patch ids are not enough | `covers_one`, `review_carries`, `tip_carry` |
| Checks carry | only over commits that add `items_after`; an item written by hand asks for checks | `gate_holds` |
| The task's own item removed | the review covers it when the removing commit changes nothing else; the checks run on it | `land.md` 6 |
| Unshown rebase | no review carries; `read` asks with the reason; `propose` ends the standing merge | `land.md` 2 |
| Outstanding must-fix | stays through any carry, and the next review of the change is whole-change | `due_of`, `tip_carry` |
| Merge read carry, clean rebase | a real verdict (`merge` or `call`, not an unusable answer), no conflict, no commit after; `who_acts` recomputed from the new proposal | `moved_carry`, `may_merge` |
| Merge read carry, conflict | the read before had a real verdict, and the resolution's one read found nothing (no must-fix, should, nit), answered, nothing careful, no commit after, the review before left no must-fix | `conflict.md`; `land.md` 7 |
| Safe read on a moved base | covers its `base` only while origin's base tree is its `base_tree` | `merge_locked`, `read_base` |
| Revert of the base | origin's base tree is the checked base's tree: the checks cover again | `land.md` 7 |
| Standing merge | stands while coverage holds and the not-green reasons are the same; else `ended: why` and "Your merge ended" | `land.md` 8 |
| Checks taken from polish | the pass committed, its run had the same five inputs | `land.md` 4 |
| Check definitions | a change of `checks.commands` or `checks.serial` makes `checked` not hold before propose and before merge | `same_checks` |
| Filing | each finding: an item (`worth: later` over the bar, `worth: no` under it); `same` (an open item holds it, `--same rN.M=PATH`); `cheap-fixed` (a commit names it); `seen` (a line with `under:` or `cheap:` and its reason). An over-bar finding whose open item says `worth: no` gets a new `worth: later` item that cites the old one, which stays | `land.md` 5-6, `cmd_file` |

## E. The hard paths

| Path | Trigger | Due, and result | Owner sees |
| --- | --- | --- | --- |
| Start over | `task move SLUG ready --start-over WHY`, only where a refusal names it | reviews to `archived`, attempts from 1, `standing` and carried reads cleared, `owner_merge: ended: the landing started over: WHY` | WHY |
| Recovery | a cut-off, a red base, a stop | `start` keeps the record whole | nothing |
| Push recorded first | a cut-off after the push, before the PR write | `pushed` is kept before the forge call; the next `propose` adopts only an open PR whose head is `pushed`; another PR on the branch is somebody's: refused with `git branch -m` | the line (`cmd_propose`) |
| Red base | a red command also red on the base | a repair task, hold `blocked: the base is red, after: SLUG`; landed: `ready`, start again; gone session: open once, then tell; dropped repair: wait for his word | one line |
| Repair limit | two builders on one failure | hold `blocked` | the row, its push |
| Fast track turns careful | the review's careful call | full set, owner merges, not green | the reason |
| Fast track lowers the bar | `checks` finds it | status `shaping`, hold `owner: interview` | one line |
| No checks | `checks.commands` empty on the main checkout | hold `blocked: no checks`; the task that adds them lands not green | the row |
| Teammate commit | a remote commit Lem did not push | `base` and `propose` refuse with each commit and the `git pull --rebase`; then `start`; checks and a read | the refusal |
| Conflict with the base | rebase stops on files | undone, files named; a builder resolves; `base` keeps the polish pass | nothing |
| Rebase refused by git | a hook or a lock | nothing kept; git's words; HEAD state after the abort with the commands that restore it | git's words |
| Merge-only change | the rebase would drop it | refused with the tip and `git reset --hard` | the line |
| Conflicting PR on the forge | `mergeable: CONFLICTING` at a head, once per head | wake; `start --conflicting`, `base` (the polish pass kept), `checks`, one read of the resolution (no round; whole change when the earlier review left a must-fix or a commit after changed the resolution; full set if careful), `propose` | `synced` |
| Base moved, open PR | merge refused `kind: base` | `mergeread` with what moved since the checks' base; `safe`: merge on that base; `another round`: new round; no new brief of that tip | one line for a new round |
| Base moved after a safe read | the base tree is not the read's | refused, read again | nothing |
| Two unusable answers | no verdict twice, base unmoved | recorded as `call` with no verdict, why names the line (`unread_next`) | "Read the merge review" |
| | no base call twice, base moved | recorded as `another round` | one line |
| No answer | `--no-answer` | an unusable answer | as above |
| Stale tap | the board's merge with a tip not the proposed one | refused; zero forge merge calls | why |
| Owner merge refused for the base | his merge, base moved | `Refused(by owner, base)`, `standing`; safe: the server merges `--by owner --standing`; another round: `propose` prints `stands` or `ended` | nothing, or "Your merge ended" |
| GitHub refuses | a rule of the base branch | `Refused(github, verbatim)`; no automatic retry of that tip | the line |
| Transport fault | `gh` or `git` failed | nothing kept; the server retries in minutes | nothing |
| Stop after the intent, before the call | the process ends between `MergeIntent` and the forge call | `reconcile`: the forge says open and not queued, so the intent is cleared and `merge` is due again under the lock; the forge says merged, so `Merged` is recorded (the call was made after all) | nothing |
| Stop after the call | the process ends after the forge took the call | `reconcile`: merged gives `Merged`; queued gives `MergeAccepted`, and `merged` polls while the forge says queued; open and not queued with a refusal line on the forge gives a definite `Refused` | nothing, or the line |
| Forge took the call, not merged yet | a queue or a check | `MergeAccepted`; `merged` polls while queued; a queue that ends unmerged clears it, and the forge's reason is a `Refused(github)` | the line, if refused |
| Merge taken, text not updated | the PR text edit failed | `text_updated: false`, exit 1; `merged` retries the edit | nothing |
| Retarget before the read | PR base is not the task's | merge refused with `gh pr edit N --base B` | the line |
| Retarget after the locked read | the forge reports a `destination` that is not the task's base | not landed: the task stays `open` with `Refused(lem, target)`, nothing cleaned, the branch kept (`base_refusal`, merged case) | the line: drop it, or a new task brings the change |
| Merge on GitHub between look and call | the right destination, but the parent's tree is not the tree the checks or the safe read covered | landed, with `uncovered` in the PR text and the landed state (`moved_line`) | one line |
| The parent, by merge method | to find the parent of the merge | squash: the merge commit's first parent; keep history: the parent before the first replayed commit (`merged~commits`, `moved_line`) | nothing |
| Base checkout cannot follow | `merge --ff-only` refused | `left_behind`, git's words, nothing changed | the line (`follow`) |
| Closed on GitHub | closed, not merged | `dropped`, "the pull request was closed on the forge"; tracker drop; `clean` | one line |
| Clean, landed | after the merge | the local branch goes when the base holds its tip, its tip is `merged_head`, or its tip holds `merged_head`'s change rebased after Lem's last push (`after_push`: `merged_head` merged onto the tip's base gives the tip's tree); a divergent local branch stays with `branch_left`, `range-diff` and `branch -D`; a tip the forge did not merge, or merged inside its own head, keeps branch and forge copy, exit 1 (`cmd_clean`) | the line |
| Clean, the forge's copy | after the merge | deleted by full ref name with a lease on `pushed` when it is `merged_head`, also when the rebase proof above fails; a failure is said, the next run tries again (`drop_forge_copy`) | the line |
| Clean, dropped or answered | after the end | the worktree goes; the local branch goes only when its tip is an ancestor of origin's base or of the local base; else it stays with `branch -D` (a dropped task's commits; an answered task's, with its reproducing test) | the line |
| Clean, dirty | changes or own files in the worktree | refused | the line |
| Drop during a step | his drop, from any status that is not ended (part 3's table; a release-stopped task too) | stops running checks, takes the step lock, rereads the record; merged meanwhile: refused, the task lands; else `dropped`, the PR stays open for him **[decided]** | the line |
| Ticket after the end | a stop before the tracker step | `ticket_owed`; `task ticket` accepted after the end | nothing |
| Relands | each admitted new round | `relands + 1`, a journal entry; shown in the merge brief; no bound | in the brief |

## F. The refusals kept, by step

Each exits 1 with `why` and `fix`; it is never sent again unchanged. The ledger's 195 `refusal`
rows are the complete list; these are their codes.

| Step | Code: refuses |
| --- | --- |
| every step | `protected` (base or task branch in `branch.protected`, at push, merge, delete) · `step-held` · `release` · `not-github` |
| `start` | `dirty` · `no-checks` · `status` |
| `base` | `teammate` · `rebase-in-progress` · `conflict` · `git-refused` · `merge-only` |
| `polish` | `fast-track` |
| `checks` | `no-polish` · `tracked-change` · `bytecode-folder` · `criteria` · `bar` (fast track) |
| `read --record` | `under-floor` · `no-careful-call` · `careful-not-full` · `attempt` · `tip` |
| `file` | `jev-same` (`--same`/`--new`) · `item-gone` (`--again`) |
| `propose` | `unfiled` · `no-bar-call` · `jev-over` (once per finding) · `breaker` · `plan-talk` · `criteria-silent` · `own-item` · `foreign-pull` (a PR on the branch at a head Lem did not push) · `closed` (the PR is merged or closed: `merged` comes first) |
| `merge-review` | `old-tip` · `another-round` · `no-verdict` |
| `merge` | `status` · `no-pull` · `merger-rule` · `tip` · `target` · `base` · `checks-changed` · `intent` (a merge intent is on record: `reconcile` first) · `accepted` (the forge holds the call: `merged` polls) |
| `clean` | `dirty` · `unmerged` |
| `task move dropped` | `merged` (the forge merged during the drop's wait) |

## G. Locks

| Lock | File | Held |
| --- | --- | --- |
| record | `tasks/SLUG/task.lock` | read, check `revision`, write; never across an effect |
| step | `tasks/SLUG/step.lock` (step, pid, since) | a whole landing step and a drop's write, effects included (`step_lock`, `held_refusal`) |
| merge | `.lem/state/locks/merge.lock` | one merge call, with the recheck of status, head, base, target, authority, check definitions |
| serial | `.lem/state/locks/serial.lock` | `checks.serial` and `lem serial` |
| load line | `~/.config/lem/load.line/` | the wait for the load: after-dependency first, then oldest; a minute apart; a look every 15 s |

## H. Invariants (`model/landing/invariants.py`), checked before the effect

1. A push or a merge names a tip that `checked` covers (D, checks carry), with check definitions
   as now.
2. A merge: the PR is open, in the configured repository, its base is the task's base, its head
   is the proposed tip, which Lem pushed; origin's base is the checked commit, or a commit whose
   tree is the checked base's tree (a revert, part D), or a commit whose tree a `safe` read
   covers; by merger: green, not careful, the newest review made the careful call,
   `branch.land = "agent"`, a `merge` verdict for that tip and base; by owner: his act for that
   tip, or a standing merge whose reasons are unchanged. The forge pins only the head
   (`gh pr merge --match-head-commit`): a retarget after the read is a race no client can
   close, so the destination the forge reports is checked after the merge (E, the retarget
   rows).
3. A push is `--force-with-lease=refs/heads/BRANCH:PUSHED` (absence on creation), inside the
   adapter; a forge ref is deleted by full name with the commit it was checked at.
4. Nothing is pushed to, merged into or deleted from a protected branch.
5. Green is the seven conditions, in one function (`model/landing/green.py`).
6. No status leaves an ended state; after the end only `clean`, ticket steps, session lines and
   retention write.

## I. Journal entries of the landing **[pair-settled]**

| Entry | Fields | Producer |
| --- | --- | --- |
| `CheckWait` | `reason` (`load` or `behind`), `load`, `start_below`, `behind` (slug), `position` | `checks_gate`, on each change of reason or position (not every look) |
| `CheckEnd` | `outcome`, `say`, `commands` (name, passed, last line) | `checks_run` (`gate_end_said`) |
| `MergeWait` | `behind` (slug) | `merge`, while the merge lock is held by another task |
| `ReviewRound`, `MergeRead`, `Refused`, `Merged`, `LandAgain` | as the evidence | the step |

Views render `CheckWait` and `MergeWait` as today's `WAITS` lines; retention folds them into
totals that the Activity view and the retro read, and a unit case checks both summaries after
prune.
