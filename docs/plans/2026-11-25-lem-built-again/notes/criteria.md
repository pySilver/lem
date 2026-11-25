# Notes of the step `criteria`

What `criteria` needs in files it does not own, what it left as a stand-in, and what the steps
after it may count on.

## For `owner` (the answer rules) and `board-acts`: the criteria's question

- The criteria wait for his yes while `Task.hold` is an `OwnerHold` with `on` in `interview`,
  `criteria` (`lem.model.criteria.waits.hold_of`). The wait's question is the newest question
  of `topic="criterion"`, "Approve the criteria?", options `yes` and `no`, asked at or after the
  hold's `since` (`waits.question_of`); `digest` is the mark of `criteria.md`'s bytes the page
  shows (`lem.model.criteria.digest.shown`, 16 hex), or None for the first wait, whose page shows
  the file as it is.
- A change (`lem criteria change --file`) and a new wait of the same text (`--unchanged`) ask a
  new question with `waits.asked`; his typed No answers the open one, made with
  `waits.question(task, now, None)` when none was asked yet (`waits.answered`). The board's Yes
  and No should find or make the question the same way, so the first answer counts across the
  two places, and write it with `waits.answered`. The id is `criterion-N-YYYYMMDDTHHMMSSZ`.
- His Yes on the board is an approval `by="owner"` of `criteria.md`, with the question his page
  answered and the digest it showed: `lem.app.criteria.approve.approved(folder, slug,
  Asked(by="owner", path=SHEET, shown=DIGEST, question=QUESTION_ID, via="board"))`. The
  approval refuses `other-question` when the question is not the wait's open, unanswered one,
  `shown-changed` when the file is not the bytes shown, and writes his Yes on the question in the
  same write as the approval (`lem.model.criteria.yes`). It ends the hold on the interview or the
  criteria (`waits.hold_after`). His No on the board is `waits.answered` with an `Answer` of
  `option="no"`, written under the task's criteria lock (`Here.held()` in
  `lem.app.criteria.where`), which every change and approval of the criteria holds.
- **No command asks the breaker's row again.** `stages/breaker.md`, "He leaves the talk with no
  decision", wrote `lem project state SLUG held "breaker N waits for the owner" "LINE"` so that the
  row came back under a new key after his Help with a note. The new tree has no command for it,
  so that line, and only it, keeps the old-form mark of `stages/breaker.md`. Asked: a command that
  asks a hold's question again (for a breaker: a new question of `topic="breaker"` with the
  stage's line), and then the line in the stage.

## For `task`

- `lem task read --wait criteria|interview` should set the `OwnerHold` the criteria read (above).
- The plan of a task: `app/criteria/where.py` (`plan_of`) is a stand-in that reads
  `docs/plans/YYYY-MM-DD-SLUG.md` in the task's worktree, the newest day's, or the plan of the
  nearest task it was resumed from (`Task.resumed_from`, read through each record). Give
  `lem task plan-file` one finder, and this module calls it.
