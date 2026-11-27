# A feature in parts: a feature branch, a small pull request for each part, one pull request at the end

> **Status: planned, not built.** Step 36 of the roadmap's "After the cutover"
> (`2026-11-25-lem-built-again/roadmap.md`). Written on 2026-11-27 by an Opus worker of the
> maintaining session, from `main` at `fa1c6e00` (Lem 0.4.2), and made smaller after a fresh
> reviewer's read. Every cite of code is at that commit. The choices marked [decided] are the
> maintaining session's, open to the owner.

Marks: **[owner]** the owner's direction; **[settled]** decided before this plan, with its source;
**[decided]** a choice of this plan; **[checked]** a fact with its source; **[untested]** a claim
that rests on reasoning alone. Sizes and counts without a source are unmeasured estimates.

## 1. What is settled

- **The shape of a feature** [owner, entry 22 of `choices-for-the-owner.md`, 2026-11-25]. His
  words: "Maybe they develop larger feature in a separate branch and do PR there (and keep the
  branch in sync with master)? So one can do their work and mark checks in a plan (issue at
  Github, Linear) with every accomplished step without feature flags and other mashinery. This
  approach will let us throw away whole thing easily if we decide we don't like it."
  - A branch `feature/NAME`, cut from the project's base.
  - Each part is an ordinary task whose base is `feature/NAME`, with its own checks, review and
    small pull request into it.
  - Nothing reaches the base until the end. No release flags.
  - At the end, the feature's own pull request goes from `feature/NAME` to the base, squashed.
  - Throw away: before the end, drop it and delete one branch; after the end, revert one commit.
- **Reserved on `main`** [settled, amendment A6]. `Task.after` is `tuple[Slug, ...]`
  (`src/lem/records/task.py`). `TicketAct` takes `ticked`; this plan writes no `ticked` step.
