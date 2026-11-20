# The board ends the checks at their end

careful: no, because the change is how `skills/lem/assets/board.html` draws events that `land.py` already writes: no record, state, decision, criterion or step of the landing changes, so no topic of the owner's is reached; the nearest, "A task's record is lost or wrong", is about the records, which the page only reads, and the page starts no pattern other code copies.

## Acceptance criteria

Size: full, because three views of the board (the time card, the large card and the task's card) change for each way a run of the checks ends.

1. A run of the checks that was stopped ends on the board where it ended. Task `trim-cart-notes` is in its landing; its checks started at 10:00 with 2 commands, finished none, and were stopped at 10:04 (`lem land checks trim-cart-notes --stop`). At 10:10 its time card shows the checks' span from 10:00 to 10:04 headed "The checks were stopped", and no span of the checks after 10:04; from 10:04 the time is Lem's, which waits for the owner's word. The task's large card and its card on the board say the same, and none of them says "The checks run".
2. A run that the checks refused before their first command ends the same way. The same task's checks start at 10:00 with 2 commands and end refused at 10:01 with no command done: its time card shows the checks' span to 10:01 headed "The checks refused the change", and no span of the checks that runs after 10:01.
3. A run that is still going is drawn as running, as today. A task whose checks started at 10:00 with 2 commands and have no end yet shows at 10:04 "The checks run: 0 of 2 commands done", as a span that runs to now.

## What is there today

Read in the code at `ffd8903`:

- `land.py` `checks_run` logs `gate.start tip=TIP commands:=N` before the first command, one `gate`
  for each command that ended, and one `gate.end` however the run ends, with `result` (`passed`,
  `red`, `refused`, `stopped`), `seconds`, `tip` and `say`. `checks_say` gives the `say`:
  stopped is "SLUG: the checks were stopped; the landing waits for your word", refused is "SLUG:
  the checks refused the change: ...; a builder repairs it, nothing for you". `stages/land.md`,
  step 4: after `stopped` Lem does nothing, "the landing then waits for his next word"; after
  `red` or `refused` a repair builder starts. A stopped landing is not on `lem project waiting`.
- `board.html`: `CHECKS = ['polish', 'gate', 'task.red', 'review', 'review.filed', 'proposed']`
  and `LANDING_STARTS = ['polish.start', 'gate.start', 'review.start', 'builder.start']`.
  `landing(k, from, to, open)` in `timeOf` reads only those events, so a `gate.end` is never
  seen: after `gate.start` and no `gate` its open piece is `['checks', 'The checks run: 0 of
  ${gates} commands done']`, drawn live to now; after a `gate` it is the "N of M commands done"
  piece or the tests of the criteria.
- In the model (`for (const e of events)`), `t.landingStep` is set at a `LANDING_STARTS` event and
  cleared by any later event that is not a state block or a decision, `gate.end` among them. The
  large card's head for `landing` is `stepRuns(t.landingStep)` or, with none, "The checks and the
  review run on it", so after a stop it says the checks and the review run.
- The task's card on the board says `t.info.label` and `t.shown`, the newest state block's first
  line; `STATUS.landing` is `{actor: 'gate', who: 'The checks', label: 'Checks and review', live:
  true}`. The lane of a landing task is `checks`.
- `SAYS` has no entry for `gate.end`, so the activity shows it as its raw fields.
- `tests/test-board.sh` has the task `gate-runs` (a `gate.start` and nothing after it), checked in
  the block "a step whose start is logged and whose end is not runs to now" with `data-head="The
  checks · The checks run: 0 of 2 commands done"` and the large card's `now` row "The checks run".
  Its slugs are written by `board --no-open --task` in the loop after the backlog checks, and
  drawn with `draw task-SLUG` in headless Chrome.

## Tasks

1. **The board reads `gate.end` as the end of a run of the checks, and says how the run ended.**
   Serves criteria 1, 2 and 3. Files: `skills/lem/assets/board.html`, `tests/test-board.sh`.
   - In `landing()`, `gate.end` is one of the events that cut the landing: the piece from the
     event before it to the `gate.end` is the checks' own, on the row `checks`, headed by its
     result ("The checks were stopped", "The checks refused the change", "The checks are red",
     "The checks passed"), with the run's commands done of its total and its seconds as the sub
     where the events give them. A run's `gate` pieces before it stay as they are.
   - When the landing is open and its newest event is a `gate.end`, its open piece is Lem's
     (`lem` row): after `stopped`, "The checks were stopped: the landing waits for your word";
     after `refused` or `red`, Lem's wait for the repair (in the words `afterFailure` has, or
     close to them); after `passed`, Lem between two steps. None of these is on the `checks` row.
     A run with a `gate.start` and no `gate.end` is drawn as today.
   - The model keeps the newest `gate.end` of a run whose landing has not gone on since (no
     later step of the landing, no state block of another status). While it is `stopped`, the
     task is Lem's wait for the owner's word on its large card and its card: an `info` with
     `actor: 'lem'`, `who: 'Lem'`, a label such as "Checks stopped" and `live: false`, and a
     shown line "the checks were stopped: the landing waits for your word"; the large card's head
     says the same, never "The checks and the review run on it". After `refused` or `red` the
     large card's head names the result and that a builder repairs it. The task stays in the
     lane `checks` and is not in "Waits for you": `lem project waiting` does not list it.
   - `SAYS` gets `gate.end`: its head by result, the `say` or the seconds and the tip as its text.
   - `tests/test-board.sh`: a task whose landing logs `gate.start commands:=2`, no `gate`, and
     `gate.end result=stopped`; and one with `gate.end result=refused` after `gate.start` and no
     `gate`. Each drawn: no `data-head="The checks · The checks run` in its page, a checks span
     headed by the result, the open piece on Lem's row, and the large card's `now` row without
     "The checks run" and, for the stopped one, with the owner's word. The board of all tasks
     gives the stopped task's card the stopped line. `gate-runs` keeps its check as it is, which
     holds criterion 3.

## Decisions

- A stopped run is Lem's wait, not a row of "Waits for you": the owner's one list
  (`lem project waiting`) does not name a stopped landing, and the board's "Waits for you" is that
  list. The words on the card say that the landing waits for his word.
- `passed` and `red` ends are read as well as the two the item names, so that every `gate.end`
  ends its run the same way; a passed run's open piece stays Lem's between two steps, as today
  after the tests of the criteria.
- The comment "the board draws them from here to their last result" in `land.py` `checks_run`
  becomes false; `land.py` is out of the task's scope (`task.md`), so it is left to the polish
  pass.
- No documentation task: no guide or stage text says how the board draws the checks; `SKILL.md`
  already says that the checks end at `gate.end`.

## What it will not verify

- The look of the new spans in a real agterm overlay: the checks run in headless Chrome only.
