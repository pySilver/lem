# Away for the whole machine

> **Status: built** in `3662a3f` (2026-11-20). The one mark of the machine still holds; the redesign of 2026-11-20 ([2026-11-20-a-session-for-each-task.md](2026-11-20-a-session-for-each-task.md))
> moved its watch from Lem's session to the shape's session of each task, and the mark changes
> nothing in a build.

careful: yes, because two topics are in reach: "A decision that is the owner's is taken without him, or one taken for him is missing from the pull request he reads" (task 1 moves the one fact that `decisions.py` `take`, `cmd_wait`, `criteria.py --alone` and `land.py` `may_merge` and `without_owner` act on, so a wrong read takes his choices in every repository at once or drops a span from a pull request), and "Lem writes over something of the developer's: a file in his home" (task 1 writes the first file Lem keeps under the home directory, and every test suite that calls `lem project owner` today would write it unless the run is kept away from it); and "A change bends a ruling of the owner" is near, since "One Lem for one repository" and "his being there is one status of the repository" (AGENTS.md) are read against a fact that now holds across repositories, which the owner's interview of 2026-11-19 settled (`directions.md`) and task 4 writes down.

## Acceptance criteria

Size: full, because the owner's status moves from each repository's event log to one mark in the home directory, which every script that reads his status, the board and the landing read, and a wrong read takes his choices in every repository at once.

1. One `/lem im-away`, typed in any repository, marks the owner away in every repository on the Mac: he types `/lem im-away` in the lem repository at 14:05, and `lem project waiting` in mybaze then says that he is away since 14:05.
   - test: `bash tests/lem-state.sh` in `tests/lem-state.sh`, `tests/lib.sh`, `tests/checks.sh`
2. One `/lem im-back`, typed in any repository, marks him back in every repository: he types `/lem im-back` in mybaze at 16:30, and `lem project waiting` in the lem repository then says that he is there.
   - test: `bash tests/lem-state.sh` in `tests/lem-state.sh`, `tests/lib.sh`, `tests/checks.sh`
3. No repository has an away status of its own. The one mark is kept under `~/.config/lem`, or under `$XDG_CONFIG_HOME/lem` when that variable is set, and a Mac with no mark reads him as there: on a new Mac where he never typed `/lem im-away`, every repository reads him as there.
   - test: `bash tests/lem-state.sh` in `tests/lem-state.sh`, `tests/lib.sh`, `tests/checks.sh`
   - test: `python3 -B -m unittest discover -s tests/unit -p test_owner.py` in `tests/unit/test_owner.py`
4. A choice that waits for him in another repository is taken when he goes away: a lead in mybaze waits on choice 2 of `fix/report-dates`; he types `/lem im-away` in the lem repository; mybaze's choice 2 is then taken with the ladder's pick within seconds, and that pull request is not green for it. A step that a later "no" cannot reverse still waits for him, as today.
   - test: `bash tests/lem-decisions.sh` in `tests/lem-decisions.sh`, `tests/lib.sh`, `tests/checks.sh`
5. Lem's session in another repository acts on the mark with no message from him there: mybaze has a task whose acceptance criteria wait for his yes; he types `/lem im-away` in the lem repository; Lem in mybaze then approves those criteria without him and starts their lead, as if he had typed `/lem im-away` in mybaze.
   - test: `bash tests/lem-state.sh` in `tests/lem-state.sh`, `tests/lib.sh`, `tests/checks.sh`
6. A night task always runs without him, also while he is marked as there: a night task in mybaze builds at 02:00; he types `/lem im-back` in the lem repository at 02:10 because he works late; a choice of that night task is still taken without him, and does not wait for his answer.
   - test: `bash tests/lem-decisions.sh` in `tests/lem-decisions.sh`, `tests/lib.sh`, `tests/checks.sh`
   - test: `python3 -B -m unittest discover -s tests/unit -p test_owner.py` in `tests/unit/test_owner.py`