- **The sync** [settled, the maintaining session, on Astra's way]. The feature branch takes in the
  base by a merge commit after each merge to the base, also while parts are open. An open part then
  meets a moved base, and the moved-base rule of the merge line handles it (section 4).
- **Who merges** [settled]. A part's merge follows `authority` in `src/lem/model/landing/merge.py`
  unchanged. The feature's own pull request always takes the owner's Approve.
- **The ticks go into Lem's own comment on the ticket** [decided]. Lem never edits a description
  that a person wrote, and its lines are the parts (section 6).

## 2. The owner's path

A small task that is not a feature gets **zero** new touches, waits and agents (section 8).

| He wants to | He does | What he sees |
| --- | --- | --- |
| Start a feature | `/lem new as a feature: <ask>` (or "in parts") | The interview as today. The criteria page groups the criteria under one heading for each part, and one group for the whole feature. His one yes approves the criteria and the split. That page alone has one more fixed answer, "One pull request" |
| Let it run | nothing | Lem makes `feature/NAME` and opens one task for each part. Each part goes the way of any task; a careful or not-green part calls him, as today |
| Add a part | `/lem new part of NAME: <words>`, in any session or on the board's "+" | A new task, with its own interview or the fast track, and his yes to its criteria as for any task |
| Watch it | the board, or `/lem status` | The card of NAME: the parts merged of all parts, its age, and how many commits the base is ahead. Each part's card says "part of NAME" |
| End it | nothing: after the last part ends, the feature's session starts its end | One Approve on the pull request NAME into the base |
| Throw it away before the end | `/lem drop NAME`, then the one line it gives: `git push origin --delete feature/NAME` | Every part that has not ended is dropped with it |
| Throw it away after the end | `/lem new revert NAME` | A fast-track task that reverts the one squash commit |

Lem never proposes parts by itself [decided]. A task the owner did not ask as a feature stays one
task. The plan's rule for a large outcome stays as it is: "An outcome that needs more than seven
tasks is two asks" (`stages/plan.md`, step 1). Its report says so, and the owner may then ask the
rest as a feature.

His touches for a feature: one yes to the criteria, one Approve at the end, and a merge for each
careful or not-green part, as for any such task.

## 3. The design

### The records: two optional keys

| Record | New key | Why |
| --- | --- | --- |
| `Task` | `part_of: Slug \| None = None` | The part names its feature. Its base is the feature's `Task.branch` |
| `Criterion` | `part: str \| None = None` | The heading of the part a criterion belongs to; none is the whole-feature group |

The feature carries no key of its own. It is a feature when a record names it in `part_of`.
No new status, hold, approval form or ticket form.

### The order of the parts, and the feature's wait

`lem task split NAME` writes `Task.after` between the parts [decided]. Each part waits for the part
before it, in the order of the headings. A heading marked `(independent)` waits for nothing and
starts at once. The feature waits for all of its parts: its `after` holds every part's slug, and
`lem task open --part-of NAME` adds one under the workspace lock. So the queue rule
(`model/task/behind.py`) and the queue duty (`board/duties/queue.py turn`) hold the feature
`queued` until each part landed or was answered. A dropped part leaves the feature waiting for his
"start NAME now", as behind any dropped task.

### The base of a task

Once a round started, `app/landing/world.py origin` replaces `rules.base` with the recorded
`Started.base_ref`. Before the first `start`, six places take the settings' base:
`app/tasks/worktree.py made`, `app/tasks/resume_claim.py prepared`,
`app/landing/checks_criteria.py inputs` and `checked`, `app/tasks/drop_pull.py merged`, and
`world.origin` itself. Two board views do too: `board/views/branch.py head_of` and `filed_of` read
`place.base`. One function in `app/tasks/where.py` serves all of them: the recorded base, else the
feature's branch for a part, else the settings' base. A part whose feature record does not read,
has ended, or has no branch on origin is refused before any worktree or push.

### The criteria of a part

The split copies the feature's criteria of each heading onto its part, word for word, with the
part's own digest. It copies the feature's persona read and the owner's approval onto the part
with that digest too. The approval's `how` names the feature's approval it comes from.
`model/landing/propose_criteria.py unread` then finds a read on record, and
`app/landing/pr_unread.py unread` finds the read's digest equal to the part's criteria
(`text_mark`). So a part needs no second read and no second yes, and its pull request is not made
not green for that. A resume keeps its criteria the same way, in one record
(`model/task/resumes.py breaker_task`). `Criterion.part` is left out of the JSON when it is none
(`omit_defaults`, `records/base.py`), so the digest of every task with no parts stays the same.

### The sync

The board server's new duty `board/duties/sync.py` looks at each feature that is `queued` with no
hold. When origin's base is not an ancestor of origin's `feature/NAME`, it wakes the feature's
session with `lem: NAME sync`, and with none alive it opens one. It wakes once for each base
commit: the wake keeps that commit in the existing `Wake.head` (`app/sessions/acts.py`), and the
duty passes over a base commit that a `sync` wake already names. The session runs
`lem task sync NAME`:

1. Bring the feature's worktree to origin's `feature/NAME` by a fast-forward.
2. Merge origin's base into it with a merge commit, never a rebase: a rebase drops the merge
   commits of the parts and of earlier syncs.
3. A conflict refuses `conflict` with the files. A builder resolves it, with the brief of the
   repair of a conflict with the base (`stages/land.md` step 2).
4. The settings' checks run on the merge, through the runner of the landing's checks. A red run
   takes the repair builder of step 4 of the land stage.
5. Under the workspace's merge lock (`app/landing/merge_lock.py`), push with a lease on the tip of
   step 1. A part merged meanwhile makes the lease fail: go back to step 1. The lock keeps a sync
   push out of the gap between a part's locked read and its merge call.
6. The session writes its handoff and closes with `--why handoff`, as a queued task's session
   does (`stages/new.md`, step 7). The feature stays `queued`.

A sync that a builder cannot finish holds the feature `blocked` with its why and fix, which "Waits
for you" shows. Nothing watches a sync session that stops with no word while the feature is
`queued`: the guard acts only on `building`, `ready` and `landing` (`app/sessions/guard_acts.py`).
The next base commit wakes that session again, and the board shows the base's lead grow. This
plan adds no guard for it [decided].

**The queue duty counts only `queue` wakes.** Today `board/duties/queue.py tick` calls
`wakes.since(duty, slug, task.since)` with no wake words, so any open or wake after the task
became queued counts as its turn. A `sync` wake of a queued feature would then keep its end from
ever starting. The call becomes `wakes.since(duty, slug, task.since, ("queue",))`.

### The end

When the last part ended, the queue duty gives the feature its turn (`lem: NAME queue`). The split
set the feature's shape `then` to `lead`, so `model/task/queue.py started_in` takes it to
`building`, not to a second interview. Its session is the lead of the end:

1. A builder writes the tests of the whole-feature criteria and builds what they show is missing.
   A criterion the build has to change takes the rule every build has: `lem decisions criterion`,
   and the pull request is not green for it (`stages/interview.md`, step 7). No option that keeps
   an approved criterion's rule is the circuit breaker (`stages/breaker.md`).
2. The landing, with five differences from a task's:
   - `start` refuses while a part of the feature has not ended (`parts-open`).
   - `base` merges origin's base into the branch (the move of the sync), never a rebase.
   - No polish pass: each part had its own.
   - The review reads in full each commit of `feature/NAME` that is not a part's merge, and the
     whole diff of each careful part. A part's merge is the commits its `Merged` record names
     (`parent` to `commit`). A sync's resolution is `git show --remerge-diff` of its merge commit.
     The brief lists each part with its pull request and its review's verdict.
   - The merge: the owner only (a new reason in `authority`), always a squash whatever
     `branch.history` says, and refused while any open pull request has `feature/NAME` as its
     base. The board's Approve gives the squash its subject for a feature too:
     `board/acts/merging.py asked_for` gives it only when `branch.history` is `squash` today.
3. The checks are today's: every criterion of the feature fails on the base and passes on the tip
   (`app/landing/checks_criteria.py`).
4. After the merge, `clean` removes `feature/NAME` here and on origin, as for any branch.

A feature with a careful part is careful: it takes the full review.

After a part's merge, `app/landing/merged.py followed` fast-forwards the feature's worktree, the
checkout whose HEAD is `feature/NAME`. That stays: `git merge --ff-only` refuses with no change
when the worktree is in a merge or its branch is ahead (`adapters/git_cli_acts.py fast_forward`),
and the sync's step 1 brings it up to date.

### The drop

`/lem drop NAME` drops each part that has not ended, each under its own step lock, then the
feature. As for any drop, open pull requests stay open and branches keep their commits. The `say`
names each open part's pull request and the command that deletes the feature branch on origin.
Lem does not run it: "A destructive or outward step is never yours" (`skills/lem/SKILL.md`). The
ticket's "drop" runs as for any dropped task.

## 4. The moved-base rule reaches a part

Checked on `main`, for a part whose `Started.base_ref` is `feature/NAME`:

- `world.origin` reads `world.base` as origin's head of the recorded base. A sync or a sibling's
  merge moves it.
- `model/landing/merge_evidence.py base_side`: an approved merge goes to
  `model/landing/merge_recheck.py refusal`, which refuses while `checked.base != world.base`, so
  the checks run on the part rebased onto the moved feature branch. The merge agent's own merge
  takes a safe read or another round (`stages/land.md` step 8), unchanged.
- `app/owner/merge_bases.py for_task` reads each task's recorded base, and
  `board/duties/merge_order.py` sorts by it.
- `forge_side`, `reconcile.landed`, `propose_push` and `pull_identity` read the recorded base
  after `start`. The forge duty polls each pull request by its number (`board/duties/forge.py`).

So the rule reaches a part with no change. The one gap is before the first `start`: without the
base function of section 3, a part would be cut from the project's base, and its pull request
would go there.

## 5. The GitHub facts

| Fact | State | Source |
| --- | --- | --- |
| "If the branch is associated with at least one open pull request, deleting the branch closes the pull requests." | checked; whether "associated" takes in a pull request whose base is the branch: untested | [Creating and deleting branches](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-and-deleting-branches-within-your-repository) |
| After a merged pull request's head branch is deleted, GitHub changes the base of each open pull request on that branch "to the merged pull request's base branch" | checked | same page |
| Automatic deletion removes head branches "after pull requests are merged" | checked | [Automatic deletion](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-the-automatic-deletion-of-branches) |
| `on: pull_request: branches:` filters "pull requests that target specific branches"; a filter of the base alone skips the parts | checked | [Events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows) |
| Closing keywords are "interpreted only when the pull request targets the repository's default branch" | checked; no effect on Lem, which writes no closing keyword (a grep of `src/` and `skills/` for "Closes #", 2026-11-27) and closes the issue itself (`app/tasks/issues/land.py`) | [Linking a pull request to an issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue) |
| `git show --remerge-diff` shows a merge against git's own merge of its parents; its output "is subject to change" | checked | [git-show](https://git-scm.com/docs/git-show) |
| Each fact on a real repository | untested; step 36h tries them on lem-scratch | |

The retarget fact is why the feature's merge refuses while a pull request targets
`feature/NAME`.

## 6. A part's ticket step

Only the feature holds a ticket; `--ticket` with `--part-of` is refused. The plan in the ticket is
one comment of Lem's own:

```text
- [x] save-endpoint: the server saves an item and returns it
- [ ] ios-save-button: the iOS app saves the item it shows
- [ ] android-saved-list: the Android app lists the saved items

lem: save-items parts
```

`lem issue tick SLUG` (a GitHub issue), or the "tick" of the `lem-linear` skill, writes it: at the
split, after each part lands (`stages/land.md` step 9, beside the "land" of a ticket), and at the
feature's "land". The comment's text is a function of the records: every part of the feature, a
box set for each part that landed. The step finds the comment by its last line, as
`app/tasks/issues/comment.py` finds its end comment. With none it posts it; with one it edits it
only when the text differs. It writes no ticket step.

So a retry ticks nothing twice: it never sets "the next box", and the same records give the same
text. A tick that a stop lost, or that a second edit in the same minute overwrote, comes back at
the next part's land or at the feature's land, which writes the text again from the records.

## 7. The two-release rule

0.4.2 reads what this step writes (AGENTS.md, "A change of the form of a record"):

- `Task.part_of` and `Criterion.part` are new optional keys. 0.4.2's structs read past unknown
  keys (`records/base.py`).
- The word `sync` goes into `WakeWhy` of `app/sessions/acts.py`. Those acts are lines of
  `session-acts.jsonl`, and 0.4.2's reader `app/sessions/log.py read` skips a line it cannot
  decode. `records/journal/sessions.py` is not where Lem writes session acts: nothing builds a
  `SessionWoken`.
- The test of 36a reads a task record of 0.4.2's form and finds each old key in the record the new
  code writes. The test of 36c decodes a `sync` line against 0.4.2's form of `Wake` (its `WakeWhy`,
  copied into the test) and finds it skipped as `log.read` skips it.

