# The landing's checks run in the background

careful: yes, because task 1 changes when the landing reads the result of the checks and adds a refusal to `read` and `propose`, which reaches the owner's topic "The landing lets through a change that should not land: one the checks or the review did not pass, one a person should merge, or one aimed at a protected branch", and a run that is stopped must leave `landing.json` true, which reaches "A task's record is lost or wrong".

## Acceptance criteria

Size: full, because the landing's longest step moves out of Lem's foreground, Lem must pick the landing up again when it ends, and the change is careful.

1. While a task's checks run, Lem's session answers the owner: in a landing whose checks take 4 min 26 s, as `lem-landing-page`'s did on 2026-11-19, a message he types one minute after the checks start gets its answer before they end. When that message is `/lem drop SLUG` or `/lem standard-track SLUG` for the task whose checks run, Lem stops the checks first, then follows `stages/correct.md`.
2. Each time the checks end, Lem says one line with no question, also in the middle of a talk about another topic: the result and the next step, as the step printed them, for example "landing-in-the-background: the checks passed; the review runs, nothing for you". The other lines that `stages/land.md` owes the owner stay as they are.
3. When the checks end while Lem's session is idle between two of the owner's messages, the landing still goes on: with the owner silent for ten minutes after the checks end, the board shows the task at its review or with its pull request open. The background command is the plain `lem land checks SLUG`, which the permission rule `Bash(lem *)` covers.
4. A landing never proposes a task before its checks ended and passed: a task whose checks fail (in this repository `bash tests/all.sh`) gets a repair builder, as today, and no pull request.
5. A check suite that runs longer than ten minutes completes and is read: a suite of twelve minutes ends with its exact last line in the landing's record, and is not cut off at the Bash tool's ten-minute limit. When the checks run three times longer than their last finished run, Lem says so in one line at its next turn, with no question, and "stop the checks" stops them.
6. One task lands at a time, as today: with two tasks `ready`, the second one's checks start only after the first one is proposed.
7. The checks of one task run once at a time: while `lem land checks landing-in-the-background` runs, a second start of the same checks (from a new or compacted Lem session) is refused with a message that says they already run.

## What is there today

Read in the code at `28d3c81`:

- `cmd_checks` in `skills/lem/scripts/land.py` runs each command of `checks.commands` with
  `subprocess.Popen(...)` and `proc.wait()`, then each command of `checks.serial` under
  `project.py serial`, then `criteria.py red` and the bar. It prints its JSON at the end. A
  SIGTERM ends the command that runs with its process group, keeps `gated=None, tree=None`, and
  exits 1 with "the checks were stopped ...". It holds no lock of its own: two runs of one task's
  checks can run at once.
- `gated` in `landing.json` is cleared only on a stop, a red result and before `criteria.py red`;
  a run on a tip that already passed keeps `gated == tip` while its commands run. `read`
  (`cmd_read`) and `propose` go through `gate_holds`, which says yes for `gated == tip`. So a
  second run of the checks on the same tip, in the background, would let `read` and `propose`
  pass before it ends.
