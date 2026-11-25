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
- His Yes on the board is an approval `by="owner"` of `criteria.md` with the digest his page
  showed: `lem.app.criteria.approve.approved(folder, slug, Asked(by="owner", path=SHEET,
  shown=DIGEST))`. An approval by the owner or without him ends the hold on the interview or the
  criteria (`waits.hold_after`); it does not write an answer on the question.
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

## For `land-propose` (green and the pull request's text)

What the record holds for the reasons that are not the plain path's:

- `Criteria.reads`: each `PersonaRead` (`by`, `started`, `ended`, `asked`, `answered`,
  `families`, `silent`, `criteria`, `flagged`, `split`, `digest`); a read is done when `ended`.
  `Criteria.skip`: `asked`, `yes` or `no`; his yes is also a `Taken` decision `by="owner"` with
  the texts of `stages/interview.md`, step 5.
- `Criteria.change`: the newest change from his note (`at`, `text` he answered, `words`, `pairs`,
  `before` and `after` marks), so the request can say that the criteria changed after the read.
- Decisions: `Taken` (`by`, `unsettled`, `story`, `advisers`, `breaker`), `CriterionChanged` and
  `Breaker`; `lem.model.decisions.changes.changes_of(task)` gives each change with the owner's
  approval that took it over (`taken_over_by`).