No release of its own is needed.

## 8. The steps

`T LEVEL PATHS` is `.venv/bin/python -I -B tests --level LEVEL PATHS`, with `LEM_SERVE=off`. Each
step is a task of Lem's own, landed by the same steps as any project's task.

| # | Step | Builds | Proves it | Needs |
| --- | --- | --- | --- | --- |
| 36a | `feature-base` | `Task.part_of`; the base function in `app/tasks/where.py` and its six callers; `lem task open --part-of NAME` (refused when NAME is not a `queued` task with a branch on origin, is itself a part, or with `--ticket`), which adds the slug to NAME's `after` under the workspace lock | unit: the base function's cases, the refusals, an old record read. Journey `tests/journeys/test_feature_parts.py`: with `LocalForge`, a part cut from `feature/x`, its pull request into it, its merge, its clean; a second part, approved by the owner, meets the first part's merge and runs its checks on the rebased tip before its merge | nothing |
| 36b | `feature-split` | `Criterion.part`; `lem task split NAME --file CRITERIA` (`cli/task/split.py`, `app/tasks/split.py`, `model/task/parts.py`): the headings checked, `feature/NAME` cut from origin's base and pushed, the feature's worktree, one part for each heading with its criteria, read and approval copied, `after` between the parts by heading order and `(independent)`, NAME `queued` after all with `then` set to `lead`. A run cut off makes only what is missing | unit: the heading checks, the order, the copy (a word that differs is refused), `unread` and `pr_unread` pass for a part. Journey: a split of three headings ends with three parts and NAME queued | 36a |
| 36c | `feature-sync` | `Git.merge` and `Git.remerge` (`ports/git.py`, `adapters/git_cli.py`, `tests/fakes/`); `lem task sync NAME`; `board/duties/sync.py` in `runner.DUTIES`; `sync` in `WakeWhy` and on `lem session wake` and `open`; the queue duty's `("queue",)` | contract `tests/contract/test_git.py`: a clean merge, a conflict, a refused merge, a remerge diff. Unit: when the sync duty wakes and when not; the queue duty gives a feature its turn after a `sync` wake; a `sync` line skipped by 0.4.2's form. Journey: a base merge, the wake, the sync's push, an approved open part refused `base` and checked again; a conflicting sync pushes nothing | 36a |
| 36d | `feature-end` | The five differences of "The end" in `model/landing/{start,base,polish,merge,merge_call}.py`, `app/landing/{world,base,review_brief,pr_text,merge}.py`, `board/acts/merging.py asked_for`; `prompts/feature-review.md` | unit: each rule; `authority` and the merge method of a task with no parts unchanged. Journey: a feature of two parts from its turn to `landed` and `clean`, with one sync between; the merge refused while a teammate's pull request targets `feature/x` | 36b, 36c |
| 36e | `feature-drop-tick` | The drop of a feature (`app/tasks/drop.py`); `lem issue tick SLUG` (`cli/issue/tick.py`, `app/tasks/issues/tick.py`, an edit of a comment in `app/tasks/issues/facts.py` and `adapters/tracker_github.py`); the "tick" of `skills/lem-linear/SKILL.md` | unit: the comment's text from records. Contract: the `gh` stand-in edits a comment. Journey: a tick cut off after its edit, run again, edits nothing; the drop of a feature drops its two open parts and names the delete | 36b |
| 36f | `feature-board` | The feature's card and the part's line in `board/inputs/`, `board/views/`, `board/templates/`; `board/views/branch.py` reads a part's own base; the words of `board/acts/merging.py said_of` name the task's base; `tests/fixtures/board/` gets one feature of three parts | unit `tests/unit/board/views/`, `tests/unit/board/pages/`; `T browser`: the card at 375, 390 and 430 px, a tablet and a computer, light and dark | 36b |
| 36g | `feature-text` | `skills/lem/stages/feature.md` (the split, a part's open, the sync wake, the end, the drop); one conditional line that names it in `stages/interview.md` step 4, `stages/new.md`, `stages/land.md` and `prompts/session.md` "A wake-up"; `docs/features.md` in STE and its line in `zensical.toml`; the owner's direction as one bullet of `docs/rulings/rulings.md` under "The review, the pull request and the merge" | `T unit tests/unit/guides/`; `T unit tests/unit/cli/`; a unit case that `stages/feature.md` and `prompts/feature-review.md` are named by those lines alone | 36a to 36f |
| 36h | `feature-trial` | `docs/plans/2026-11-27-a-feature-in-parts/trial.md`. On lem-scratch with GitHub: F1 a feature of two parts to its squash on `main`; F2 a merge to `main` while a part is open, the sync, the part's recheck; F3 the drop and the delete, and whether GitHub closes a part's pull request whose base was the branch; F4 a tick on an issue, and a tick cut off; F5 a workflow with `pull_request: branches: [main]` on a part | F1 to F5 passed in the file; a defect becomes a step | 36g |

36b and 36c may run at the same time after 36a; 36e and 36f after 36b. `--level full` runs once
before `main` moves for 36d and for 36g.

## 9. The cost on a small task

What a task with no `part_of` and no parts meets:

- **Touches, waits, agents:** none new.
- **Code:** the base function returns the settings' base after one `None` check. The queue rule
  is unchanged. `authority` and `merging` get a fact that is empty for it. The sync duty makes no
  git call when no record names a feature. The queue duty's wake words change nothing for a task
  that gets only `queue` wakes while queued.
- **Text:** every task reads `prompts/session.md`, `stages/new.md` and `stages/land.md`, and a
  standard-track task reads `stages/interview.md` and `prompts/review.md`. Each of the first four
  gets one conditional line that names `stages/feature.md`; `prompts/review.md` gets none, since
  the feature's review is `prompts/feature-review.md`; `stages/start.md` gets none, since
  `lem task worktree` finds the base. No task without parts reads `stages/feature.md`.

The proof: the existing levels pass with no case changed; `tests/journeys/test_skeleton.py` and
`test_fast_session.py` keep their counts of commands, agents and forge calls; the case of 36g
holds the four lines.

## 10. Not in this step

- Parts that Lem proposes on its own, and a split found after a build started.
- A part from a ticket of its own, and sub-issues on GitHub or Linear.
- A part of a part, and a part of two features.
- Stacked pull requests and release flags.
- A `lem doctor` row for a workflow that filters `pull_request` to the base: the guide says it.
- Lem's own delete of `feature/NAME`.
- A guard of a sync session that stops while the feature is `queued`.
- A watch of the deploy that the feature's merge starts.
- A feature of a night, or across repositories.

## 11. Risks

| Risk | Input that makes it | What it costs | What holds it |
| --- | --- | --- | --- |
| Many syncs | A base with ten merges a day (unmeasured estimate for mybaze) while a feature is open | Ten short sessions of the feature, ten runs of its checks, and a recheck of each approved open part after each | One wake for each base commit; a sync takes the newest base |
| A feature that lives for weeks | A feature open for three weeks beside a busy base | Sync conflicts grow, and the merge risk of a long branch comes back | The board shows its age and the base's lead |
| A stalled sync session | The session stops with no word during a sync | The feature falls behind until the next base commit wakes it | The board's base lead; nothing more in this step |
| A part's request moves to the base | The feature merged on GitHub while a part's request is open, then its branch deleted | GitHub moves the part's request onto the base | The end refuses while a part is open or a request targets the branch; `forge_side` refuses a part on another base |
| The branch deleted by hand | `git push origin --delete feature/NAME` before `/lem drop` | GitHub closes the parts' requests; the forge duty drops those parts; the feature refuses `no-base` | His `/lem drop NAME` ends it |
| A part's follow line | A part merges while the feature's worktree is in a sync merge | `followed` writes a `left_behind` line that the land stage tells the owner | The line is true and changes nothing; the sync brings the worktree up |
| No CI on parts | A workflow with `pull_request: branches: [main]` | GitHub runs nothing on a part's request | Lem's own checks run on each part; the guide says it |
| A lost box | Two parts land in the same minute | One box stays empty for a while | The next land writes the text from the records |
| A checklist in Linear | Linear's comment markdown | A box may not draw | untested; 36h or the first Linear feature shows it |
| A dropped part | He drops a part he no longer wants | The feature waits for his "start NAME now": one touch | The rule behind a dropped task |

## 12. What the direction's notes say that `main` does not hold

The notes in `.claude/style-tools/reshape/feature-parts/` were written on `rebuild` (Astra's on
`rebuild@4a9c446d`). Read against `main` at `fa1c6e00`:

- "The rebuild holds the base behind one seam (`rules()`)": only after a round started. Before
  it, six places and two board views read the settings' base (section 3).
- "So the new step changes code, not record forms": it needs two optional keys and a new word of a
  session act; each is a form 0.4.2 reads (section 7).
- Astra: `start.decide` writes `base_ref=world.rules.base`, and `reconcile.landed` checks
  `target(pull.base, world.rules, ...)`. On `main` both use the recorded base first.
- Astra: `cli/criteria/red.py run` raises `not_built`, and `board/duties/forge.py tick` says
  "nothing yet". On `main` both are built.
- Astra: `pulls_of` is in `app/landing/world.py`. On `main` the search is
  `app/landing/pull_identity.py in_world`.