- `stages/plan.md` queues the lead's task behind another with `lem --repo WORKTREE task move
  SLUG queued --line "WHY" --line "after: OTHER-SLUG"`: the record's `after` needs to come from
  that line, or `task move` needs an `--after`.
- The texts call `lem task span SLUG scout|interview start|end`, `lem task span SLUG builder start
  --job "task N of M"`, `lem task span SLUG plan-talk start --by AGENT`, and `lem task talked`
  (which should end the `plan-talk` span). `stages/plan.md`, `prompts/lead.md` and
  `prompts/defender.md` read `talk` and `mode` in `lem task show SLUG`.
- The ledger rows moved to you are in `tests/ledger/moves/criteria.tsv`: resume, park, may-start,
  start, the release stop, and the five span events.

## For `settings`

- `app/decisions/experts.py` is a stand-in: `seats.experts` read raw from `.lem/settings.local.toml`
  over `.lem/settings.toml` with `tomllib`, else `claude/fable:high` and
  `codex/gpt-6.2-astra:high`, named `fable` and `astra` by place. Replace `named` with the
  settings' seats.
- `paths.plans` and `paths.plan_file` (the stand-in above takes their defaults).

## For `sessions`

- `lem decisions log --by experts` writes the experts whose `Harness.available(seat)` is None.
  The slice's Claude Code adapter answers `missing` for every agent but `claude`, so on a Mac with
  Codex the record says one expert where two answered. `available` must find `codex` too.

## For `land-checks`

- `lem criteria red` and `inputs` read the criteria as `lem criteria show` does:
  `lem.app.criteria.show.shown_of(here, record)` gives the file, `small`, and the criteria with
  their tests, checked against the approval and the recorded changes. `Criteria.digest` in the
  record is the 12-hex mark of the criteria with their cases and tests (no charts),
  `lem.model.criteria.digest.of_tests`, which `lem criteria record` writes.
- The rows of `Inputs` and `Unstarted` (`test_criteria.py`) are moved to you.

## For `land-checks`, `land-propose` and `land-merge`: the contract the evidence is of

The criteria are a task's contract. On `main`, `land.due` and `land.may_merge` read the criteria
as they stand at each step, so a pull request proposed for criteria A does not merge as green
after the owner approved criteria B. Here the contract is one mark,
`lem.model.criteria.contract.mark(task)` (the approved track and the expected criteria, after
each recorded change), and `contract.moved(task, seen)` gives the refusal `contract-moved` when
the mark is not the one the evidence was made under. What each step must do:

- `land-checks`: keep the mark of the run in `Checked` (a field `contract`), so a run of the
  checks on other criteria is not the evidence of this contract.
- `land-propose`: keep the mark in `Proposed`, and propose again when `moved` refuses: the
  pull request's text then names the new criteria.
- `land-merge`: refuse a merge intent, the merge agent's merge and `merged`'s green when `moved`
  refuses for the mark of the proposal (the owner's own merge on `main` was not held by it).
- `core`: the two fields (`Checked.contract`, `Proposed.contract`, `str | None`) are asked here;
  until they exist, a step compares the mark the review or the proposal recorded in a field of
  its own, or none.

## For `core`: two asks of the review of this step

The ports of a call of `lem decisions` are bound by `lem.app.landing.frame.bound`, the one
binding of the app; a place in `app/` for it that is no landing's would suit every step.


- `Git.clean(where)` counts untracked files. `main:decisions.cmd_breaker` refused only an
  uncommitted change of a tracked file. A fact `clean(where, untracked: bool)` (or
  `tracked_clean`) lets the breaker take main's rule again; until then the breaker refuses work
  that no commit holds, untracked files too, and `stages/breaker.md` says so.
- `markdown-it-py` is in the environment but not among the app's dependencies, so the criteria's
  reader keeps its own fences and headings (`model/criteria/{fences,section}.py`); with the
  dependency declared, those two modules can take its tokens and keep Lem's criteria rules.

## For `land-propose` (green and the pull request's text)

What the record holds for the reasons that are not the plain path's:

- `Criteria.reads`: each `PersonaRead` (`by`, `started`, `ended`, `asked`, `answered`,
  `families`, `silent`, `criteria`, `flagged`, `split`, `digest`). A read with a result has its
  `digest`; one that ended in silence has none, and counts as no read
  (`lem.model.criteria.clear`); two in a row that nobody answered are two of the same digest.
  `Criteria.skip`: `asked`, `yes` or `no`; his yes is also a `Taken` decision `by="owner"` with
  the texts of `stages/interview.md`, step 5.
- `Criteria.change`: the newest change from his note (`at`, `text` he answered, `words`, `pairs`,
  `before` and `after` marks), so the request can say that the criteria changed after the read.
- Decisions: `Taken` (`by`, `unsettled`, `story`, `advisers`, `breaker`), `CriterionChanged` and
  `Breaker`; `lem.model.decisions.changes.changes_of(task)` gives each change with the owner's
  approval that took it over (`taken_over_by`).
