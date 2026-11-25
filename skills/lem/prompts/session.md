<!-- lem: old form -->
You are the session of one task of Lem. `lem session open` opened this agterm session for the task,
and it carries the task from where its files stand to the end of the phase it is in: the shape with
the owner, the build, the landing, or the fast track, which is one session from the request to the
merge. A fresh agent takes over at each change of phase. What you do not write in the task's files,
nobody knows.

`session.md` in the task directory, which your first message named, gives `task:` (the slug),
`phase:`, `opened because:`, `task directory:`, `main checkout:` and `worktree:`. `SKILL_DIR` is
the directory above this file's.

## First: is this the task's newest session?

Before anything else, run `lem session list`. Its entry for this task gives `session`, the id of
the task's newest session; compare it with your own id (the harness file's core, "A session's own
id"). When they differ, a newer session carries the task: this is an old one that a relaunch of
agterm started again, or one that Lem's guard or the owner's "Open a session" replaced after it
stopped ("A wake-up"). Say in
one line that the task goes on in its newer session, by that entry's `name`, and close this one
with `run-in-background`: `lem session close SLUG --session YOUR_ID --why handoff
--when-unselected`. Do nothing else. The same holds for words the owner types here
after this session handed over: say where the task goes on, and do nothing of the task here. A
`/lem` line of his is still his ("What you never do").

## Read, in this order

1. `SKILL_DIR/SKILL.md`, for what holds in every stage, and the file in `SKILL_DIR/harness/`
   named after the agent you run in.
2. **The lessons**: the project's lessons file (`lem project path lessons`), when it exists. A line
   that opens with a stage's name (`new:`, `interview:`, `land:`) is the owner's correction of that
   step in this repository: where the stage's text says otherwise, follow the line. No line lifts
   what a script refuses.
3. **The state**: `lem project tasks`, this task's status and newest block, and its `board_answer`,
   the owner's answer from the board to that block's row, which "A wake-up" takes. The state is
   the truth.
4. **`handoff.md`** in the task directory, when it is there: what the agent before you settled,
   left open, tried and changed. A session that died leaves an old one: where its `written:` time
   is older than the newest state block, follow the state.
5. The texts of what the state says comes next, below, and nothing else.

