# A companion only when something waits for the owner

careful: yes, because the change moves where the owner's yes to the criteria and his answer to a choice are typed, which reaches "A task's record is lost or wrong" (the approval is written in a companion and must reach Lem's records) and "A decision that is the owner's is taken without him" (a companion that closes, a message that is lost or an away status must never let anyone take his yes for him); task 6 writes new rulings of his into `AGENTS.md`, which reaches "A change bends a ruling of the owner".

## Acceptance criteria

Size: full, because the change moves where the owner answers Lem, adds a session kind, a message from a companion to Lem and the board's way to a companion, and records his rulings.

1. Two standard-track asks typed one after the other in Lem's session have two interviews open at the same time, each in a companion of Lem's session: the owner types `/lem the export holds the gift note` and then `/lem the report dates stay whole`; the sidebar shows `gift-note-in-export · interview` and `report-dates-stay-whole · interview` under Lem's session, and Lem answers his next message at once. When a companion opens, Lem says one line in its session that names it as the sidebar shows it ("the interview of gift-note-in-export is open in `gift-note-in-export · interview` under this session"), and a new companion never takes the keyboard focus.
2. An interview's companion is a fresh agent, not a fork of Lem's conversation: it reads the ask, the task's file, the turns of the talk in Lem's session that led to the ask, copied word for word into the task directory, and the scout's report; it knows no other task. Lem copies every turn of its talk about this ask, from the turn where the topic began; the companion first says what it got (the ask and the copied turns); the copy stays in Lem's state folder and never reaches git or a pull request.
3. His yes in the companion is his approval, and Lem starts the lead with no message from him: he approves the criteria of `gift-note-in-export` in its companion; `lem criteria approved gift-note-in-export` shows his approval; the companion tells Lem and closes, Lem's session says one line "the build of gift-note-in-export started", and the board shows the lead building. When the companion's message is lost, Lem starts the lead at its next turn from the task's files, and meanwhile the board shows the task as approved with no lead.
4. A choice of a lead that waits for him opens a companion with its card already shown, and he can discuss it there: choice 2 of `gift-note-in-export` opens `gift-note-in-export · choice 2`; he asks there "what do the experts say?" and gets the answer from the choice's record; his answer is written to the record, the lead goes on with it, and the companion closes. Two choices of two tasks are two companions open at the same time. A companion that opens never takes the keyboard focus, and the card names the experts in a few words, from the settings' experts.
5. A card he closes with no answer leaves the choice in the list of what waits, and nobody takes it while he is there. The way to open it again is a row of the board's "Waits for you" or `/lem` in Lem's session, and the card shows that way before it is closed.
6. Criteria that wait only for his yes open a companion too: a ticket a teammate wrote, read by the personas, opens `SLUG · criteria` with the criteria and the personas' read; his yes there approves them. The pull request says that the criteria waited for the owner's yes and when he gave it.
7. The board leads him to what waits: each row of "Waits for you" opens the companion that waits for him, and the board shows each open companion with its task. The row of a choice whose companion was closed opens a new companion for it.
8. A companion does its one need and nothing else: it takes no ask, starts no lead, lands nothing and watches no pull request. A companion that gets an ask gives the exact line to paste into Lem's session, with that session named as the sidebar shows it.
9. A fast-track ask, a green pull request and the retro's proposals open no companion. While he is away no companion opens, since the ladder takes every choice and `--alone` approves held criteria; a step that a later "no" cannot reverse still waits for him, and at `/lem im-back` one companion opens for each such step.
10. `AGENTS.md` holds his rulings of 2026-11-19 in his words: one Lem session for each repository and no global Lem; a companion only when something waits for him, which closes when he answered; a fresh companion with the talk copied in; a companion tells Lem with an agterm pane message. After his quoted words, one sentence marked as the session's design says that a companion runs only on the owner's machine and asks nothing of a teammate, and that the copied talk stays in Lem's untracked state folder and never reaches git or a pull request.

## What is there today

