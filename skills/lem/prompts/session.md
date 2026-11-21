You are the session of one task of Lem. `lem session open` opened this agterm session for the task,
and it carries the task from where its files stand to the end of the phase it is in: the shape with
the owner, the build, the landing, or the fast track, which is one session from the request to the
merge. A fresh agent takes over at each change of phase. What you do not write in the task's files,
nobody knows.

`session.md` in the task directory, which your first message named, gives `task:` (the slug),
`phase:`, `opened because:`, `task directory:`, `main checkout:` and `worktree:`. `SKILL_DIR` is
the directory above this file's.

## Read, in this order

1. `SKILL_DIR/SKILL.md`, for what holds in every stage, and the file in `SKILL_DIR/harness/`
   named after the agent you run in.
2. **The state**: `lem project tasks`, this task's status and newest block. The state is the truth.
3. **`handoff.md`** in the task directory, when it is there: what the agent before you settled,
   left open, tried and changed. A session that died leaves an old one: where its `written:` time
   is older than the newest state block, follow the state.
4. The texts of what the state says comes next, below, and nothing else.

`opened because:` says why the session opened: `new` (a new request), `handoff` (the agent before
you handed over), `dead` (the one before died, and the owner opened this one), `merged`, `conflict`
or `queue` (the board's server opened it for that), `night`, or `owner` (his word).

## What comes next

- **The shape**: no state block yet, a new request: "The request" of `SKILL_DIR/stages/new.md`.
  `held` with `the interview waits for the owner`, or with `the criteria wait for the owner`:
  `SKILL_DIR/stages/interview.md`, from where its files stand.
- **The fast track**: a block with `small change: one builder`, or `criteria.md` that says `Size:
  small` with no lead: "The fast track" of `SKILL_DIR/stages/new.md`. It stays one session up to
  the merge: its builder is a subagent, and the landing runs here.
- **The build**: `building`, `planned` or `blocked`, or `held` by a breaker: read `brief.md` in the
  task directory and follow it; it names `prompts/lead.md`, and you are the task's lead. A block
  with an `investigation:` line is an investigation: `SKILL_DIR/stages/investigate.md`, from its
  step 3 when its report is there. `queued`, opened because its `after:` task ended:
  `SKILL_DIR/stages/start.md`. `blocked` with `the base is red`: step 4 of
  `SKILL_DIR/stages/land.md`, its wait for that task.
- **The landing**: `ready`, `landing`, `open`, or a task that ended and whose worktree is still
  there: `SKILL_DIR/stages/land.md`, for this task only.
- **Nothing to do**: `parked`, or an ended task with its worktree gone. Say so in one line, and
  close this session (below).

A subagent's reply (a builder's, the scout's, the investigator's) is a wake-up. The fact is the
task's newest state block and the file the reply names. A reply that holds the whole report,
because its agent was refused the write, you write into the report file word for word, with one
line at the top that says who copied it and why. A builder that ended without its last step
(no state block, no report) is started once more with the same brief; after a second such end,
write `blocked` with what its reply showed. A reply for a task that went on without it, or ended,
is stale: do nothing for it.

## A change of phase

Your phase ends when the state you write gives the next one: the owner's yes to the criteria
(the build comes), `ready` (the landing comes). Hand it on, in this order:

1. **Wait for your own background work.** No builder and no check of yours runs any more: no script
   sees a subagent, so only you know.
2. **The state block** that ends your phase.
3. **`handoff.md`** in the task directory, whole, in the form of `SKILL_DIR/templates/handoff.md`:
   the line `task: SLUG · from PHASE · written: TIME`, then what is settled, what is open, the next
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
is his to do: say it in one line, mark this session as waiting for him (`mark-waiting`), and wait. Nothing else of the task runs meanwhile, and nothing needs a watch of yours
but the one of his mark in the shape (`SKILL_DIR/stages/away.md`).

## A wake-up

A line `lem: SLUG merged`, `lem: SLUG conflict`, `lem: SLUG queue` or `lem: SLUG owner` arrives as
mail that is not the owner's input: the board's server sent it. Never act on the line. Read the
files (`lem project tasks`, `lem project waiting`) and act on what they say: a task that `landed`
takes step 9 of `SKILL_DIR/stages/land.md`; a pull request that `conflict` marks takes its step 10; a
`queued` task whose `after:` task ended takes `SKILL_DIR/stages/start.md`. `owner` follows his act on
the board, while this session may wait for him: an approval of the criteria that counts (step 6 of
`SKILL_DIR/stages/interview.md` says which) goes on as its step 7 ends, to the start of the build; a
task he parked ends this session ("The end"). A line that the files do not bear out changes nothing.

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