- `cmd_start` takes the landing line under `landing.lock` of the state folder, and
  `start_locked` refuses a second task while one is in `landing` ("one branch lands at a
  time"); `tests/lem-land-guards.sh` holds that race. Criterion 6 is that rule, unchanged.
- In this repository `checks.commands` is the unit level and `checks.serial` is `bash
  tests/all.sh` (`.lem/project.toml`). The run of `lem-landing-page` went from `gate.start` at
  10:18:18Z to its last `gate` at 10:22:44Z (`.lem/state/events.jsonl`, 2026-11-19). The
  `gate.start` event holds `tip` and `commands`, and each `gate` event `command`, `exit`, `last`,
  `tip` and, for a serial one, `serial`.
- `skills/lem/harness/claude-code.md`, "## run-in-background", allows one background command, the
  watch, and says that an end which comes while Lem waits between two messages "is not seen yet
  to wake it". The Bash tool's own description in Claude Code 2.1.328 (read 2026-11-19) says that
  `run_in_background` "keeps running across turns and re-invokes you when it exits", and gives
  the 600000 ms limit "for a foreground command". The end of a background `codex exec` woke an
  idle Lem session on 2026-11-19 (the Astra expert, recorded 14:25:11Z; the task's
  `directions.md`).

## Tasks

1. **`lem land checks` knows its own run: one at a time, a status, a stop, a line for the owner,
   and no review or proposal while it runs.** Serves criteria 1 (the stop), 2 (the line), 4, 5
   (the overdue line and the stop) and 7. Files: `skills/lem/scripts/land.py` (its docstring,
   which is `lem land --help`, too), `tests/unit/test_land.py`, `tests/lem-land-guards.sh`.
   - *One run at a time.* `cmd_checks` takes a lock of its own before anything else it does
     (before `gate.start` and before it touches `landing.json`): a non-blocking `flock` on a file
     in the task directory (`checks.lock`), with the process id and the start time written into
     it, held until the step ends however it ends. A second `lem land checks SLUG` while it is
     held exits 1 with a message that says the checks of SLUG already run, since when and in which
     process, that the session which started them goes on when they end, and that `lem land
     checks SLUG --status` says whether they still run. The commands do not inherit the lock's
     file (Popen's `close_fds`), so a server a command left behind does not hold it.
   - *No result while it runs.* `cmd_checks` clears `gated` and `tree` before its first command,
     and `read`, `propose` and `land` refuse while the task's checks run, with a message that
     names the run and says that its end comes first. A test for criterion 4: a first run green on
     a tip, then a second run on the same tip with a slow command; during it `read` is refused,
     where the base commit lets it pass on the kept `gated`.
   - *`--status`.* `lem land checks SLUG --status` prints JSON and starts nothing: `running`,
     `since`, `seconds`; `last_seconds`, the length of the last finished run of the checks in this
     repository, of any task, read from the event log (a `gate.start` followed by a `gate` event of
     the same task and tip for each of its `commands`, each with exit 0; from `gate.start` to the
     last of them), or null when there is none; `overdue`, true when the checks run and `seconds`
     is more than three times `last_seconds`; `say`, the one line for the owner when they are
     overdue ("SLUG: the checks run for 14 min, three times their last run of 4 min 26 s; \"stop
     the checks\" stops them"); and `ended`, the last run of this task's checks that ended (its
     time, its tip, green or not and its `say`), or null, so that a session which did not see the
     end reads it. A look at the lock never makes a real start fail: read the process id from the
     file and test it, or take the lock in a way a start does not meet.
   - *`--stop`.* `lem land checks SLUG --stop` sends SIGTERM to the process the lock names, only
     while the lock is held, waits for its end, and prints whether it stopped one (`stopped`).
     With no run it exits 0 with `stopped: false`, so that `stages/correct.md` can call it for a
     task in `landing` without a look first. The stopped run ends as today: the command and its
     group end, `gated` and `tree` stay null, and the run's own exit says it was stopped.
   - *`say`.* Every result the step prints, the JSON of a green run and the JSON it prints before
     a red refusal (a red command, a criterion's test that does not hold, a lowered bar), has
     `say`: one line with the slug, the result and the next step, with no question, as
     "landing-in-the-background: the checks passed; the review runs, nothing for you" or
     "landing-in-the-background: the checks are red on bash tests/all.sh; a builder repairs it,
     nothing for you". The same line is what `ended` keeps.
   - Unit cases for the rules that take facts (the last run's length from a list of events, the
     overdue call, the `say` lines); the block for what needs processes and git (a second start
     refused while one runs, `--stop` ends a run and leaves `gated` null, `read` refused during a
     run). Run `python3 -B -m unittest discover -s tests/unit` and `bash
     tests/lem-land-guards.sh`, never `tests/all.sh`.

2. **Lem runs the checks in the background and goes on when they end.** Serves criteria 1, 2,
   3, 5 and 6. Files: `skills/lem/stages/land.md` (step 4, and the stage's opening, which says
   what Lem does at each turn while a task is in `landing`), `skills/lem/stages/correct.md`
   (`drop` and `standard-track`), `skills/lem/SKILL.md` ("Between two of the owner's messages
   Lem only waits": the end of the checks wakes it too; "## Status": at each turn, `lem land
   checks SLUG --status` for a task in `landing`), `skills/lem/harness/claude-code.md` ("##
   run-in-background"), `docs/flow.md`.
   - `stages/land.md`, step 4: Lem starts `lem land checks SLUG` with `run-in-background`, the
     plain command, says nothing more and goes on with whatever the owner talks about. One run of
     the checks at a time, and the step refuses a second. When it ends, Lem reads what it printed,
     says its `say` once (on exit 1 with no JSON, the step's own `land.py:` line), and goes on as
     step 4 says today: green to step 5, red to the repair builder. `start`, `base`, `read` and
     `propose` stay in the foreground: they are short (not measured), and only the checks are
     named in the criteria. While the checks run, at each of Lem's turns, `lem land checks SLUG
     --status`: its `say` once when `overdue` turns true; its `ended`, when Lem did not see the end
     of the run (a session that started after it), is that end. "stop the checks" in the owner's
     words is `lem land checks SLUG --stop`, and the landing then waits for his next word.
   - `stages/correct.md`: `drop` and `standard-track` of a task in `landing` run `lem land checks
     SLUG --stop` first.
   - `harness/claude-code.md`: two background commands may run, the watch and the checks, each
     one at a time; the end of a background command wakes an idle session (the Bash tool's
     description and the run of 2026-11-19, above); the 10-minute limit is the foreground's, so a
     check suite of twelve minutes runs to its end in the background. Stop the checks with
     `--stop`, never with the tool's own stop alone: that ends the shell and may leave the
     script's process running with its lock.
   - `docs/flow.md`: one sentence in its STE, where it says that the checks run, that the owner
     can talk to Lem while they run.
   - No test: a stage file's test is a real task (`AGENTS.md`, "Checks"), and this task's own
     landing is that run for criteria 1, 2, 3 and 5.

## Decisions

- The stop goes through the script (`--stop`, by the process id in the lock), not only through
  the tool that started the background command: a new or compacted session does not hold the
  first session's background task, and a stop of the shell alone may leave the Python process and
  its lock behind.
- "Their last finished run" is the last run in this repository whose commands all ran and passed,
  of any task: a red run stops before the serial commands and would make the next run look
  overdue. With no such run there is no overdue line.
- `read`, `propose` and `land` refuse while the checks run, and the checks clear their kept
  result before their first command: with the checks in the background, Lem's session is free to
  run another step of the same task, and criterion 4 says no proposal comes before the checks
  ended.
- Only `checks` moves to the background. The other steps stay as they are.

## Not verified

- Criteria 1, 2, 3 and 5 (its twelve-minute suite) are about a session's behavior: whether the
  owner gets an answer during the checks, whether an idle session wakes at their end, and
  whether a background command outlives ten minutes. No test in `tests/` holds them; the owner
  asked for quick test runs ("I demand quick tasks run", 2026-11-19), and the twelve-minute run
  is one real run, as the task's directions say. This task's own landing is the first run of
  1, 2 and 3.
- Criterion 6 is today's rule, which `tests/lem-land-guards.sh` already holds; the change keeps
  it.