7. The board and the pull request of a task in another repository show the time without him: after `/lem im-away` in the lem repository at 14:05, the board of mybaze says "You are away since 14:05", and a mybaze pull request whose task ran from 14:00 to 17:00 says that it ran without the owner from 14:05 to 16:30.
   - test: `bash tests/lem-state.sh` in `tests/lem-state.sh`, `tests/lib.sh`, `tests/checks.sh`
   - test: `python3 -B -m unittest discover -s tests/unit -p test_owner.py` in `tests/unit/test_owner.py`
   - test: `bash tests/test-board.sh` in `tests/test-board.sh`, `tests/checks.sh`
8. Lem writes only its own mark in the home directory, and the test suites never touch it: a full run of `bash tests/all.sh` leaves `~/.config/lem` as it was before the run.
   - test: `bash tests/lem-state.sh` in `tests/lem-state.sh`, `tests/lib.sh`, `tests/checks.sh`
   - test: `python3 -B -m unittest discover -s tests/unit -p test_owner.py` in `tests/unit/test_owner.py`

## What the code does today

Read in the code at `ac05a78`, and in the scout's report (`scout.md` of the task directory).

- `lem project owner away|back --words TEXT` (`project.py` `cmd_owner`) appends an `owner` event with
  `task: null` to the repository's own `.lem/state/events.jsonl` and `events.js`
  (`append_event`). It writes nothing when nothing changes, except that `back` is written while he
  is there if a task of that repository runs without him, because `back` also ends a night's span.
  After an `away` it runs `decisions.py --repo ROOT away` for that one repository.
- `owner_now(records)` gives `{away, since, words}` from the newest `owner` event;
  `cmd_waiting` gives it as `owner`.
