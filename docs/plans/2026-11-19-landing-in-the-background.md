# The landing's checks run in the background

careful: yes, because task 1 changes when the landing reads the result of the checks and adds a refusal to `read` and `propose`, which reaches the owner's topic "The landing lets through a change that should not land: one the checks or the review did not pass, one a person should merge, or one aimed at a protected branch", and a run that is stopped must leave `landing.json` true, which reaches "A task's record is lost or wrong".

## Acceptance criteria

Size: full, because the landing's longest step moves out of Lem's foreground, Lem must pick the landing up again when it ends, and the change is careful.

1. While a task's checks run, Lem's session answers the owner: in a landing whose checks take 4 min 26 s, as `lem-landing-page`'s did on 2026-11-19, a message he types one minute after the checks start gets its answer before they end. When that message is `/lem drop SLUG` or `/lem standard-track SLUG` for the task whose checks run, Lem stops the checks first, then follows `stages/correct.md`.
   - test: `bash tests/lem-land-guards.sh` in `tests/lem-land-guards.sh`, `tests/lib.sh`, `tests/checks.sh`
2. Each time the checks end, Lem says one line with no question, also in the middle of a talk about another topic: the result and the next step, as the step printed them, for example "landing-in-the-background: the checks passed; the review runs, nothing for you". The other lines that `stages/land.md` owes the owner stay as they are.
   - test: `python3 -B -m unittest tests.unit.test_land.ChecksSay` in `tests/unit/test_land.py`
3. When the checks end while Lem's session is idle between two of the owner's messages, the landing still goes on: with the owner silent for ten minutes after the checks end, the board shows the task at its review or with its pull request open. The background command is the plain `lem land checks SLUG`, which the permission rule `Bash(lem *)` covers.
   - no test: a session's behavior while it is idle, which no test in `tests/` can hold; task 3's one real run did not happen, since Claude Code asked to trust the new folder and that answer is the owner's, so the run waits for him
4. A landing never proposes a task before its checks ended and passed: a task whose checks fail (in this repository `bash tests/all.sh`) gets a repair builder, as today, and no pull request.
   - test: `bash tests/lem-land-guards.sh` in `tests/lem-land-guards.sh`, `tests/lib.sh`, `tests/checks.sh`
5. A check suite that runs longer than ten minutes completes and is read: a suite of twelve minutes ends with its exact last line in the landing's record, and is not cut off at the Bash tool's ten-minute limit. When the checks run three times longer than their last finished run, Lem says so in one line at its next turn, with no question, and "stop the checks" stops them.
   - test: `python3 -B -m unittest tests.unit.test_land.Overdue` in `tests/unit/test_land.py`
   - test: `python3 -B -m unittest tests.unit.test_land.LastRun` in `tests/unit/test_land.py`
6. One task lands at a time, as today: with two tasks `ready`, the second one's checks start only after the first one is proposed.
   - no test: the change keeps behavior; the suite holds it
7. The checks of one task run once at a time: while `lem land checks landing-in-the-background` runs, a second start of the same checks (from a new or compacted Lem session) is refused with a message that says they already run.
   - test: `python3 -B -m unittest tests.unit.test_land.HeldRefusal` in `tests/unit/test_land.py`

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