Read in the code at `28d3c81`:

- The interview runs in Lem's own session: `skills/lem/stages/new.md` step 4 sends a standard-track
  ask with an interview to `skills/lem/stages/interview.md`, whose steps 1 to 7 (the scout, the
  questions, `directions.md`, the criteria, the personas' read, his yes, `lem criteria approve`)
  are Lem's, and step 6 of `new.md` then writes the brief and `stages/start.md` starts the lead from
  the same session. Its first state is `held` with `the interview waits for the owner`.
- A companion exists for the plan talk only: `skills/lem/harness/claude-code.md`,
  `## open-task-session` ("Lem opens one for a plan talk only"), with the launch line
  `agtermctl session new --parent ... --cwd WORKTREE --name SLUG --no-select --command ...`, the
  state lines `lead: session`, `session: ID` and `defender: MODEL, EFFORT`, and its close in
  `stages/stopped.md` (`planned`) and `stages/correct.md`. No script opens a session: the stage
  text and the harness give the line.
- A card of a choice is opened by Lem in its own session through `ask-owner` (`lem-ask`), which
  waits in the foreground up to 570 s (`skills/lem-ask/SKILL.md`, "Waiting") and exits 5 `busy`
  when the session already shows an overlay: one card at a time per session.
- `lem project waiting` (`cmd_waiting` in `skills/lem/scripts/project.py`) lists `choices` (from
  `lem decisions pending`), `criteria` (a `held` task whose line starts with
  `the criteria wait for the owner`, `CRITERIA_WAIT`), `held` (every other `held` task, the
  interview among them), `pull_requests` and `retros`. Nothing there knows a session.
- `lem project may-start` refuses a `queued` task only while its `after:` task has not ended
  (`cmd_may_start`); a `queued` task with no `after:` line starts at the next look at the queue
  (`stages/start.md`, "The queue").
- `land.py` `read_skipped` (`READ_SKIP`) ends the interview at the first state line that starts
  with `lead:`; `board.html` reads `lead:` and `session:` lines into `t.lead` and `t.session`
  (around its line 917) and jumps to a session with `paneOf(id)` and `jump(target, label)`; its
  backlog tab types a `/lem` line into Lem's session (`itemActions`).
- The pull request's line of the read and the approval is `read_line` in `land.py`: "...; the
  owner approved them on DATE". Nothing says that the criteria waited for his yes.
- `stages/away.md` step 3 runs an open interview without him and approves with `--alone`;
  `lem project owner away` takes every choice that is no irreversible step (`lem decisions away`).
- The interview of this task already settled three questions without him (decisions 1 to 3 in
  `lem decisions list interview-in-a-companion`): which needs open a companion, that a companion's
  persona read runs on one model family, and that no companion opens while he is away.

## Tasks

1. **`lem companion`: one script opens, names, lists and closes the companion of one need, and
   says what is due.** Serves criteria 1, 2, 3, 4, 5, 6 and 9. Files: new
   `skills/lem/scripts/companion.py`, `bin/lem` (its `COMMANDS`), new `tests/unit/test_companion.py`,
   new `tests/lem-companion.sh` (a block with a stand-in for `agtermctl`, as `tests/lem-picker.sh`
   has), `tests/pick.py` (the map), `tests/test-lem.sh` only if a new block must be named there.
   - *A need* is one of three, and each has one fixed name in the sidebar: `interview`
     (`SLUG · interview`), `criteria` (`SLUG · criteria`) and `choice N` (`SLUG · choice N`).
   - `lem companion open SLUG --need interview|criteria|choice --choice N`: refuses with exit 1
     and the fix for a task on the fast track (`track` `fast`), a task that ended, a need that
     does not wait (no `held` with `the interview waits for the owner` for `interview`, no
     `CRITERIA_WAIT` line for `criteria`, no choice N that `waits` for `choice`), an `interview`
     with no `talk.md` in the task directory (the copied turns, criterion 2), and any need while
     the owner is away except a choice that is `irreversible` (criterion 9). A need whose
     companion still runs in agterm's tree is not opened twice: the command prints that one. It
     writes `companion-NEED.md` into the task directory (the brief: `Read SKILL_DIR/prompts/companion.md
     and follow it.`, the task, the need, the task directory, the main checkout, `coordinator:`
     and `socket:` with Lem's address, and `lem session:` with Lem's session's name as the
     sidebar shows it, read from `agtermctl tree --json`), then opens the session under Lem's
     (`--parent`, the same parent rule as `board.py`'s `show`: a companion's companion is its
     sibling), with `--no-select`, `--cwd` the main checkout, the name above, and the command
     `LOGIN_SHELL -l -c 'claude "Read BRIEF and follow it."'` with no model flag. It logs
     `companion.open` with `task`, `need`, `session` and `name`, and prints `say`: "the
     interview of SLUG is open in `SLUG · interview` under this session" (for a choice, "choice N
     of SLUG is open in ..."; for criteria, "the criteria of SLUG are open in ...").
   - `lem companion close SLUG --need ...`: closes the session when it runs and logs
     `companion.close` with why (`answered`, `gone`, `dropped`); it exits 0 when nothing runs.
   - `lem companion list`: each companion that `companion.open` names and agterm's tree still has,
     with its task, need and name. The board reads the same events.
   - `lem companion due`: nothing opens or starts here, it says what Lem owes, from the files:
     `open`, each need that waits for the owner and has no live companion (with him there; while
     he is away only the irreversible choices; so after `/lem im-back` one entry for each such step
     and for each other need); `start`, each task `queued` with the line
     `the criteria are approved: Lem starts its lead` (criterion 3's recovery, also when the
     companion's message was lost); `close`, each live companion whose need no longer waits.
   - The rules that take facts (which need waits, `due` from a list of tasks, events and live
     sessions, the names, the refusals) are functions with unit cases; the block runs `open`,
     `list`, `close` and `due` against the stand-in and checks the `agtermctl` arguments it got
     (`--no-select`, `--parent`, the name), two companions of two tasks open at once, and that
     `talk.md` and `companion-*.md` are in the state folder that git ignores
     (`git check-ignore`). Run `python3 -B -m unittest discover -s tests/unit` and
     `bash tests/lem-companion.sh`.

2. **The companion's agent: one need, the task's files, and its end.** Serves criteria 2, 3, 4, 5,
   6 and 8. Files: new `skills/lem/prompts/companion.md`, `skills/lem/harness/claude-code.md`
   (`## open-task-session` for a need's companion beside the plan talk's; `## tell-coordinator`
   from a need's companion; `## ask-owner`: a card in a companion), `skills/lem/harness/README.md`
   (the capability names a need's companion), `skills/lem/stages/interview.md` (its actor is the
   companion: who runs each step, the read on one model family, the end of step 7).
   - The brief opens with what the companion is for, and that it knows one task: it reads
     `task.md`, `ask.txt`, `talk.md`, `directions.md` and `scout.md` of its task directory and no
     other, and its first words to the owner say what it got: the ask and how many turns of the
     talk were copied, with the first one.
   - *interview*: it starts the scout and the interview as `stages/interview.md` step 1 says
     (the scout is its builder, and its reply comes to it), runs steps 2 to 7 there, and after his
     yes typed in it, `lem criteria approve SLUG --file FILE` (by `owner`); then it writes the
     brief of `stages/new.md` step 6 with Lem's address from its own brief, writes the state
     `queued` with the line `the criteria are approved: Lem starts its lead`, never a `lead:` line
     (`READ_SKIP` in `land.py` reads that line as the end of the interview), sends
     `lem: SLUG criteria approved` to Lem's pane (`tell-coordinator`), and closes itself with
     `lem companion close`.
   - *choice*: it shows the card through `ask-owner` in its own session, built as
     `stages/choice.md` step 1 says, with the experts named in a few words from the settings'
     `seats.experts` and one line on the card: "Close this card and the choice still waits: its
     row in the board's Waits for you, or /lem in `LEM SESSION NAME`, opens it again". It answers
     "what do the experts say?" from the choice's record (`advice`). His answer goes into the
     record with `lem decisions answer` as step 2 there says; then the line
     `lem: SLUG choice N answered`, and it closes itself. A card he closes with no answer leaves
     the choice as it is: the companion says the way back in one line and closes, and takes
     nothing.
   - *criteria*: it shows the criteria with the personas' read from the lead's `report.md` on one
     page, as `stages/interview.md` step 6 says; his yes there is `lem criteria approve --file`,
     then the same `queued` line, the message and the close as for the interview.
   - What it never does (criterion 8): take an ask, start a lead, land, watch a pull request. An
     ask typed there gets the exact line to paste, `/lem THE ASK AS TYPED`, and the name of Lem's
     session from `lem session:`.
   - His `/lem im-away` typed in a companion is his word as everywhere:
     `lem project owner away --words`, and the interview goes on without him as
     `stages/away.md` step 3 says, in the companion, which then ends as above with `--alone`.
   - No test: these are a brief and stage texts, whose test is the real task of this plan's last
     section; the script's refusals of task 1 hold what a script can.

3. **Lem opens a companion where it waited for the owner, and starts the lead after.** Serves
   criteria 1, 3, 4, 5, 6 and 9. Files: `skills/lem/SKILL.md` (the opening paragraph's three
   touches, "## Two levels" with the need's companion as a third kind of session, the
   Subcommands rows "a lead stopped" and "a choice waits" and a row for a companion's line, "What
   holds in every stage": the three points are answered in a companion, and at each turn
   `lem companion due`), `skills/lem/stages/new.md` (step 5's line for the standard track with an
   interview names the companion; step 4 and after step 5: Lem copies the turns of its talk about
   this ask, from the turn where the topic began, word for word into `talk.md`, runs
   `lem companion open SLUG --need interview`, says its `say`, and goes back to the owner's next
   message), `skills/lem/stages/choice.md` (a choice opens its companion; Lem shows no card in its
   own session), `skills/lem/stages/stopped.md` (`held` with `the criteria wait for the owner`
   opens `--need criteria`; a companion's line is a wake-up and the fact is the files),
   `skills/lem/stages/start.md` ("The queue": a task `queued` with
   `the criteria are approved: Lem starts its lead` gets its lead, and Lem says "the build of SLUG
   started"), `skills/lem/stages/status.md` (bare `/lem` opens a companion for each `open` of
   `due`; `/lem status SLUG` opens the one of that task), `skills/lem/stages/away.md` (away: no
   companion opens, and each open one gets one message that he is away; back: `due` opens one for
   each irreversible step and each other need), `skills/lem/stages/investigate.md` (a full fix's
   interview opens its companion too), `skills/lem/stages/correct.md` (a drop closes the task's
   companions).
   - A fast-track ask, a green pull request and the retro's proposals open no companion
     (criterion 9): `new.md` "The fast track" and `status.md` say so where they act.
   - No test: stage texts; task 1's `due` and refusals hold the rules a script can.

4. **The board leads to what waits.** Serves criteria 3 and 7. Files:
   `skills/lem/assets/board.html`, `skills/lem/scripts/board.py` only if the page needs a field
   the event log does not give, `tests/test-board.sh`.
   - Each row of "Waits for you" (the banners, the large card and a task's own board) whose need
     has a live companion has a jump to it, by the `session` of its newest `companion.open` that
     no `companion.close` followed and that `paneOf` finds. A row whose companion is gone types
     `/lem status SLUG` into Lem's session, the way the backlog tab's action types its line, with
     the same confirm and the same fallback text when no agent runs there (criterion 7).
   - Each task card shows its open companion by its name (`SLUG · interview`) with that jump.
   - A task `queued` with `the criteria are approved: Lem starts its lead` shows as approved with
     no lead (criterion 3), in Lem's lane.
   - Test in `tests/test-board.sh` over a fixture with a live and a closed companion: the rows,
     the jump target and the typed line. Run `bash tests/test-board.sh`.

5. **The pull request says that the criteria waited for the owner's yes, and when he gave it.**
   Serves criterion 6. Files: `skills/lem/scripts/land.py` (`read_line` and what it is given),
   `tests/unit/test_land_text.py` or `tests/unit/test_land.py`.
   - When the task's state had `the criteria wait for the owner` before his approval (a request
     somebody else wrote, or criteria a persona doubted), the line ends "the criteria waited for
     the owner's yes, which he gave on DATE at HH:MM UTC" in place of "the owner approved them on
     DATE". Unit cases on the function for both cases and for an approval with no such wait.
     Run `python3 -B -m unittest discover -s tests/unit`.

6. **The documents: his rulings and the guides.** Serves criterion 10. Files: `AGENTS.md` (his
   rulings of 2026-11-19 in his words, from `directions.md` and `ask.txt` of this task, each with
   its date, and after them one sentence marked as the session's design: a companion runs only on
   the owner's machine and asks nothing of a teammate, and the copied talk stays in Lem's
   untracked state folder and never reaches git or a pull request; the ruling on the plan talk's
   companion and "Lem asks through its question page" say where a card now opens; "## Layout"
   names `companion.py`, `prompts/companion.md` and the new block; "## Checks" lists the block),
   `docs/when-lem-needs-you.md` (where he answers now: a companion under Lem's session, the board's
   rows), `docs/flow.md` (the interview in its companion; its diagram's labels in double quotes),
   `README.md` where it says that the interview is in Lem's session (STE).
   - No test: the sentences of documents.

## Decisions of the plan

Each is logged with `--by lead` in `lem decisions list interview-in-a-companion`.

- A script opens the companion (task 1), where the plan talk's companion is a line in the
  harness file: the name in the sidebar, no focus, one companion for each need, the refusal while
  he is away and the record for the board must hold the same way each time, and only a script can
  be tested for that. It assumes that `agtermctl` belongs in a script as it does in `board.py`.
- Lem writes the copy of its talk itself, from its own context, into `talk.md`; no script reads
  Claude Code's own transcript, whose format is the harness's and not Lem's. It assumes that an
  agent copies turns of its own context word for word; the companion's first words show what it
  got, so a short copy is seen at once (criterion 2).
- After his yes the companion writes the state `queued` with
  `the criteria are approved: Lem starts its lead`, and Lem's queue starts the lead. `queued`
  with no `after:` line already starts at the next look at the queue (`cmd_may_start`), so no new
  status is needed, and no `lead:` line is written before a lead runs (`READ_SKIP`).
- The companion runs on the owner's default Claude: no seat and no model flag, since no setting
  names one and a new key is the owner's.
- The companion starts in the main checkout and edits no tracked file; it writes only through
  `lem` (the criteria, the decisions, the state, `directions.md` and `task.md` in the task
  directory).
- A row of the board whose companion is gone types `/lem status SLUG`, and bare `/lem` opens one
  for each need that is due: no new command of his.
- The scout of an interview is the companion's builder, so its reply comes to the companion and
  not to Lem.
- At `/lem im-away` an open companion gets one agterm message; an interview goes on there without
  him, and a card's companion closes, since `lem project owner away` took its choice.

## What this plan does not verify

- That an agterm message from a need's companion wakes an idle Lem: it did from the plan talk's
  companion (agterm 0.41.1, 2026-11-14 to 16, `harness/claude-code.md`); `due` at each of Lem's
  turns covers a lost one.
- That `--no-select` keeps the keyboard focus in Lem's session, and that a companion can close
  its own session as its last act: neither ran in Lem. The real run of the plan's end shows both.
- The whole path in a real run: two asks in Lem's session, two interviews at once, a yes in each,
  a choice in a companion. No test of a script holds it; it is the stage files' test, after the
  merge.