- `read_tasks` reads `events_named(root, "task.mode", OWNER, "task.state")` in the log's order
  and gives each task `mode`, `mode_since` and `without_owner` from `runs_without_owner`. There a
  `back` sets both `away` and `own` (the night's mark) to `None`: "The owner's 'back' ends both."
- Every other reader takes the mode from `lem project tasks`: `decisions.py` (`Task.read_status`,
  `take`, `cmd_wait`, which reads the mode again every 2 s, `cmd_away`), `criteria.py` (`--alone`),
  `land.py` (`may_merge` at `mode == "alone"`, `without_owner` for the pull request's line). No
  script but `project.py` reads an `owner` event.
- `board.html` `derive` takes the header's "You are away since ..." from the `owner` events of
  `events.js` in its own state folder. A board page reads only files beside it (`readScript`,
  `events.js`, `meta.js`, `watch.js`, `backlog.js`), and `board.py` `prepare` writes `meta.js`
  and `backlog.js` at each run.
- No script under `skills/lem/scripts/` names a folder in the home directory today except
  `doctor.py`. `tests/lib.sh` sets no `HOME` and no `XDG_CONFIG_HOME`, `tests/all.sh` runs the
  suites at once, and `tests/lem-state.sh` and `tests/lem-decisions.sh` call `owner away` and
  `owner back`: with a mark in the home directory and no change to the tests, a run of them would
  mark the developer away for real.

## Tasks

1. **The one mark, and every script reads it.** Serves criteria 1, 2, 3, 4, 6, 7 (its pull
   request part) and 8. Files: `skills/lem/scripts/lem_state.py`, `skills/lem/scripts/project.py`
   (with its `--help` text of `owner` and of the event log), `skills/lem/scripts/criteria.py`
   (`cmd_approve`), `skills/lem/scripts/land.py` (`may_merge`), `tests/lib.sh`, `tests/all.sh`,
   `tests/test-board.sh`, `tests/test-ask-expert.sh`, the
   unit cases in `tests/unit/` (a new case file or `test_task.py`), `tests/lem-state.sh`,
   `tests/lem-decisions.sh`, and each other block or unit case whose checks call `owner` or read
   an `owner` event from a repository's log (`grep -rn "owner away\|owner back\|\"owner\"" tests`).
   - *The place*: `lem_state.py` names it, as it names the state folder: a function that gives
     `$XDG_CONFIG_HOME/lem` when that variable is set and not empty, and `~/.config/lem`
     otherwise (`Path.home()`), and the one file in it, `owner.jsonl`. A read never makes the
     folder: no file is "there", with `since` null, as `owner_now` gives today for an empty log.
     Only a write of the mark makes the folder, and nothing else of Lem's goes into it.
   - *The record*: one JSON line for each status he says, appended, in the form the `owner`
     event has today, so that `owner_now` and `runs_without_owner` read it unchanged:
     `{"ts", "event": "owner", "task": null, "away": true|false, "by": "owner", "words": TEXT,
     "repo": MAIN_CHECKOUT}`, `repo` being where he typed it, for a reader of the file. A line
     that does not read as JSON is refused with the file and the line number, as `events_named`
     refuses one of the event log.
   - *The write*: `cmd_owner` appends to the mark and never to the repository's log. It writes
     only when the status changes: `away` while he is away, and `back` while he is there, write
     nothing (`written: false`). The condition on the repository's own tasks goes, since a `back`
     no longer ends a night (below). It still runs `decisions.py away` for its own repository
     after an `away`, and gives `tasks` and `taken` of its own repository as today. `cmd_log`
     keeps refusing an `owner` event in a repository's log.
   - *The reads*: `cmd_waiting` gives `owner` from the mark, with `seen`, the number of records
     in it, which the watch of task 2 takes. `read_tasks` takes the repository's
     `task.mode` and `task.state` events from its log and the mark's records, and puts them in
     one list in the order of `ts`; on the same second, the repository's events come first (a
     stable sort of the repository's list followed by the mark's). The cut of an ended task at its
     newest event stays. An `owner` event that a repository's log still holds is not read: Lem
     keeps no reading of the form before it (AGENTS.md).
   - *The night*: in `runs_without_owner` a `back` ends the span that `away` started and never a
     task's own mark: a night's task runs without him until it ends, whatever his status (the
     interview, `directions.md`). The docstrings of `runs_without_owner` and `nights` say so.
   - *The readers act on the mode as it is at the act*: with the mark, another repository's
     session can change the mode while a command of this one runs. `decisions.py` already reads
     the mode again under its lock (`Task.add` calls `read_status`, which sets `mode`). So
     `criteria.py` `cmd_approve` reads the task's mode again under `criteria.lock`, before its
     `--alone` check, and `land.py` `may_merge` reads the task's record again (`lem project
     tasks`) after the forge's answer and before its check of `mode`. The decision it sits on:
     "every script reads the mark directly", with `decisions.py` `Task.add` as the existing code
     it follows. Its cost: one more read of `lem project tasks` for each merge by an agent and
     each `--alone` approval.
   - *The tests never touch the home directory*: every file of `tests/` that makes a `WORK`
     folder of its own exports `XDG_CONFIG_HOME` as a folder under that `WORK` on the next line:
     `tests/lib.sh`, which every block sources, and each `test-*.sh` that sets `WORK=` itself
     (`grep -ln '^WORK=' tests/*.sh`; today `test-board.sh` and `test-ask-expert.sh` reach the
     mark, and a developer runs each alone, as the Checks of AGENTS.md list them). `tests/all.sh`
     exports one under its own temporary folder before it starts the suites, for a suite with no
     `WORK` of its own. A unit case that reaches the mark sets
     `XDG_CONFIG_HOME` to a temporary folder in its `setUp` and puts it back after, since `python3
     -B -m unittest discover -s tests/unit` runs without `all.sh`. Check, before the export,
     which suites call a real `gh`, `codex` or `claude` that reads its own settings under
     `XDG_CONFIG_HOME`, and give each such call what it needs; say in the report what was found.
   - *Checks that assumed a status of the repository's own*: within one block every repository
     now shares one mark. A check that marks the owner away in one repository and expects
     another to read him as there puts him back first, or uses a mark of its own
     (`XDG_CONFIG_HOME=...` on that call). The check of "exactly 2 `owner` lines in
     `events.jsonl`" becomes a check of the mark's lines, and of no `owner` line in the log.
   - *Tests that hold the criteria*: two repositories in one block, `away` in the first, `lem
     project waiting` in the second gives `owner.away` true with the same `since` (1); `back` in
     the second, the first reads him as there (2); with an empty `XDG_CONFIG_HOME` folder every
     repository reads him as there, the mark is written under `$XDG_CONFIG_HOME/lem` after an
     `away`, and under `HOME/.config/lem` with the variable unset and a `HOME` of the check's own
     (3, 8); a lead's `lem decisions wait` on a choice of a task in the second repository ends
     with the choice taken after `away` in the first, and an `--irreversible` choice there still
     waits (4); a task opened with `task-dir --night` in the second repository stays `alone` after
     a `back` in the first, and its choice is taken (6); the pull request's text, or `land.py`'s
     line of the time without the owner, for a task of the second repository names the span from
     the `away` of the first to the `back` of the second (7). The unit cases call
     `runs_without_owner` and `owner_now` with records: a `back` that leaves a night's span open,
     a merge with the same second in both lists, and a missing mark file.

2. **Lem in each repository hears the mark, and its board shows it.** Serves criteria 5 and 7
   (its board part). Files: `skills/lem/scripts/project.py`, `skills/lem/scripts/board.py`,
   `skills/lem/assets/board.html`, `tests/lem-state.sh`, `tests/test-board.sh` and the fixture or
   demo data that gives the board an `owner` event (`board.py --demo`, `tests/board-showcase.py`).
   - *The watch*: `lem project owner watch --seen N`, where `N` is the number of records in the
     mark, which `lem project waiting` gives as `owner.seen` (0 with no mark). It looks at the
     mark once every 5 seconds and ends with exit 0 and the status as JSON (`away`, `since`,
     `words`, `seen`) as soon as the mark holds another number of records than `N`, at once when
     that is so at its start: so no change is lost between Lem's read of the status and the
     watch's start. The count is the cursor and a time is not, because a `ts` has whole seconds
     and two records can share one; the mark is only appended to and nothing removes a line (the
     plan's first decision), so a new record always changes the count. It is built after `lem land
     watch` (`land.py`), which a Lem session already keeps in the background, and is refused
     outside a repository like every command of `project.py`. It writes nothing to the mark.
     The interval is a guess, not a measurement, and the code says so beside it.
   - *The board's copy*: `owner.js` in the state folder, one `lemOwner({...});` line for each
     record of the mark, written whole (a temporary file and a rename, so that the page never reads
     half of it) by `cmd_owner` after its write, by the watch at its start and at its end, and by
     `board.py` `prepare` at each run. `board.html` reads it with `readScript` in `pollFiles`
     beside `watch.js`, takes the header's `away` from its newest record, and no longer from the
     `owner` events of `events.js`. A missing `owner.js` is no problem: he is there.
   - *Which board criterion 7 covers*: the board of a repository where Lem's session runs, as
     the task's outcome says ("every repository on this machine where Lem runs a task"). That
     session keeps the watch, so `owner.js` there is written again at each change of the mark. A
     board of a repository where no Lem session runs shows the mark as of its last `lem board`,
     and no task builds there: a lead and a builder are subagents of Lem's session. A copy that
     one writer replaced with an older read is written again at the watch's next start, which Lem
     makes after each end.
   - *Tests that hold the criteria*: the watch, started in the second repository with the
     `seen` it read, ends within 15 seconds after `away` in the first, with `away` true and that
     record's `ts`, and the second repository's `owner.js` then holds the record (5, and the board
     part of 7); started with a `seen` that is no longer the count, it ends at once; an `away` and
     a `back` written in the same second end it too. The board
     test gives the page an `owner.js` with an `away` record and an `events.js` with no `owner`
     event, and the header says "You are away since" (7), where headless Chrome runs.

3. **Lem's stages act on the mark.** Serves criteria 5 and 6 as Lem's session runs them. Files:
   `skills/lem/SKILL.md` (the row of `im-away`, `im-back`, the paragraph "The owner is needed at
   three points", and the paragraph on the watch under "Status"), `skills/lem/stages/away.md`,
   `skills/lem/stages/night.md` (step 3: "it runs without the owner until he says `/lem
   im-back`"), `skills/lem/stages/status.md` (the first line of the list), `skills/lem/stages/choice.md`
   where it names his away, `skills/lem/harness/claude-code.md` (`run-in-background`: one watch
   of the forge and one watch of the mark, each its own, with the stop of each),
   `skills/lem-ask-expert/SKILL.md` (where it names `lem project owner away`).
   - The mark is the machine's: his `/lem im-away` and `/lem im-back` in any repository hold in
     every repository on this machine, and a repository has no status of its own.
   - Lem's session keeps one watch of the mark in the background, from its start, never two:
     before it starts one, it reads `owner.seen` of `lem project waiting` and passes it as
     `--seen`. Its end wakes Lem. An end with `away`: Lem takes steps 2 to 5 of "Away" in
     `stages/away.md`, as if he had typed it here, after `lem decisions away` for this repository
     in place of step 1, with the words of the mark for what the record needs. An end with
     `back`: the lines of "Back". Then it starts the watch again with the new `seen`. The steps
     act on what waits now, so an end for a status that this session wrote itself does no harm:
     what was settled waits no more.
   - A session that starts while the mark says away takes the same steps once.
   - The session that `/lem night` started keeps no watch of the mark and takes no steps of
     `stages/away.md` on it: every task it opens runs without him whatever the mark says
     (`directions.md`), and a task of the day is the day session's to act on. So two Lem
     sessions of one repository never both act on one change of the mark.
   - `stages/away.md` step 2 takes a task `held` with the line `the criteria wait for the owner`
     and nothing after it. A task whose line is `the criteria wait for the owner: the small
     change is a full change` goes on with an interview (`stages/new.md`, "When it stops"), so
     while he is away it takes step 3, the interview without him: its `criteria.md` says
     `Size: small`, which `criteria.py approve --alone` refuses. This step of `away.md` already
     reads every task `held` this way today; the watch only runs it more often.
   - A night's task runs without him until it ends, and his `back` does not change it.
   - A stage file has no test (AGENTS.md, "Checks"); the commit names this task.

4. **The documents.** Serves no criterion. The change makes these false:
   - `docs/when-lem-needs-you.md`, "Away": the status holds in every repository on the Mac, and a
     night's task runs without him whatever his status (STE, as every guide).
   - `docs/install.md`: "What Lem keeps" names the one file Lem keeps outside the repository,
     `~/.config/lem/owner.jsonl` (or under `$XDG_CONFIG_HOME/lem`), and the removal steps delete
     that folder when no other repository uses Lem.
   - `README.md`, the row of `/lem im-away`, `/lem im-back`, and its line on away near line 107,
     when they say or imply one repository.
   - `AGENTS.md`, "Layout": `lem_state.py` names the machine's mark beside the state folder;
     `project.py`'s list says the owner's status is read from the mark; the board reads
     `owner.js`. And "The owner's rulings": the sentence "So his being there is one status of the
     repository" under "He says whether he is there" says the machine, and a new entry of
     2026-11-19 quotes his three answers of the interview word for word (`directions.md` of the
     task directory): the one mark, the night that always runs without him, and `~/.config/lem`.
     It says that each repository's Lem still runs only its own tasks and reads one more fact,
     which is how this change keeps "One Lem for one repository".
   - `docs/flow.md` line 51 and `docs/pull-request.md` line 14, when the wording no longer holds.

## Plan talk

Who argued the plan: the reviewer, Codex, `GPT 6.2 Sol high` as its pane's status line showed
it; the defender, Claude, Opus 5.5 at high effort (the `defender:` line of the task's state). Two
families. 7 turns over the bound of 38 for its 9 questions: the request, the list, two answers of
each side, and the close. The messages are `talk-01.md` to `talk-03.md` in the task directory.

The list, numbered as the reviewer gave it:

1. **A mode read before a long wait acts after the owner's status changed** (`land.py`
   `cmd_land` and `may_merge`, `criteria.py` `cmd_approve`). Repaired: task 1, "The readers act
   on the mode as it is at the act". The reviewer closed the approval half and held the merge half
   twice: `Task.fetch` (`git fetch origin BASE`, no timeout) runs after `may_merge` and before
   `gh pr merge`. **A design choice**: the plan's position, a re-read after the forge's answer and
   before the fetch, since any read leaves a window up to the merge call and the same window
   exists today through a lead's session (`prompts/lead.md` step 5); against the re-read after the
   fetch, right before `gh pr merge`, where the permission is settled at the last local step.
   Step 5 of `stages/plan.md` takes it; its result is below.
2. **Two sessions with different `XDG_CONFIG_HOME` read two marks** (task 1, the place).
   Refuted twice: criterion 3, approved word for word, names the variable; a session started
   with another value moves git's and gh's settings too; AGENTS.md "Lem is a companion, not a
   gate", (4). The reviewer held twice: criteria 1 and 2 promise that every repository follows one
   command, and both paths can work as written while the repositories disagree. **A design
   choice**: the plan as written, against a shared configuration path as a stated condition of
   the promise, which changes no code and may change a criterion. Step 5 of `stages/plan.md`
   takes it; its result is below.
3. **A suite run alone writes the real mark** (`tests/test-board.sh` line 1489,
   `tests/test-ask-expert.sh` line 68, neither sources `lib.sh`). Repaired: every file of `tests/`
   that makes a `WORK` of its own exports `XDG_CONFIG_HOME` under it. Settled by the two, not
   checked by the review.
4. **What wakes an idle Lem in criterion 5** (the watch's end). Refuted: the Bash tool's
   `run_in_background` re-invokes the session on exit, the reviewer found that contract in the
   Claude Code 2.1.328 binary, and `lem land watch` relies on it already; the idle two-repository
   case stays under "Not verified". Settled by the two, not checked by the review.
5. **The watch's cursor is a whole-second `ts`**: an away and a back in one second share it.
   Repaired at the cause: the cursor is the count of the mark's records (`owner.seen`, `--seen
   N`), a restart passes the count the watch returned. The reviewer held once on the restart and
   closed it on the plan's text. Settled by the two, not checked by the review.
6. **Two Lem sessions of one repository both act on one change** (the night's session; a fast
   task that grew sent to `approve --alone`). Repaired: the night's session keeps no watch, and
   `stages/away.md` step 2 takes only the plain line `the criteria wait for the owner`. The
   reviewer held once on a scheduled retro session and closed it on SKILL.md's "Two levels": the
   watch and the start rule are the owner's Lem session's only. Settled by the two, not checked by
   the review.
7. **The copy of old events merges two repositories' histories**. Repaired with a count: only
   this repository's log holds `owner` events (2; 0 in mybaze and in lem-scratch, counted by both
   sides). The reviewer held once on the fallback and closed it "for the current cutover". Settled
   by the two, not checked by the review.
8. **A stale `owner.js` on a board** (three writers, and a board with no Lem session). Repaired:
   task 2 names the board criterion 7 covers, a board of a repository where Lem's session runs. The
   reviewer held once on a write by `board.py` `prepare` after the watch's restart and closed it as
   not realistic. Settled by the two, not checked by the review.
9. **The span of an ended task** (`read_tasks`, the cut at the newest event). Refuted: no reader
   acts on an ended task's mode or spans; `land.py` `without_owner` is read only while the task is
   landing. Settled by the two, not checked by the review.

Mechanisms a repair added:

- The re-read of the mode at the act (question 1): it sits on the decision "every script reads
  the mark directly", and follows existing code, `decisions.py` `Task.add`, which reads the mode
  again under its lock. The reviewer: a layer over that decision. It stays.
- The count of records as the watch's cursor (question 5): it changed the decision that the watch
  compares the newest `ts`. The reviewer: at the cause.

Raised after the first turn and not argued: none. Additions refused as unpriced: none.

What changed in the plan, by question and by task: task 1, the files `criteria.py`, `land.py`,
`tests/test-board.sh`, `tests/test-ask-expert.sh`, the bullet on the re-read (1), the export in
each file with its own `WORK` (3), and `seen` in `owner` of `waiting` (5); task 2, the cursor and
its test (5) and the board criterion 7 covers (8); task 3, `seen` in place of `since` (5), the
night's session and step 2 of `away.md` (6); "Left to Lem before the merge", the count (7).

The two design choices after the talk, by the ladder of `stages/ladder.md`; the question gate
settled both, and no card went to the owner (`lem decisions list away-for-the-whole-machine`):

- Question 1, decision 3: the gate's judge answered "cheap". Both options move one re-read a few
  lines in `cmd_land` at the same cost, `branch.land` is "owner" in this repository, and the window
  between them is one `git fetch`. The plan's position stands: the re-read after the forge's
  answer, before `may_merge`. The judge noted that the re-read after `Task.fetch` fits "Lem owns
  each merge" at the same cost; that is the decision's undo.
- Question 2, decision 4: the gate's judge answered "cheap". A change of criterion 3 is out, since
  the owner approved it with the variable in it; AGENTS.md "Lem is a companion, not a gate", (4),
  caps the case at one sentence, and task 4 already names `$XDG_CONFIG_HOME/lem` in
  `docs/install.md`. The plan stands as written. The judge leaned to one more sentence in a guide;
  that is the decision's undo.

## Decisions of the plan

The lead of the build logs each with `lem decisions log --by lead`, as the plan talk leaves it, so
that the record holds no decision the talk reversed.

- **The mark is a log of each away and back, not a file of the status now.** Criterion 7 asks
  another repository for the span from 14:05 to 16:30 after he is back, and only the times of both
  records give it. One line for each status he says; nothing removes old lines (a few lines a
  day: an unmeasured estimate). Undo: keep the newest line only, and lose the spans of the other
  repositories.
- **Every script reads the mark directly, and no repository keeps a copy in its log.** A copy
  written later would carry two sources of one fact and a wrong order when a repository's Lem was
  not running. The board's `owner.js` is a copy for the page only, rewritten whole from the mark,
  because a page reads only files beside it. Undo: a copy in each log, written by the watch.
- **Lem's session in each repository keeps one watch of the mark.** Criterion 5 needs an idle Lem
  in another repository to act, and nothing else wakes it: a lead that stops wakes it, the forge's
  watch runs only while a pull request is open, and the mark cannot name the sessions of other
  repositories without a list of them, which "One Lem for one repository" leaves out. Its cost on
  a small task: one background command that reads one small file every 5 seconds, and no wake
  while the mark does not change. Undo: remove the command and the stage text; criterion 5 then
  holds only at the next turn of that Lem.
- **The tests keep away from the home directory through `XDG_CONFIG_HOME`.** Criterion 3 names
  that variable already, so the tests need no other way in. Undo: a variable of Lem's own for the
  tests, a third place the criteria do not name.
- **A `back` while he is there writes nothing.** Before, it ended a night's span; criterion 6 takes
  that away, so it changes nothing.
- **No lock on the mark.** Two repositories that write at the same second each append one short
  line with `O_APPEND`; the newest line still gives the status, and `runs_without_owner` already
  takes the first `away` of a run of them. A lock would be a second file in the home folder, which
  criterion 8 keeps to one.

## Left to Lem before the merge

The `owner` events that the event logs of the repositories that use Lem hold today (this
repository's: an `away` with the words "dnd" at 10:06:08Z and a `back` at 12:20:23Z on
2026-11-19, `lem project tasks`) are no longer read after the merge. A task that ran without him
in one of those spans and has not landed (`status-boards-steady-look`, building) would then show
no such span in its pull request. The maintaining session copies those events into the mark, in
the order of their `ts`, before the merge, by hand, as AGENTS.md has it for a change of a record's
form. On 2026-11-19, before 14:21 UTC, only this repository's log held `owner` events: 2 in
`lem/.lem/state/events.jsonl`, 0 in `mybaze` and 0 in `sandbox/lem-scratch` (`grep -c '"event":
"owner"'` on each log). So the copy is those two lines, and no two histories are merged. The
session counts again before the merge; when another log holds `owner` events by then, it copies
only the log of the repository whose open task needs its spans, and says in the pull request
which spans the other repositories' open tasks lose.

## Not verified

- Lem's session in a second repository acting on the watch's end (criterion 5 as a whole): it is
  Lem's stage text, and only a real run with two repositories open shows it.
- A board in a second repository that is open while the mark changes: the test loads the page
  with a written `owner.js`, not with the watch writing it under a running board.
- The watch from Lem's own session under Claude Code: the line is the same as `lem land watch`'s,
  whose end wakes the session that started it (the harness file).