1. **`lem land` runs one step of a task at a time, and `checks` knows its own run: a status, a
   stop, an end on record and a line for the owner.** Serves criteria 1 (the stop), 2 (the line),
   4, 5 (the overdue line and the stop) and 7. Files: `skills/lem/scripts/land.py` (its
   docstring, which is `lem land --help`, too), `tests/unit/test_land.py`,
   `tests/lem-land-guards.sh`.
   - *One step of a task at a time.* Every step of `lem land` that names a task (`start`, `base`,
     `polish`, `checks`, `read`, `file`, `propose`, `land`, `merged`, `clean`) takes the task's
     one step lock before anything else it does (before `gate.start`, before a fetch, before it
     touches `landing.json` or the worktree): a non-blocking `flock` on `step.lock` in the task
     directory, held until the step ends however it ends. Its first act after the lock is to write
     into the file the step's name, its process id and its start time. A step of the same task
     while the lock is held exits 1 and names the step that holds it, since when and in which
     process. When that step is `checks`, the message says that the checks of SLUG run, that their
     end comes first, that the session which started them goes on when they end, and that `lem
     land checks SLUG --status` says whether they still run; for a second `checks` it says that
     they already run (criterion 7). `checks --status`, `checks --stop` and `watch` take no lock.
     The commands do not inherit the lock's file (Popen's `close_fds`), so a server a command left
     behind does not hold it.
   - *No result while it runs.* `cmd_checks` clears `gated` and `tree` before its first command,
     so a run cut off with no chance to clean up leaves no result of an earlier run for its tip.
     Tests for criterion 4, in both orders: during a slow run on a tip that passed before, `read`,
     `propose` and `base` are refused, where the base commit lets `read` pass on the kept
     `gated`; and while the test holds the task's step lock as another step would, `checks` is
     refused.
   - *The end of a run.* Every run that logged `gate.start` logs one `gate.end` event when it
     ends, however it ends: `result` (`passed` when the step returns its JSON and keeps `gated`;
     `red` for a command of the checks that failed; `refused` for a criterion's test that does
     not hold, a lowered bar, or a command that changed the tree; `stopped` for a stop), `seconds`
     from its `gate.start`, `tip`, and `say`. A run is that pair of events.
   - *`--status`.* `lem land checks SLUG --status` prints JSON and starts nothing: `running`, true
     when the step lock is held by `checks`; `since` and `seconds` of that run; `last_seconds`,
     the `seconds` of the newest `gate.end` with `result` `passed` in this repository's event log,
     of any task, or null when there is none; `overdue`, true when the checks run and `seconds` is
     more than three times `last_seconds`; `say`, the one line for the owner when they are overdue
     ("SLUG: the checks run for 14 min, three times their last run of 4 min 26 s; \"stop the
     checks\" stops them"); and `ended`, the newest `gate.end` of this task (its time, its tip,
     its `result`, its `say`, and `resumed`, the line for a session that did not start the run:
     "SLUG: its last run of the checks ended at TIME, RESULT; the landing goes on from its first
     step, as after a cut-off"), or null. A look at the lock never makes a real start fail: read
     the process id from the file and test the lock without holding it in a way a start meets.
   - *`--stop`.* `lem land checks SLUG --stop` sends SIGTERM to the process the lock names, only
     while the lock is held by `checks`, waits until the lock is free, and prints whether it
     stopped one (`stopped`). With no run it exits 0 with `stopped: false`, so that
     `stages/correct.md` can call it for a task in `landing` without a look first. A stop reaches
     every process the run started, through each one's own cleanup, and the lock goes last:
     `cmd_checks` keeps its SIGTERM handler from the lock to its last line, `criteria.py red` and
     the bar included; on a stop during `criteria.py red` it sends that child SIGTERM and waits
     for its end, so that its own handler ends its tests and removes its two worktrees (the
     child is never killed first, as `subprocess.run` does on an exception); and `end_group`
     gives the wrapper of a serial command the time of its own cleanup (`project.py serial`: a
     term, three seconds, a kill) before it kills it. The stopped run then ends as today: `gated`
     and `tree` stay null, and its exit says it was stopped.
   - *`say`.* Every end of the step has `say`, in the JSON it prints and in its `gate.end`: one
     line with the slug, the result and the next step, with no question, as
     "landing-in-the-background: the checks passed; the review runs, nothing for you",
     "landing-in-the-background: the checks are red on bash tests/all.sh; a builder repairs it,
     nothing for you", or "landing-in-the-background: the checks were stopped; the landing waits
     for your word". A stopped or refused run prints its JSON with `say` before its exit 1, as a
     red one does today.
   - Unit cases for the rules that take facts (`last_seconds` from a list of events, the overdue
     call, the `say` lines); the block for what needs processes and git (a second `checks`
     refused while one runs; `base` and `read` refused during a run and `checks` refused while
     the lock is held; `--stop` during a command of the checks and during the criteria' tests
     ends the run with no process of it left, no `SLUG.red-*` worktree, `gated` null, the lock
     free and a `gate.end` of `stopped`). Run `python3 -B -m unittest discover -s tests/unit`
     and `bash tests/lem-land-guards.sh`, never `tests/all.sh`.

2. **Lem runs the checks in the background and goes on when they end.** Serves criteria 1, 2,
   3, 5 and 6. Files: `skills/lem/stages/land.md` (step 4, and the stage's opening, which says
   what Lem does at each turn while a task is in `landing`), `skills/lem/stages/correct.md`
   (`drop` and `standard-track`), `skills/lem/SKILL.md` ("Between two of the owner's messages
   Lem only waits": the end of the checks wakes it too; "## Status": at each turn, `lem land
   checks SLUG --status` for a task in `landing`), `skills/lem/harness/claude-code.md` ("##
   run-in-background"), `docs/flow.md`.
   - `stages/land.md`, step 4: Lem starts `lem land checks SLUG` with `run-in-background`, the
     plain command, says nothing more and goes on with whatever the owner talks about. One run of
     the checks at a time, and the step refuses a second. When the run its own session started
     ends, Lem reads what it printed, says its `say` once (on exit 1 with no JSON, a refusal
     before `gate.start`, the step's own `land.py:` line), and acts by its `result`: `passed`, the
     step after the checks in the path that ran them (step 5; for a task brought onto the base in
     step 9, that path's read and its `propose` with the last proposal's title); `red` or
     `refused`, the repair builder, as step 4 says today; `stopped`, nothing, since the word that
     stopped it (a drop, a track change, "stop the checks") says what comes next. A session that
     did not start the run (one that started after it) says the `resumed` line of `ended` once,
     never the run's own `say`, whose next step was that of the session that saw the run end, and
     takes the landing up by the stage's rule for a session before it that was cut off. Criterion
     2's "as the step printed them" is the line of the session that saw the run end; the
     `resumed` line is for a session that did not, so that no line names a next step that is not
     the landing's next step now. A step of the
     task that the step lock refuses while the checks run is not sent again: it waits for their
     end. `start`, `base`, `read` and `propose` stay in the foreground: they are short (not
     measured), and only the checks are named in the criteria. While the checks run, at each of
     Lem's turns, `lem land checks SLUG --status`: its `say` once when `overdue` turns true. "stop
     the checks" in the owner's words is `lem land checks SLUG --stop`, and the landing then waits
     for his next word.
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
   - No test: a stage file's test is a real task (`AGENTS.md`, "Checks"), and task 3 is that run
     for criteria 1, 2, 3 and 5.

3. **One real run with this branch's plugin.** Serves criteria 1, 2, 3 and 5. No file of the
   repository changes; the builder's report is the record, and the criteria's lines for 1, 2, 3
   and 5 are `- no test:` lines that name it. This task's own landing runs on the installed
   plugin, whose `bin/lem` runs the scripts of its own folder (`bin/lem`, `ROOT`), so it runs the
   code before this change and is not the run.
   - A throwaway clone of this repository at the branch's tip, outside the worktree, whose main
     checkout's `.lem/project.toml` has as its one `checks.serial` command a command of twelve
     minutes that ends with a known last line, and one task in it brought to `ready`.
   - An agterm session of its own, opened by the builder, started in the clone with `claude
     --plugin-dir WORKTREE`, so that its skill, its harness and its `lem` are this branch's. The
     builder types into it with `agtermctl session type`, as the owner would: `/lem land`; one
     message about another topic one minute after `gate.start`; then nothing for ten minutes
     after `gate.end`.
   - The report holds, from the clone's event log and the session's screen text: the time of the
     message and of its answer beside the run's `gate.start` and `gate.end` (criterion 1); the
     `say` line on the screen, and that no question came with it (criterion 2); the task's state
     ten minutes after `gate.end` (criterion 3); and the `last` of the twelve-minute command in
     `landing.json` beside the last non-blank line of its output file, both with the white space
     around them taken off as `cmd_checks` takes it, and that line as the command printed it,
     with no white space around it, so that the two forms are one; with the run's `seconds` over
     600 (criterion 5). The overdue line is held by the unit cases of task 1.
   - For each of those criteria the report opens with one line, held or not held, by the
     criterion's own numbers, with the times under it: criterion 1 is held when the answer came
     less than 4 min 26 s after `gate.start` and before `gate.end`; criterion 3 is held when, ten
     minutes after `gate.end`, the board shows the task at its review or in its "Pull request"
     band, where it draws an `open` task that is a branch ready to land with no GitHub remote
     (`board.html`, `stageOf`; `project.py`, the `open` state), and the line says that the local
     copy has no GitHub pull request. This reading of criterion 3 is decision 8 of the task's
     record, which the pull request lists as taken without the owner.
   - The builder closes the session and removes the clone and its worktrees at the end. A run it
     cannot hold to the end is said in its report as such, with where it stopped: no criterion is
     marked as held by a run that did not happen.

## Decisions

- The stop goes through the script (`--stop`, by the process id in the lock), not only through
  the tool that started the background command: a new or compacted session does not hold the
  first session's background task, and a stop of the shell alone may leave the Python process and
  its lock behind.
- "Their last finished run" is the newest `gate.end` in this repository whose `result` is
  `passed`, of any task: a red run stops before the serial commands and would make the next run
  look overdue, and only the end event marks a run as finished (the criteria' tests and the bar
  come after the last `gate`). With no such run there is no overdue line.
- Every step of a task's landing takes the task's one step lock, and the checks clear their kept
  result before their first command: with the checks in the background, Lem's session (or a
  second one, as criterion 7 names) is free to run another step of the same task, in either
  order. Criterion 4 says no proposal comes before the checks ended, and `gate_holds` takes a kept
  `gated == tip` as a pass; `base` and `clean` change the worktree the checks run in.
- Only `checks` moves to the background. The other steps stay as they are.

## Not verified

- Criteria 1, 2, 3 and 5 (its twelve-minute suite) are about a session's behavior: whether the
  owner gets an answer during the checks, whether an idle session wakes at their end, and
  whether a background command outlives ten minutes. No test in `tests/` holds them; the owner
  asked for quick test runs ("I demand quick tasks run", 2026-11-19), and the twelve-minute run
  is one real run, as the task's directions say: task 3, in a session that loads this branch's
  plugin.
- Criterion 6 is today's rule, which `tests/lem-land-guards.sh` already holds; the change keeps
  it.

## Plan talk

Who argued the plan: the reviewer, Codex, GPT 6.2 Sol at high effort (its pane's status line);
the defender, Claude Code, Opus 5.5 at high effort (the `defender:` line of the task's state).
Two families. 7 turns over 8 questions (the bound is 4 × 8 + 2 = 34). Agreement carries no
authority: the review before the pull request reads each settled position as a claim.

The list, as the reviewer gave it, and how each question ended:

1. **A proposal could pass the old gate while a new run of the checks starts, and `base` could
   rebase the worktree during a run.** Settled: every step of `lem land` that names a task takes
   the task's one step lock (task 1, "One step of a task at a time"), which excludes both orders
   and `cmd_base`; `cmd_propose`, `cmd_base` (`gated=None`) in `land.py`. Settled by the two, not
   checked by the review.
2. **A pull request closed on the forge during a run: `merged` and `clean` could remove the
   worktree while the checks run.** Settled by the same lock: `cmd_merged` and `cmd_clean` wait
   for the run's end, `cmd_propose` then meets the closed pull request, and `start_locked` still
   sees the task in `landing`. Settled by the two, not checked by the review.
3. **The stop by the process id in the lock may not reach the exact run, and did not reach the
   criteria' tests or a serial command's cleanup.** The reach was repaired (task 1, "--stop": the
   SIGTERM handler for the step's whole length, the child `criteria.py red` stopped through its
   own handler, `end_group` that waits for `project.py serial`'s cleanup). What held a second
   time: the process id has no link to the current holder of the lock, so a run that ends and a
   step of another session that takes the lock before the TERM is sent makes `--stop` miss the
   run and wait on the other step; and a stale id in the file may have been reused. A design
   choice:
   - kept: the stop by the process id the lock file names, only while the lock is held, as task 1
     says. Its cite is `harness/claude-code.md`, "## run-in-background": a background command an
     earlier session started is not the new session's, and only `TaskStop` in the session that
     started it stops it through the tool. The defender's position: the race needs a second Lem
     session of the same repository to start a step of the same task inside two calls of one
     process, which is no realistic input here, and its worst outcome is `stopped: false` and a
     wait on a short step.
   - the reviewer's position: the plan itself admits a second session at this step (criterion
     7), and nothing ties the id to the current holder, so the signal is not safe as designed.
   - the ladder: the gate judged it cheap (a reversal stays inside `land.py`, and no developer
     sees either difference), so the kept decision stands (`lem decisions list`, decision 6).
4. **A session that did not start the run cannot tell which result to act on, nor whether its
   next step already ran.** The end of a run was repaired at the cause: `gate.end` with `result`
   (`passed`, `red`, `refused`, `stopped`), `seconds`, `tip` and `say`; task 2 acts by `result`
   for the run its own session started, and a session that did not start it says the `say` of
   `ended` once and takes the landing up by the stage's cut-off rule. What held a second time:
   task 2 makes no test of `builder.start` when it resumes; and after `cmd_base` clears the gate,
   a new session can say an older `passed` line ("the review runs") whose next step is wrong for
   the landing as it is now. A design choice:
   - kept: `ended` is only said, never acted on; the cut-off rule (`stages/land.md`, lines 41 and
     42) runs the steps again, and `builder.start` is on record for a reader (`stages/land.md`,
     lines 301 to 305; `board.html` reads it).
   - the reviewer's position: the line a new session says can name a next step that is not the
     next step of the landing as it is now.
   - the ladder: the gate judged it checkable by the rule "Lem owns the truth of its words"
     (`AGENTS.md`, "Lem is a companion, not a gate"), which the kept line breaks; so task 1's
     `ended` has a `resumed` line, and task 2 has a session that did not start the run say that
     line, which names the result as past and the next step as it is now (`lem decisions list`,
     decision 7).
5. **The continuation after a green end of a task brought onto the base in step 9.** Settled:
   task 2 sends a passed end to the step after the checks in the path that ran them; for a session
   that did not start the run, the cut-off rule is the scope, and `synced`, `title` and
   `notes.md` are on disk. Settled by the two, not checked by the review.
6. **The length of "their last finished run" was not a run that finished.** Settled by the same
   `gate.end` as 4: `last_seconds` is the `seconds` of the newest `gate.end` with `result`
   `passed`. Settled by the two, not checked by the review.
7. **Which text is "the exact last line" of criterion 5.** The defender's refutation (the stage's
   own term, `stages/land.md` step 4, and `cmd_checks`'s `last`) held as to the term; the repair
   then made task 3 compare both forms with the white space taken off as `cmd_checks` takes it,
   with a last line that has none. Settled by the two, not checked by the review.
8. **Which run checks criteria 1, 2, 3 and 5.** Repaired at the cause: this task's own landing
   runs on the installed plugin (`bin/lem`, `ROOT`), so task 3 is one real run in a session that
   loads this branch's plugin. What held a second time: in a throwaway clone with no pull request
   the review can end before the ten minutes of criterion 3, and the task is then `open` with no
   pull request, which is neither outcome the criterion names at that time; and a twelve-minute
   run lets an answer later than 4 min 26 s show in the report beside the criterion's case. A
   design choice:
   - kept: task 3 as written: its report records times and events, not a pass, so a reader sees
     an answer after 4 min 26 s and a task past its review; `board.html` draws "The review runs"
     from `review.start`.
   - the reviewer's position: at the time the criterion names, the board of such a run can show
     neither outcome, and the times can show an answer that misses the criterion's case.
   - the ladder: the gate held it and added two options (two runs, each built for one
     criterion's case; new words for criterion 3 first); a check of the panel's brief found that
     the board already draws an `open` task with no GitHub remote in its "Pull request" band
     (`board.html`, `stageOf`; `project.py`, the `open` state); the personas split (the
     developer: a held line for each criterion, sure; the teammate: new words for criterion 3,
     leaning, else the held lines with the reading listed); the dialectic found no break of the
     held lines. The owner had said he was away (17:10:59Z, "complete everything /lem dnd"), so
     `lem decisions ask` took the ladder's pick: task 3's report gives a held or not-held line
     for each criterion, and the pull request is not green for that choice (decision 8).

The mechanisms the repairs added:

- the task's one step lock: sits on the decision "what keeps a proposal from coming before the
  checks end" (Decisions, bullet 3), which rests on criterion 4 and `gate_holds`; the reviewer:
  closed, at the cause.
- `gate.end`: sits on the decision "their last finished run" (Decisions, bullet 2) and on
  `--status`'s `ended`, which rested on the planner's choice; the reviewer: at the cause.
- the stop's reach (the handler for the whole step, the stop of the criteria' child, the wait in
  `end_group`): sits on the decision "the stop goes through the script" (Decisions, bullet 1);
  the reviewer: holds, a layer over that decision, which closed as the design choice of 3.

Raised, not argued:

- A stopped run leaves the task in `landing`, and `skills/lem/assets/board.html` (lines 1346 to
  1363) still draws "The checks run" from the prior `gate.start` or `gate`, since it does not read
  `gate.end` (the reviewer, its second turn).

Refused as unpriced: none.

What changed in the plan, by question and by task:

- task 1: the lock of `checks` alone became the task's one step lock over every step (1, 2); the
  refusal list in `read`, `propose` and `land` went, and the tests cover both orders (1); a new
  bullet, "The end of a run", with `gate.end` (4, 6); `--status` reads `gate.end` and the lock's
  step (4, 6); `--stop` waits for the lock and reaches the criteria' child and the serial
  wrapper's cleanup (3); `say` covers a stopped and a refused end (4); the block tests (1, 3).
- task 2: the end acts by `result` for the run its own session started, a passed end goes to the
  step after the checks in its path, step 9's included, and a session that did not start the run
  only says `ended` (4, 5); a step that the lock refuses during the checks waits for their end
  (1); its last line names task 3 (8).
- task 3, new: one real run with this branch's plugin, with the last line compared as
  `cmd_checks` keeps it (8, 7).
- Decisions and Not verified: bullets 2 and 3 of Decisions follow 6 and 1; Not verified names
  task 3 (8).
