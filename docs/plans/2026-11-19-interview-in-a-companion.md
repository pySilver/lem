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
   has), `tests/pick.py` (the map), and the block's name in both arrays that name the blocks,
   `suites` in `tests/all.sh` and `blocks` in `tests/test-lem.sh`, as `lem-picker` is named there
   (Q11).
   - *A need* is one of three, and each has one fixed name in the sidebar: `interview`
     (`SLUG · interview`), `criteria` (`SLUG · criteria`) and `choice N` (`SLUG · choice N`).
   - *Which need waits*, from the task's newest state block, one rule for `open`, `due`, the board
     and the pull request: `held` with `the interview waits for the owner`, and `held` with
     `the criteria wait for the owner: the small change is a full change` (`FAST_GREW`, the fast
     track's builder found a full change, `stages/new.md` "The fast track" step 3), are an
     `interview` (Q7); `held` with any other `CRITERIA_WAIT` line is `criteria`; `held` with
     `choice N waits for the owner`, and every choice N that `lem decisions pending` lists as
     waiting, is `choice N`. A wait is *answered* when the record holds his word after the state
     block that opened it: a `criteria.approved` event by `owner` or `alone` after that block for
     an interview or criteria, or choice N no longer `waits` in `lem decisions list` for a
     choice. An answered wait opens nothing.
   - `lem companion talk SLUG --from TEXT` writes `talk.md` (Q4): the turns of Lem's own Claude
     Code session, word for word, from the owner's turn whose text starts with TEXT to the
     newest turn, each with who said it (the owner or Lem) and only the text blocks (no tool
     call, no tool output). It reads the session's transcript, the file
     `~/.claude/projects/*/ID.jsonl` with `ID` from `CLAUDE_CODE_SESSION_ID`, which Claude Code
     gives the Bash tool, as `corrections.py` `last_agent_text` reads the transcript a hook is
     given. The transcript keeps the turns from before a compaction (one of this project's
     transcripts holds 495 owner records before its first `compact_boundary`, read 2026-11-19),
     so a copy is word for word also after one. It refuses with exit 1 and the fix when the
     variable is not set, the file is not there, or no owner turn starts with TEXT. The format
     is the harness's: `harness/claude-code.md` names the file and the variable, and the script
     keeps the read in one function that names the harness.
   - `lem companion open SLUG --need interview|criteria|choice --choice N`: refuses with exit 1
     and the fix for a task on the fast track (`track` `fast`), a task that ended, a need that
     does not wait or whose wait is answered (the rule above), an `interview` with no `talk.md`
     in the task directory (the copied turns, criterion 2), any need while the owner is away
     (his status, `lem project waiting`'s `owner`; criterion 9), and, with him there, any need of
     a task whose `mode` is `alone` except a choice that is `irreversible`: a night's task runs
     without him while he is there (`stages/night.md` step 3), and its criteria and its other
     choices are taken without him as today (Q3). A need whose
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
     `companion.close` with why (`answered`, `dismissed`, `gone`, `dropped`); it exits 0 when
     nothing runs. `dismissed` is a card he closed with no answer (Q8).
   - `lem companion list`: each companion that `companion.open` names and agterm's tree still has,
     with its task, need and name. The board reads the same events.
   - `lem companion due`: nothing opens or starts here, it says what Lem owes, from the files:
     `open`, each need that waits for the owner, is not answered, has no live companion and
     would not be refused by `open`, and whose newest `companion.close` is not `dismissed`
     (criterion 5: nobody opens a card he closed until he asks; Q8); so nothing while he is
     away, and after `/lem im-back` one entry for each need, irreversible steps among them
     (criterion 9); `start`, each task whose wait is answered and that has no `lead:` state
     block after the answer: his yes to the criteria (an interview or criteria), or his answer
     to the choice a lead stopped `held` for (`stages/build.md` step 4, `choice N waits for the
     owner`; Q5). This is criterion 3's recovery from the record itself, the approval and the
     answer as the scripts wrote them, so a companion that stops after `lem criteria approve`
     and before anything else, or a lost message, still gives the start (Q1); `close`, each
     live companion whose need no longer waits or is answered.
   - `lem companion open` with `--asked`, which bare `/lem`, `/lem status SLUG` and a board row
     pass (his word), opens a need whose newest close was `dismissed`; without it, `open`
     refuses such a need with the line that names the way back (Q8).
   - The rules that take facts (which need waits, `due` from a list of tasks, events and live
     sessions, the names, the refusals) are functions with unit cases; the block runs `open`,
     `list`, `close` and `due` against the stand-in and checks the `agtermctl` arguments it got
     (`--no-select`, `--parent`, the name), two companions of two tasks open at once, and that
     `talk.md` and `companion-*.md` are in the state folder that git ignores
     (`git check-ignore`). Unit cases for `due`: an approval with the `held` block still newest
     gives `start` and no `open`; a choice a lead stopped for, answered, gives `start`; a
     dismissed card gives no `open`, and `--asked` opens it; a night's task with him there opens
     only its irreversible choice; `FAST_GREW` is an `interview`. `talk` over a fixture
     transcript with a `compact_boundary` copies the turns from before it. Run
     `python3 -B -m unittest discover -s tests/unit` and `bash tests/lem-companion.sh`.

2. **The companion's agent: one need, the task's files, and its end.** Serves criteria 2, 3, 4, 5,
   6 and 8. Files: new `skills/lem/prompts/companion.md`, `skills/lem/harness/claude-code.md`
   (`## open-task-session` for a need's companion beside the plan talk's; `## tell-coordinator`
   from a need's companion; `## ask-owner`: a card in a companion), `skills/lem/harness/README.md`
   (the capability names a need's companion), `skills/lem/stages/interview.md` (its actor is the
   companion: who runs each step, the read on one model family, the end of step 7).
   - The brief opens with what the companion is for, and that it knows one task: it reads
     `task.md`, `ask.txt`, `talk.md`, `directions.md`, `scout.md` (for a `FAST_GREW` interview the
     builder's `report.md` stands in for it, as `stages/new.md` "The fast track" step 3 says; Q7),
     `criteria.md` and `criteria-read.md` of its task directory and no other task's, and its
     first words to the owner say what it got: the ask and how many turns of the talk were
     copied, with the first one. A turn of the copy that also speaks of another task is copied
     whole, since criterion 2 asks for every turn about this ask; the brief says that the
     companion acts on its own task only and treats the rest of such a turn as context.
   - *A fresh companion goes on from the files* (Q6): it asks nothing that `directions.md`
     already holds, and when `criteria.md` and `criteria-read.md` are there it goes on from step 6
     of `stages/interview.md`. So the companion writes each direction into `directions.md` as he
     names it, not after the last question (step 3 there), and the personas' answers of step 5,
     each persona and family with its words, into `criteria-read.md` beside the `criteria.read`
     event, as a lead puts them into its `report.md` today. When he leaves with no words of
     away, the companion's page waits and the state stays `held` with `the interview waits for the
     owner`: in a companion the line `the criteria wait for the owner` of `stages/interview.md`'s
     last paragraph is not written, since the need is still the interview and a closed companion
     opens again from the files above.
   - *interview*: it starts the scout and the interview as `stages/interview.md` step 1 says
     (the scout is its builder, and its reply comes to it), runs steps 2 to 7 there, and after his
     yes typed in it, `lem criteria approve SLUG --file FILE` (by `owner`). That record is the
     whole handoff (Q1, Q2): it writes no brief and no `lead:` line (`READ_SKIP` in `land.py`
     reads that line as the end of the interview). Then the state `queued` with the line
     `the criteria are approved: Lem starts its lead`, which is for the board and the status and
     which no start reads, `lem: SLUG criteria approved` to Lem's pane (`tell-coordinator`), and
     `lem companion close --why answered`. A stop after the approval and before the close loses
     nothing: `due` gives the start from the approval.
   - *choice*: it shows the card through `ask-owner` in its own session, built as
     `stages/choice.md` step 1 says, with the experts named in a few words from the settings'
     `seats.experts` and one line on the card: "Close this card and the choice still waits: its
     row in the board's Waits for you, or /lem in `LEM SESSION NAME`, opens it again". It answers
     "what do the experts say?" from the choice's record (Q9): the experts' level of `said`, which
     the ladder writes there (`stages/build.md` step 2, `decisions.py` `ask`), and `advice` when
     the record holds it. When neither holds an answer of the experts, it says that the ladder
     settled before the experts' level, and his "ask them" runs `lem experts brief SLUG N` and
     `record SLUG N`, which keep their advice on his card (`stages/ladder.md`, "All opinions").
     His answer goes into the record with `lem decisions answer` as step 2 there says; then the
     line `lem: SLUG choice N answered`, and `lem companion close --why answered`. A card he
     closes with no answer leaves the choice as it is: the companion says the way back in one
     line, closes with `--why dismissed`, and takes nothing.
   - *criteria*: it shows the criteria with the personas' read from the lead's `report.md` on one
     page, as `stages/interview.md` step 6 says; his yes there is `lem criteria approve --file`,
     then the same `queued` line, the message and the close as for the interview.
   - What it never does (criterion 8): take an ask, start a lead, land, watch a pull request. An
     ask typed there gets the exact line to paste, `/lem THE ASK AS TYPED`, and the name of Lem's
     session from `lem session:`.
   - His `/lem im-away` typed in a companion is his word as everywhere (Q3):
     `lem project owner away --words`, then the line `lem: the owner is away` to Lem's pane, so
     that Lem takes `stages/away.md` for every other task and every other open companion; its own
     interview goes on without him as `stages/away.md` step 3 says, in the companion, which then
     ends as above with `--alone`, and its own card closes, since `lem project owner away` took
     its choice. His `/lem im-back` there is the same with `back`.
   - No test: these are a brief and stage texts, whose test is the real task of this plan's last
     section; the script's refusals of task 1 hold what a script can.

3. **Lem opens a companion where it waited for the owner, and starts the lead after.** Serves
   criteria 1, 3, 4, 5, 6 and 9. Files: `skills/lem/SKILL.md` (the opening paragraph's three
   touches, "## Two levels" with the need's companion as a third kind of session, the
   Subcommands rows "a lead stopped" and "a choice waits" and a row for a companion's line, "What
   holds in every stage": the three points are answered in a companion, and at each turn
   `lem companion due`), `skills/lem/stages/new.md` (step 5's line for the standard track with an
   interview names the companion; after step 5: Lem writes the brief of step 6 now, before the
   companion opens, with every line it knows from the ask (`stop after the plan: yes` for
   `/lem plan <what>`, `request by: someone else`), so that `be-careful` during the interview
   writes its line into that brief as `stages/correct.md` says (Q2); then
   `lem companion talk SLUG --from "THE OWNER'S FIRST TURN ON THIS ASK"` with the start of the
   turn where the topic began, `lem companion open SLUG --need interview`, its `say`, and back to
   the owner's next message), `skills/lem/stages/choice.md` (a choice opens its companion; Lem
   shows no card in its own session), `skills/lem/stages/stopped.md` (`held` with a
   `CRITERIA_WAIT` line opens `--need criteria`, and with `FAST_GREW` `--need interview`; `held`
   with `choice N waits for the owner` starts its lead when `due` gives `start` for it (Q5); a
   companion's line is a wake-up and the fact is the files), `skills/lem/stages/start.md` ("The
   queue": each `start` of `lem companion due` gets its lead: for an approved interview or
   criteria, step 7 of "Open the task" from the ask in `task.md`, which may queue it `after:`
   another task, and step 8 with the brief already written (Q2); for an answered choice, a
   fresh lead as `stages/stopped.md` says; and Lem says "the build of SLUG started"),
   `skills/lem/stages/status.md` (bare `/lem` opens a companion with `--asked` for each need that
   waits, dismissed ones too; `/lem status SLUG` opens the one of that task, and
   `/lem status SLUG choice N` that choice's (Q8)), `skills/lem/stages/away.md` (away: no
   companion opens, and each open one gets one message that he is away; his words in a
   companion come as the line `lem: the owner is away` and take the same steps (Q3); back: `due`
   opens one for each irreversible step and each other need), `skills/lem/stages/investigate.md`
   (a full fix's interview opens its companion too), `skills/lem/stages/correct.md`
   (`standard-track`: the state `held` with `the interview waits for the owner`, then the
   interview's companion as after step 5 of `stages/new.md`, with the builder's report as the
   scout's when its builder ran (Q7); a drop closes the task's companions).
   - A fast-track ask, a green pull request and the retro's proposals open no companion
     (criterion 9): `new.md` "The fast track" and `status.md` say so where they act.
   - No test: stage texts; task 1's `due` and refusals hold the rules a script can.

4. **The board leads to what waits.** Serves criteria 3 and 7. Files:
   `skills/lem/assets/board.html`, `skills/lem/scripts/board.py` only if the page needs a field
   the event log does not give, `tests/test-board.sh`.
   - Each row of "Waits for you" (the banners, the large card and a task's own board) whose need
     has a live companion has a jump to it, by the `session` of its newest `companion.open` that
     no `companion.close` followed and that `paneOf` finds. A row whose companion is gone types
     `/lem status SLUG` into Lem's session, and the row of a choice `/lem status SLUG choice N`,
     so that of two choices of one task the row opens its own (Q8), the way the backlog tab's
     action types its line, with the same confirm and the same fallback text when no agent runs
     there (criterion 7).
   - Each task card shows its open companion by its name (`SLUG · interview`) with that jump.
   - A task whose wait is answered and that has no lead after the answer (task 1's rule: a
     `criteria.approved` event by `owner` or `alone` after its `held` block, whether or not the
     companion's `queued` line followed) shows as approved with no lead (criterion 3), in Lem's
     lane (Q1). The fixture holds both: an approval with `held` still newest, and with `queued`.
   - Test in `tests/test-board.sh` over a fixture with a live and a closed companion: the rows,
     the jump target and the typed line. Run `bash tests/test-board.sh`.

5. **The pull request says that the criteria waited for the owner's yes, and when he gave it.**
   Serves criterion 6. Files: `skills/lem/scripts/land.py` (`read_line` and what it is given),
   `tests/unit/test_land_text.py` or `tests/unit/test_land.py`.
   - The wait is the newest `held` state block with a `CRITERIA_WAIT` line other than
     `FAST_GREW` (a request somebody else wrote, or criteria a persona doubted; a `FAST_GREW` task
     went to an interview), and its end is the first `criteria.approved` by `owner` after that
     block (Q10). When there is such a pair, the line ends "the criteria waited for the owner's
     yes from DATE at HH:MM UTC, which he gave on DATE at HH:MM UTC", and a later approval of his
     adds "; he approved them again on DATE" in place of "the owner approved them on DATE". Unit
     cases on the function: a wait and its approval; a wait, its approval and a later approval
     with no wait, which names the first as the end; an approval with no such wait.
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

## Plan talk

Argued on 2026-11-19 in the task's companion. The reviewer: Codex, GPT 6.2 Sol at high effort,
as its pane's status line showed. The defender: Claude, Opus 5.5 at high effort, as the task's
`defender:` state line gives it. Seven turns, 11 questions. The repairs are commit `f2d9bd4`;
the record is the commit after it. Agreement carries no authority: the review before the pull
request reads each settled position as a claim.

The list, as the reviewer gave it:

1. **An approval recorded before the `queued` line is lost** (Task 2's order of writes; Task 1's
   `due.start` read only the `queued` line). Repaired at the cause: decision 16 changed, the
   approval or the answer on record is the whole handoff and `due.start` reads it. The reviewer:
   "holds, at the cause": (a) the companion's display `queued` can come after Lem's `building` or
   Lem's `queued` with `after:`, and `cmd_state` accepts it (`project.py:1529-1537` refuses only
   an ended state, `landing` and `open`); (b) after that `queued`, "the newest block" is not the
   `held` block the rule reads; (c) `cmd_approve` writes `criteria.json` before it logs
   `criteria.approved`, and the log can fail (a full disk) after the file is written. The
   defender refuted (c) as one call under one lock; the reviewer held it, since an append can
   fail alone. **A design choice**: the plan as it stands (the record is the handoff, with the
   companion's display `queued` and the rule on the newest block and the event), against the
   companion writing no state after the approval and the rule finding the newest `held` block
   with the approval after it, read from `criteria.json` as well as the event. `stages/plan.md`,
   step 5, takes it.
2. **The handoff drops `after:`, `stop after the plan` and the careful mark** (Task 2 wrote the
   brief; `cmd_may_start` reads `after:` only in the newest block). Repaired, at the cause (the
   same decision as question 1): Lem writes `brief.md` when it opens the task, before the
   companion, and takes steps 7 and 8 of "Open the task" after the answer. Closed. Settled by the
   two, not checked by the review.
3. **`/lem im-away` in one companion; irreversible cards while away; a night's task.** Repaired:
   the companion records his word and sends `lem: the owner is away`, Lem takes `stages/away.md`;
   `open` refuses every need while he is away and every need but an irreversible choice of a task
   whose `mode` is `alone`. The reviewer held it: a lost message leaves the other interviews and
   held criteria where they are, and a dismissed irreversible choice stays out of `due.open` at
   `/lem im-back`, against criterion 9. No refutation. **A design choice**: the plan as it stands,
   against Lem taking `stages/away.md` whenever the owner's status (`lem project waiting`'s
   `owner`) changed since its last turn, and `/lem im-back` opening each irreversible step with
   `--asked`.
4. **The verbatim copy after a compaction; a turn about two tasks** (decision 15: the copy from
   Lem's own context). Repaired at the cause: decision 15 changed, `lem companion talk` reads
   Lem's transcript, which keeps the turns from before a compaction (495 owner records before the
   first `compact_boundary` in one of this project's transcripts, read 2026-11-19). The reviewer:
   "holds, at the cause": the copy from a start text to the newest turn takes unrelated turns in
   between, against criterion 2's "every turn of its talk about this ask", and two owner turns
   with the same start have no rule. No refutation. **A design choice**: the plan as it stands,
   against `talk` taking only the turns Lem names (a list of start texts or the transcript's turn
   ids), with the newest match of a start text.
5. **What restarts a lead held for an irreversible choice after a lost message.** Repaired:
   "answered" covers `choice N waits for the owner`, and `due.start` gives a fresh lead. Closed.
   Settled by the two, not checked by the review.
6. **A fresh companion after a closed one** (answers lost mid-interview; the interview's own
   `the criteria wait for the owner` line with no lead's report). Repaired: each direction into
   `directions.md` as he names it, the personas' answers into `criteria-read.md`, a resume from
   those files, and no criteria-wait line in a companion. The reviewer: "holds, layer over the
   decision to reopen a fresh interview companion from task files, which rests on criterion 7":
   an answer that sets the outcome and is no direction is still lost, and the resume misses his
   word to skip the read (`READ_SKIP`), which leaves no `criteria-read.md`. No refutation.
   **A design choice**: the plan as it stands, against the companion keeping each answer, outcome
   and direction, in a file as it comes, and the resume reading the `READ_SKIP` decision too.
7. **The fast-to-standard paths into the interview companion.** Repaired: `FAST_GREW` is an
   `interview` need with the builder's report as the scout's; `standard-track` writes the
   interview's `held` line and opens its companion. The reviewer held it, and the defender
   confirmed it by a call: `track_of` returns `fast` for `held: the interview waits for the
   owner` above a `small change: one builder` block, so `open` refuses the `standard-track` path,
   and the `FAST_GREW` path from `stopped.md` has no step that writes `talk.md`. No refutation.
   **A design choice**: the plan as it stands, against `standard-track` writing a line that
   `track_of` reads as standard, and both paths running `lem companion talk` before `open`.
8. **A dismissed card, and which of two choices of one task opens.** Repaired: `close --why
   dismissed`, `due.open` leaves such a need out, `open --asked` opens it on his word, and the row
   of a choice types `/lem status SLUG choice N`. Closed, "layer over the decision to keep an
   unanswered choice pending after dismissal, which rests on criteria 5 and 7". Settled by the
   two, not checked by the review.
9. **Where the experts' answers are** (`said`, not only `advice`). Repaired: the companion reads
   the experts' level of `said` and `advice`, and runs the experts on his word when neither holds
   an answer. The reviewer held it: a ladder that reached the experts and got no answer from
   either is told as "settled before the experts". No refutation. **A design choice**: the plan as
   it stands, against the empty case reading the experts' level of `said` as it is ("asked, no
   answer") before it says the ladder settled earlier.
10. **Which approval ends the wait in the pull request's line.** Repaired: the newest
    `CRITERIA_WAIT` block other than `FAST_GREW`, and the first approval by `owner` after it. The
    reviewer held it: after an `--alone` approval, a later approval of his is of other criteria,
    and criterion 6 ties his yes to the criteria that waited. The defender refuted it with
    criterion 6's words ("when he gave it") and the two rules' two questions; the reviewer held it
    again. **A design choice**: the plan as it stands, against the end of the wait being the first
    approval after the block by anyone (`owner` or `alone`), with the line saying his yes only when
    that approval is his.
11. **The new block joins the full check.** Repaired: `suites` in `tests/all.sh` and `blocks` in
    `tests/test-lem.sh`. Closed. Settled by the two, not checked by the review.

Where the seven design choices went (`stages/plan.md`, step 5; the task runs without the owner,
so each log is the end, and `lem decisions list interview-in-a-companion` holds each). The plan's
text above is as the talk left it; the lead that builds reads each decision below as the plan's,
in place of the option the text describes:

- question 1: option B, by the gate (checkable; decision 20). The companion writes no state after
  the approval; `due.start` finds the newest `held` block with an approval after it, read from
  `criteria.json` as well as the event; the board and the status read the same rule.
- question 3: option C, by the dialectic (decision 26). At each turn Lem reads the files as they
  are: each interview or criteria that wait for the owner while his status says away get the away
  steps, the message to its companion among them, with a record of which companions it told; at
  `/lem im-back` each irreversible step opens, also one whose card he closed. Not green.
- question 4: option C, by the dialectic (decision 27). The copy is every turn from the one where
  the topic began to the newest, minus the turns Lem names to leave out as another topic, and the
  companion's first words name each left-out turn by its time and first words. In every option
  the copy leaves out records the owner did not type (the skill body `/lem` loads, task
  notifications, agterm mail), copies a `/lem` line as he typed it, and takes the newer of two
  owner turns a start text matches: the brief check of the panel found that the transcript holds
  such records as owner records (2026-11-19). Untested: whether `CLAUDE_CODE_SESSION_ID` follows a
  `/clear`. Not green.
- question 6: option B, by the gate (checkable; decision 21). The companion also keeps each answer
  that sets the outcome in a notes file of the task directory as it comes, and the resume reads
  the owner's logged word to skip the read (`READ_SKIP` in `decisions.jsonl`).
- question 7: option B, by the gate (checkable; decision 19). `/lem standard-track` writes a line
  that `track_of` reads as the standard track (or `track_of` reads the interview's `held` line as
  standard), and both paths run `lem companion talk` before `lem companion open`.
- question 9: option B, by the gate (checkable; decision 22). The empty case reads the experts'
  level of `said` as it is before it says that the ladder settled earlier.
- question 10: option B, by the gate (checkable; decision 23). The end of the wait is the first
  approval after the block by anyone (`owner` or `alone`); the line names his yes and its time
  only when that approval is his, and otherwise says that the wait ended without him.

Decisions 24 and 25 record that the talk changed decisions 15 and 16.

The mechanisms the repairs added, with the decision each sits on:

- `lem companion due`'s `start` over the record (questions 1, 2, 5): on the changed decision 16,
  which rests on the owner's direction "The task's files stay the truth: at each turn Lem starts
  the lead of an approved task that has no lead" (`directions.md`). At the cause.
- `lem companion talk` over the transcript (question 4): on the changed decision 15. At the cause;
  the question stays open on its range rule.
- `criteria-read.md` and the resume from the task's files (question 6): a layer over the decision to
  reopen a fresh interview companion from the task's files, which rests on criterion 7. Open.
- `close --why dismissed` with `open --asked`, and `/lem status SLUG choice N` (question 8): a
  layer over the decision to keep an unanswered choice pending after a dismissal, which rests on
  criteria 5 and 7. Closed, and it stays.

Raised after the first turn: none. Additions refused as unpriced: none.

What changed in the plan, by task: task 1 (the one rule of which need waits and when it is
answered, `talk`, the refusals while he is away and for a task without him, `due`'s `start` from
the record and its `open` with no dismissed card, `--asked`, the unit cases, both suite arrays);
task 2 (what the companion reads, the resume from the files, `criteria-read.md`, the approval as
the whole handoff, the experts' answers, `--why dismissed`, his away and back typed in a
companion); task 3 (the brief before the companion, `talk`, `start` from `due`, `stopped.md`'s
`FAST_GREW` and held choice, `status SLUG choice N`, `standard-track`, his words of away from a
companion); task 4 (approved with no lead by the record's rule, the row of a choice); task 5 (the
wait and its end); the decisions on the copy of the talk, the handoff and the board's rows.

## Decisions of the plan

Each is logged with `--by lead` in `lem decisions list interview-in-a-companion`.

- A script opens the companion (task 1), where the plan talk's companion is a line in the
  harness file: the name in the sidebar, no focus, one companion for each need, the refusal while
  he is away and the record for the board must hold the same way each time, and only a script can
  be tested for that. It assumes that `agtermctl` belongs in a script as it does in `board.py`.
- `lem companion talk` copies the talk from Lem's own Claude Code transcript into `talk.md`
  (task 1), since a compaction leaves a summary in the agent's context and the turns in the
  transcript (the talk's Q4). The transcript's format is the harness's: `harness/claude-code.md`
  names it, as `corrections.py` already reads it for the hook. Lem chooses only the turn where
  the topic began.
- The approval or the answer on record is the whole handoff of a companion (the talk's Q1, Q2
  and Q5): `lem companion due` gives the start from it, and Lem writes the lead's brief when it
  opens the task and takes step 7 and step 8 of "Open the task" after the answer, as today.
  The companion's state `queued` with `the criteria are approved: Lem starts its lead` is for the
  board and the status only, and no `lead:` line is written before a lead runs (`READ_SKIP`).
- The companion runs on the owner's default Claude: no seat and no model flag, since no setting
  names one and a new key is the owner's.
- The companion starts in the main checkout and edits no tracked file; it writes only through
  `lem` (the criteria, the decisions, the state) and in its task directory (`directions.md`,
  `task.md` and `criteria-read.md`).
- A row of the board whose companion is gone types `/lem status SLUG`, or
  `/lem status SLUG choice N` for a choice, and bare `/lem` opens one for each need that waits,
  dismissed ones too: no new command of his. At Lem's other turns `due` opens no card he closed
  (the talk's Q8).
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