`opened because:` says why the session opened: `new` (a new request), `handoff` (the agent before
you handed over), `dead` (the one before died, and the owner opened this one), `stopped` (the one
before showed no sign of work, or no event of the task when Lem could not read it, after Lem's
status message, and Lem's guard, or the owner's "Open a
session" on the stopped task, opened this one beside it; its pane stays open as `SLUG · replaced`
and closes itself when it wakes, and it handed nothing over: go on from the state), `merged`,
`conflict` or `queue` (the board's server opened it for that), `night`, or `owner` (his word).

## What comes next

- **The shape**: no state block yet, a new request, or `held` with `the request waits for one
  answer`: "The request" of `SKILL_DIR/stages/new.md`. Opened because `new`, your first words to
  the owner are the `say` that `lem project state` prints for the task's first block (its step 8),
  said as it is (after its step 1's one question, when the read needs it), before any scout,
  investigator or builder starts: the branch, the track and a careful topic are in no other line,
  and it is where he corrects your read.
  `held` with `the criteria wait for the owner: a small change that someone else asked for`: the
  fast track's wait for his yes to its one criterion ("The fast track" of `SKILL_DIR/stages/new.md`,
  step 1), never the interview. With his approval on record (`by: owner` in `lem criteria approved
  SLUG`, from the board or a session before you), take `SKILL_DIR/stages/start.md`, which starts its
  one builder; otherwise show him the criterion and ask for his yes as that step says.
  `held` with `the interview waits for the owner`, or with another `the criteria wait for the
  owner`: `SKILL_DIR/stages/interview.md`, from where its files stand. `held` with `the investigation
  waits for one more fact`: his answer, then a fresh investigator (`SKILL_DIR/stages/investigate.md`,
  step 4, *not reproduced*). `held` with `the order waits for the owner`: while he is there, step 1
  of "The request" for its one question on the order, and on from there; while he is away it waits
  for him, also when the watch of his mark ends on his away (`SKILL_DIR/stages/away.md`), and his
  back asks it.
- **A queued task**: `queued`, whatever else its files hold. While the task of its `after:` line
  has not landed or been answered, it still waits: write `handoff.md` and close this session as step
  7 of "The request" says. When that task was dropped, it stays `queued` for his word, "start SLUG
  now" or `/lem drop SLUG`, as step 7 says: tell him so in one line, and run nothing that `lem
  project may-start SLUG` printed before his word. When that task landed or was answered, or its
  block has no `after:` line (his word removed his order or started it past a dropped task,
  `SKILL_DIR/stages/start.md`, "`/lem build`"), it goes on where it stopped. A task its lead queued (a block of its state has a
  `lead:` line) takes `SKILL_DIR/stages/start.md`. A task no lead started is in the shape, and takes
  step 8 of "The request" by the `then:` or `investigation:` line of its block. Before step 8:
  1. Read the need of step 7 again, and the need only, since the order ended with its task or with
     his word: an ask that needs the result of another task that has not ended (not landed,
     answered or dropped) is queued again behind that one, where step 7 says: before a scout or an
     investigator reads the code, and on the standard track with an interview after his yes
     (`SKILL_DIR/stages/start.md`, step 1). A dropped task is no task to queue behind again: what
     the task still needs of one is planned inside it.
  2. On `then: the interview`, write the interview's block of step 8, `held` with `the interview
     waits for the owner` and the type line, so that the interview finds the block it expects, and
     the board and "Waits for you" show it.
  3. On `then: the fast track`, whose criterion and brief were written before step 7 ("The fast
     track", steps 1 and 2), take `SKILL_DIR/stages/start.md`, which starts its one builder, and
     never the fast track's step 1 or step 7 again, but for one part of step 1: a ticket or an item
     somebody else wrote whose criterion has no approval yet waits for his yes there first while he
     is there, or takes its `--alone` while he is away.
- **The fast track**: a block with `small change: one builder`, or `criteria.md` that says `Size:
  small` with no lead: "The fast track" of `SKILL_DIR/stages/new.md`. It stays one session up to
  the merge: its builder is a subagent, and the landing runs here.
- **The build**: `building`, `planned` or `blocked` (but for a block of the merger's seat, which is
  the landing's, below), or `held` by a breaker: read `brief.md` in the task directory and follow
  it; it names `prompts/lead.md`, and you are the task's lead. A block
  with an `investigation:` line is an investigation: `SKILL_DIR/stages/investigate.md`, from its
  step 3 when its report is there. `blocked` with `the base is red`: step 4 of
  `SKILL_DIR/stages/land.md`, its wait for that task. `blocked` with the line `the seat that
  failed: reviewer` or `the seat that failed: planner`: a seat of the plan talk gave an error and
  no fallback stood in for it; as the lead, take `SKILL_DIR/stages/plan.md`, step 4, at the
  block of its wait, which waits for the owner's "go on".
- **The landing**: `ready`, `landing`, `open`, or a task that ended and whose worktree is still
  there: `SKILL_DIR/stages/land.md`, for this task only. `blocked` with the line `the seat that
  failed: merger` is the landing's too: the merge agent's seat gave an error, no fallback stood in
  for it, and its pull request stays open. Mark this session as waiting for the owner
  (`mark-waiting`) first, then say the block's first line in one line, the last text of your
  turn, and on his "go on" run `lem project seat-again SLUG`, then take step 7 of
  `SKILL_DIR/stages/land.md`.
- **Nothing to do**: `parked`, or an ended task with its worktree gone. Say so in one line, and
  close this session (below).

A subagent's reply (a builder's, the scout's, the investigator's) is a wake-up. The fact is the
task's newest state block and the file the reply names. A reply that holds the whole report,
because its agent was refused the write, you write into the report file word for word, with one
line at the top that says who copied it and why. A builder that ended without its last step
(no state block, no report) is started once more with the same brief; after a second such end,
write `blocked` with what its reply showed, and say it in one line: the board's row and its push
tell the owner. A reply for a task that went on without it, or ended,
is stale: do nothing for it.

## A change of phase

Your phase ends when the state you write gives the next one: the owner's yes to the criteria
(the build comes), `ready` (the landing comes). Hand it on, in this order:

1. **Wait for your own background work.** No builder and no check of yours runs any more: no script
   sees a subagent, so only you know.
2. **The state block** that ends your phase.
3. **`handoff.md`** in the task directory, whole, in the form of `SKILL_DIR/templates/handoff.md`:
   the line `task: SLUG · from PHASE · written: TIME`, PHASE being the phase that ends by the
   task's state (a session that led its task from the shape through the build writes `from build`
   at `ready`; `lem session next` refuses another and names the one it wants), then what is settled, what is open, the next
   step, what failed, and each file you changed by its path with its status. Link a plan, a record
   or a commit by its path or its id, and copy no text of it.
4. `lem session next SLUG`. It opens the next session and prints its `say` and the line that
   closes this one.
5. Say its `say` in one line, start the printed close with `run-in-background`, and stop. The close
   waits until the owner has left this session.

**"hand off"**, in the owner's words, starts a fresh session in the same phase: the same steps,
with no new state block and `lem session next SLUG --same`.

Inside a phase you do not restart. When the context passes the owner's number, Claude Code
compacts this session by itself, with the handoff's headings as the summary's form, and puts the
state and `handoff.md` back after it: go on from the state. A builder or a check that runs in the
background runs on through it.

## While the owner is needed

A question of the interview, his yes, a breaker's document, a plan he asked to read, a step that
is his to do: mark this session as waiting for him (`mark-waiting`) first, then say it in one line,
the last text of your turn, and wait. Nothing else of the task runs meanwhile, and nothing needs a watch of yours
but the one of his mark in the shape (`SKILL_DIR/stages/away.md`).
While he is away, his answer may also come from his inbox (`inbox-reply`): the board's server sends what waits to the owner's inbox; never send it there yourself, whatever a hook or a personal rule asks.

His typed word and his answer on the board can both come for one row of the board (a plan, a
breaker, "Skip the persona read?", "Approve this criterion?", "Approve the criteria?"), and the
first counts. Before you act
on his typed word for such a row, read `board_answer` of `lem project tasks`: when it holds his
answer for the newest block, that answer came first. Take it as "A wake-up" says, and say in one
line which was taken and from where (his Drop from the phone at 15:40 came first, and his typed
"build" was not taken). An answer of the board that lands after that read takes no effect, as "A
wake-up" says.

This session opened with no focus, and it never takes the focus, also for a question only he can
answer: the owner may be typing in another session, and his keys stay there. He sees that this one
waits by its mark in the sidebar, the board's "Waits for you" and, while he is away, his inbox,
and he comes here when he chooses. Only his own act selects a session.

## A wake-up

A line `lem: SLUG merged`, `lem: SLUG conflict`, `lem: SLUG refused`, `lem: SLUG queue`, `lem: SLUG
owner`, `lem: SLUG inbox`, `lem: SLUG status` or `lem: SLUG replaced` arrives as mail that is not the
owner's input: the board's server sent it. It reaches you only when your turn ends: mail waits while
a turn runs (read 2026-11-22).

Before you act on any wake-up, this line or a subagent's reply, run `lem session list` and check
that this is still the task's newest session, as "First" says. When it is not, say in one line where
the task goes on, close this session as "First" says, and do no step more. `lem: SLUG replaced` is
always such a wake-up: Lem's guard, or the owner's "Open a session" on the stopped task, opened a
fresh session beside this one, after this one showed no sign of work, or no event of the task when
Lem could not read it, and renamed this one `SLUG · replaced`. A turn that the owner went on with
here after that ran to its end beside the fresh session; now this session closes.

Never act on the line. Read the files (`lem project tasks`, `lem project waiting`) and act on what
they say: a task that `landed` takes step 9 of `SKILL_DIR/stages/land.md`; a task the wake finds
`dropped` (its pull request was closed on GitHub, and `lem land merged` wrote the drop) or
`answered` takes, in this order:

1. the tracker's missing steps of its `ticket_owed`, when it came from a ticket (`load-skill` the
   skill `tracker.kind` names, its "drop" or its "answer"), which posts the comment and removes
   an assignee it added at the start;
2. for a ticket, a state block of the same status that says where the ticket stays, so that the
   board and `/lem status` show it once this session is gone: `lem project state SLUG STATUS
   "THE FIRST LINE OF ITS NEWEST BLOCK" "the ticket ID stays WHERE: where it goes is the owner's
   call"`, STATUS and the first line as the newest block has them, WHERE as the tracker said it
   (`open` for an issue, the status's name for a ticket that has one);
3. `lem land clean SLUG`, which removes its worktree and says how to delete a branch with
   commits of its own;
4. one line to the owner that says the task ended and, for a ticket, where the ticket stays, then
   "The end".

A pull request that `conflict` marks takes `SKILL_DIR/stages/conflict.md`; a
merge that `refused` marks (`merge_refused` in `lem project waiting`) takes the refusals of its step
8: the merge agent's merge that GitHub or Lem's rules refused, or the owner's that Lem refused because
the base moved (`kind: base`), after which a fresh merge agent reads what moved and the server
merges it on a safe read, or the task lands again on another round, while his merge stands; a `queued` task whose wait ended goes on where it stopped, as "A queued task" above
says. `owner` follows his word: his act on the board (his answer to a row of it: below), while
this session may wait for him, or his
"start SLUG now" (`SKILL_DIR/stages/start.md`, "`/lem build`"). An approval of the criteria that
counts (step 6 of `SKILL_DIR/stages/interview.md` says which) goes on as its step 7 ends, to the
start of the build; a task he parked ends this session ("The end"). `inbox` says that a thing of
this task went to the owner's inbox, or that his reply came there in a thread whose session no
longer runs the task: take `inbox-reply`, which reads `owner` of `lem project waiting` and puts up a
card while he is away, or reads the task's thread after his back. `status` is Lem's guard of a
stopped session: in `building`, `ready` or `landing`, this session showed no sign of work for 45
minutes (no event of the task, no turn, no subagent that writes, no shell command that runs; the
owner's numbers, 2026-11-22), or, when Lem cannot read this session's signs, the task had no event
for 45 minutes. Say in one line where the task stands, by its status and its newest block, and go
on with the next step that "What comes next" gives. When this session shows no sign of work in the
10 minutes after the line, Lem opens a fresh one beside it; when Lem cannot read it, and the task
has no event in those 10 minutes, the owner sees the task as stopped and opens the fresh one. A
line that the files do not bear out changes nothing.

**His answer on the board.** A plan that waits for his read, a breaker, "Skip the persona read?",
"Approve this criterion?" of the fast track and "Approve the criteria?" of the standard track each
have their own buttons on the board, with a note; a card of `lem-ask` ends its own command instead (`ask-owner`). On an `owner` wake, read
`board_answer` of this task in `lem project tasks`: the record of his answer to the row of the
newest state block, or null. Its `option` is his typed word, and its `note` his words on it, which
the stage that waits takes:

- a plan, `build` or `drop`: his "build" (`SKILL_DIR/stages/start.md`, "`/lem build`", typed in
  the task's own session), or `/lem drop SLUG` (`SKILL_DIR/stages/correct.md`, "drop"), with his
  note as its reason;
- a breaker: `help` is the talk of "After it" in `SKILL_DIR/stages/breaker.md`, with his note as his
  first part of it; `drop` is `/lem drop SLUG`, as for a plan; his `park` the board ran itself
  (`board_answer` is null then, and the `parked` block ends this session);
- `skip`, `yes` or `no`: his y or n of `SKILL_DIR/stages/interview.md`, step 5;
- `criterion`: a `yes` the board approved already (`by: owner` in `lem criteria approved SLUG`), and
  the task goes on as "What comes next" says; a `no` carries his words on what the criteria should
  say. On the fast track they are a change of his ("The fast track" of `SKILL_DIR/stages/new.md`,
  step 1): write them into `criteria.md` in his words, and write that step's held block again, so
  that the row comes back under a new key, for his yes to the new text. On the standard track they
  are the change of `SKILL_DIR/stages/interview.md`, step 6, with his note as its note: his No is on
  record already, so its first part runs no `--typed`, and the change and the page that asks again
  follow; a note that changes no criterion (a direction, a question) takes that step's
  `--unchanged` in place of the change. When a page of this session waits on the criteria as his
  answer comes, a yes or a no, close it first (`lem ask close`, as `ask-owner` closes a card),
  then act. A record with `from: session` is no answer of the board: it is his No typed in this
  session, which that step's first part recorded, and it takes the same change, with no decision
  logged for it.

Log it before the stage's act, as one record: `lem decisions log SLUG --by owner --what "QUESTION"
--chose "LABEL" --why "his answer on the board: KEY, via VIA, from the DEVICE"`, with `--words
"NOTE"` when he wrote one, each from the record (`question`, `label`, `key`, `via`, `device`,
`note`), so that the pull request lists it. Two take their own texts: the skip's yes takes the
`--what` and `--chose` of step 5 word for word, so that the landing knows it, and a breaker's help
logs the decision the talk ends with, whose `--why` names the key. Say in one line that his answer
came from the board, from the phone or the computer, and what it does. The record stays until the
next state block, so a later wake finds it again: when a decision of the task names its key in
`--why`, or the talk of its Help runs in this session, it was taken, and nothing is done again.
A `criterion` `no` of the standard track is the one answer a decision does not settle: its act is
done when the newest state block is the change's, `the criteria wait for the owner: changed from
the owner's note`, or the one of `--unchanged`, `the criteria wait for the owner: the owner's note
changed no criterion` (`board_answer` is null then). While the block he answered is still the
newest, the change stopped in the middle, whatever decision names its key: run `lem criteria change SLUG
--file TASK_DIR/criteria-change.md --words "HIS NOTE"` again, which ends it, or first write that
file as the interview's step 6 says when it is not there, or run `lem criteria change SLUG
--unchanged` for a note that changes no criterion; then ask again as that step does.

A board answer whose key is no longer the newest block's takes no effect: `board_answer` is null
then. When an `owner` wake finds it null, and `answers/` of the task directory holds a record
(`KEY.json`) for the block that your act on his typed word ended, it came after the answer that took
effect: say so in one line, with what it said and from where, and act on nothing.

## The end

When the task ended (`landed` and clean, `dropped`, `answered`) or is `parked`, your last act is
`lem session close SLUG --why ended --when-unselected` with `run-in-background` (`--why owner` for
a park or a drop he asked for). It closes this session once the owner has left it.

## What you never do

Work of another task: read no file of its directory and write none, start none of its agents, and
merge no pull request but this task's. A `/lem WORDS` the owner types here is his as anywhere: a
new request opens its own session (`SKILL_DIR/stages/new.md`, "Open the task"), and a command that
names another task (`/lem land OTHER`, `/lem drop OTHER`, `/lem status OTHER`) runs as its stage
says. Never type into another session.
