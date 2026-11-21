---
name: lem
description: "Lem coordinates the work of coding agents in one repository: `/lem new`, `plan`, `build`, `land`, `night`, `status`, `serve`, `reviewer`, `learn`, `retro` and `init`, or `/lem` followed by an ask in plain words. Each task gets an agterm session of its own, from its shape with the owner to its merge, with a fresh agent at each change of phase: a lead and its builders on the standard track, one builder on the fast track. Each branch goes through the machine checks and a review to a pull request that says green or not green, many at the same time, and a merge agent reads it. It reads the repository's own settings (`.lem/project.toml`: checks, what must never go wrong, who lands) and its personas, lessons, rulings and rules, and gives a change that reaches what must never go wrong the full review and a person's merge. Use when the user says \"lem\", \"/lem\", \"lem new\", \"lem status\", \"lem serve\", \"put the board on my phone\", \"lem land\", \"lem night\", \"lem init\", \"lem retro\", \"ask Lem\" or \"tell Lem\"."
---

# Lem

One command carries a unit of work from the ask to a pull request that says whether it is green,
the same way in every repository. What differs between repositories is in the repository: its settings file names
the machine checks of a landing and what must never go wrong, and beside it are the personas, the
lessons, the rulings and the review configuration, each in its one place, and the rules for the
code in `.claude/rules`. This skill holds the flow and knows no project.

The owner is a developer whose attention is short, and a task takes one of two tracks.
The fast track is for one plain change: one acceptance criterion in his own sentence, nothing careful
and no question open, whatever its type (a fix of one rule, a typo, a rename, a version bump, a line
of a document). One builder makes it and files in the backlog what it saw outside it, the machine
checks and one read review it, it has no polish pass, and the merge agent reads it and merges it. Every other request takes the standard track, and the flow asks for his attention at
three touches: the interview, while a scout reads the code around his ask; the criteria, which the
personas read before he does and which he approves, so that they are the contract in plain
language and become the tests; and the merge, which is his only when a fresh merge agent, which
reads every proposed task, calls him with its review: for a careful change, for a request that is not
green, for what it found, or in every task where the settings say `branch.land = "owner"`. The build asks him nothing; only a circuit breaker stops a task, with a document for him.
He answers the interview, his yes to the criteria and a breaker in the task's own session. A task on the standard track from a complete request (a ticket that says what is wanted, a settled
backlog item) has no interview, and its criteria wait for him only when a persona doubts them.
Lem names the type of each request from its words, a Conventional Commits type (`feat`, `fix`,
`docs`, `refactor`, `perf`, `test`, `chore`) or `question`, and its track, and says both in one
line before anything runs. The records name the two tracks by their own words: `small` for the fast
track and `full` for the standard track (the `Size:` line of the criteria, `size` in the events, the
`call` of an investigation), and the state line `small change: one builder` for the fast track's
builder. Keep those tokens where a command needs them, and say the track's name to a person. A bug whose cause the request does not show is investigated
before any criterion: a fresh builder reproduces it as a failing test and finds its cause, and its
report sets the track. A question is the same work, and ends `answered`, with
a report and nothing to merge. Between the touches a task builds without him. A plan whose change makes a document
false ends with a documentation task. After the last task a fresh builder makes the polish pass, a
short fixed list of what a build leaves behind (a comment made false, a leftover, code that reads
badly, a document made false, the defects outside the task, fixed when cheap or filed), and changes
no behavior. Then the change passes the machine checks and a
review by an agent that did not build it, as large as the change needs. Nothing is reviewed after
the merge, since reviews queued after a landing stay open (43 of 48 about 28 hours later:
convertiser-server, 2026-11-14), and nothing is argued task by task. Only a careful or large plan
is talked through, once, before any code. The price of one review at the end is not measured, so
the event log keeps each review's rounds and counts, and each request that was not green with
its reason.

## One session for each task

**A task's session** is an agterm session of its own, named for the task, which `lem session open`
starts (`open-task-session`). It carries the task from its shape to its merge, and no session holds
two tasks: a session that holds many tasks fills with their code and loses them. Its phases are the
shape (the request read, an investigation, the interview and the criteria, with the owner), the
build (the lead and its builders), and the landing (the checks, the review, the pull request, the
merge agent, the cleanup). A fresh agent takes over at each change of phase: the one that leaves
writes `handoff.md` and runs `lem session next`, which opens the next session and closes the old
one once the owner left it. The fast track is one session from the request to the merge, since a
fresh session starts at about 84,000 tokens (a second opinion's median of 10 sessions, 2026-11-20).
Inside a phase, past the owner's number of tokens, Claude Code compacts the session by itself, with
the handoff's headings as its summary. Its standing brief is `prompts/session.md`.

**A task's lead** is that session's agent in the build: it writes the plan, starts one fresh builder
for each task of it, also for a plan of one task, reads their reports and writes no code. A task on
the fast track has no lead and no plan: its session starts one builder with `prompts/small.md`, a
brief complete in itself, and the builder's own check of the change against the topics moves the
task to the standard track when the fast track does not fit after all.

**A plan talk's defender** is the agent of a pair the lead opens under its session for a careful or
large plan (a plan of more than three tasks), with the reviewer in its other pane. The defender and
the reviewer argue the plan through the mailbox before any code; the defender repairs the plan,
writes down how the talk went, and stops; the lead closes the pair and builds the talked plan.

**The board's server**, `lem serve`, holds what reaches across tasks, with no context of its own:
it notices a merge or a close on GitHub and runs `lem land merged`, wakes the task's session for its
cleanup, for a pull request that became conflicting, and after the owner's approval or park on the
board, opens the session of a queued task when the task it waited for ended, opens the session of a
task he starts on the board ("+" or a backlog item), and shows a task whose session is gone as "no
session" for the owner. It never types into a session, decides, or closes one.

Every task on the standard track starts with an interview or a complete request, and then a lead,
also one the owner calls careful in the ask: there is no talk before there is a plan. The plan says
whether it is careful or large (`stages/plan.md`), because only the plan names the files and the
tasks. A lead and a defender never ask the owner: the ladder decides, and only the breaker stops.

If your first message named `session.md` of a task, follow `prompts/session.md`. If it named
`prompts/defender.md`, or a brief that names it, your stages are `stages/talk.md` and step 5 of
`stages/plan.md`; a `/lem` typed there is no subcommand of yours: say that it belongs in another
session, and change nothing.

## Before any subcommand

`/lem` runs inside agterm only: the tasks' sessions, the reviewer's pane, the pages for the owner
and the mailbox are agterm's. When `AGTERM_SESSION_ID` is not set, say that the session must be
started in agterm, and stop.

```bash
lem project show
```

`SKILL_DIR` is this skill's own directory. The output is the project's settings, resolved: each
place Lem reads with whether it exists, the base branch, who lands, the commands of the checks and the topics of
what must never go wrong (`flow.topics`). When `settings` is null the repository was never onboarded: only `init` and `status`
run, and every other subcommand says so and stops. Read the project's `AGENTS.md` once per
session; it is where a project says what its own scripts are (a worktree script, a landing
script, a board). Read the project's lessons file (`places.lessons` in the output, `.lem/lessons.md`) when it exists: a
line that opens with the name of a stage or of a shipped skill is the owner's correction of it
for this repository, and you follow it where that text says otherwise. No line there lifts what a script
refuses.

`lem` is Lem's one command: `lem NAME ARGS...` runs the script `NAME.py` of this skill's
`scripts/`, or a shipped skill's (`lem experts`, `lem cast`), and `lem help` lists every name.
Run Lem's scripts only through it. The harness file says where it comes from, and what to run
where the shell does not find it.

## Subcommands

`/lem` runs in any session: a task's, or one of no task. Read the stage file when the subcommand
runs, and follow it. Do not read the others. In a task's session, `be-careful`, `standard-track`,
`drop`, `park`, `land` and `status` with no task named mean that session's task.

| Subcommand | Does | Read |
| --- | --- | --- |
| `new <what>` | opens the task (its directory, the ask in the owner's words, the talk that led to it) in a session of its own, which says its type and its track in one line and runs it. The fast track: one builder and the landing, and nothing waits. The standard track: the interview there, where a scout reads the code, the personas read the criteria and he gives his yes, then a fresh lead; a ticket or an item whose whole context is written skips the interview. A bug whose cause the ask does not show is investigated first, and a question ends with its answer. `<what>` may be a tracker's ticket, by its id or its URL | `stages/new.md` |
| `plan <what>` | as `new`, and the lead stops at the committed plan for the owner to read. A plan is the standard track's, so the ask takes the standard track, and the task's first line says so | `stages/new.md` |
| `build [<task> or <plan file>]` | the build of a task whose plan the owner read. With no name it lists those tasks and asks which | `stages/start.md`, "`/lem build`" |
| `im-away`, `im-back` | the owner says that he is away, and an interview and criteria that wait for his yes go on without him, or that he is back; a build and a merge are the same either way. His word holds in every repository on this machine | `stages/away.md` |
| `be-careful`, `standard-track`, `drop` `[<task>]` | the owner corrects a task: careful until its merge, the standard track until its pull request exists, or not wanted | `stages/correct.md` |
| `park`, `resume` `[<task>]` | the owner puts a task aside, a breaker's answer with his help and `drop`, or goes back to it: a parked task goes on in its own worktree, and a dropped one in a new task from its handoff and its branch | `stages/park.md` |
| `land [<task>]` | in a task's session, its landing; for a task that is `open`, the owner's word to merge it (`lem land merge --by owner`) | `stages/land.md` |
| `learn`, `retro` | a correction becomes an edit of the file that owns the step | `stages/learn.md` |
| `init` | onboarding: checks the machine, examines the project, interviews the owner, writes the settings and the draft profiles | `stages/init.md` |
| `night` | unattended: takes backlog items, the smallest first, four at most (`/lem night N` takes N), and opens them one after another, each in its own session that runs it without the owner to its pull request | `stages/night.md` |
| bare `/lem`, `status` | the one list of what waits for the owner, the same every time: each breaker of a task, each task whose criteria wait for his yes, each pull request with green or not, those of the night with the night's report, each retro's proposals, and where he answers each; and the board of all tasks. In a task's session, that task's line first. A retro's proposal he answers with approve, reject or later, all on one page | `stages/status.md` |
| `status <task>` | the board of one task, and its session when something of it waits for him and none runs | `stages/status.md` |
| `serve` | the board's server: `lem serve --ensure` starts it when none runs, and you say where the board is, its `url`, and its `tailscale` address when the door is open | `stages/status.md`, "The board's server" |
| `serve tailscale`, or "put the board on my phone" | opens the tailnet door from now on (`lem serve --tailscale`) and says the address the phone opens; `serve tailscale off` closes it (`--tailscale-off`) | `stages/status.md`, "The board's server" |
| `serve join HOST`, `serve leave HOST`, `serve peers` | another computer's boards on this one's address, under its name: `lem serve --join HOST`, `--leave HOST`, or `--peers`, the computers joined and whether each answers; say the JSON's `said` | `stages/status.md`, "The board's server" |
| `serve stop` | ends the server (`lem serve --stop`); the next `lem` command of any session starts it again | `stages/status.md`, "The board's server" |
| `read <ticket>` | reads one ticket of the tracker, by its id (`/lem read MBZ-12`) or its URL, and says what it holds; it opens no task and writes nothing to the ticket. With no tracker in `lem project show`, say that the project has none | the tracker's skill (`load-skill` the one `tracker.kind` names), its "read" |
| `reviewer AGENT/MODEL:EFFORT`, `reviewer default` | who sits in the reviewer's pane on this machine for now, as one seat (`/lem reviewer codex/gpt-6.2-sol:high`; the effort, or the model and the effort, may be left out for the agent's own default), and the project's own reviewer again: `lem project reviewer` with the same words. Say what `lem project show` then gives as the seat | the harness file, `second-opinion` |
| a helper | `/lem interview-me` loads `lem-interview-me` (`load-skill`): read `SKILL_DIR/../lem-interview-me/SKILL.md` by its path and follow it, with the rest of the line as its arguments. Plain words start one too, with or without `/lem`: "let's brainstorm this" or "interview me about X" (`interview-me`), "argue both sides of ..." (`dialectic`), "why does this keep breaking" (`root-cause`), "what would the experts say" (`ask-expert`), "how would the users take this" (`panel`). Outside a session where `/lem` was typed a shipped skill never starts by itself. Lem's stages load `ask-expert`, `panel`, `linear`, `lem-ask` and `lem-gate` themselves: Lem opens its question page each time it asks him, and the gate is the first level of the ladder | that skill |
| anything else | an ask in plain words: `/lem the report dates must stay whole` is `new` with that sentence, also in another task's session. Words that plainly say one of the rows above go there | `stages/new.md` |

A helper's name at the start of a line does not make the line its call: `/lem root-cause analysis
of the logs is slow`, `/lem panel layout breaks on a phone` and `/lem ask the payment provider for
a sandbox key` are asks, and each opens a task. When you cannot tell a helper from an ask, or one
helper from another, ask once in the terminal, in one line, with your guess first: "Do you want an
interview about this first, before I open a task? (y/n)". Never a page for this.

A task runs on from `new` to its pull request without the owner, unless a stage file names a stop.
Between two of the owner's messages a task's session only waits: a builder that stops wakes it, and
so do the end of a command it runs in the background and a wake-up from the board's server.

## What holds in every stage

- **The owner is needed at three points.** The interview and his yes to the criteria (`new`), a
  breaker, and the pull request when the merge agent calls him; a task on the fast track needs him
  at its pull request only. He answers in the task's own session. The build asks him nothing, there
  or away. A lead takes a decision in doubt up a ladder of opinions (the gate, the personas, the
  dialectic, the experts; `stages/ladder.md`), and its pick is taken at once, logged, and said in
  one line in the task's session. A pick past the personas makes the pull request not green. Only
  the circuit breaker stops a task, and only that one: the next step cannot be reversed by a later
  "no", or no option keeps the criteria he approved (`stages/breaker.md`). It leaves him a document;
  he helps, parks the task or drops it. He is away or there for the whole machine: his `/lem
  im-away` in any session holds in every repository, and it matters for an interview and criteria
  that wait for his yes. A night's task runs without him until it ends, whatever his status. A task
  that ran without him is merged as any other: by the merge agent, or by him when it calls him.
  Every other decision is the session's: decide from the code, the settings and the rulings, write
  it in the decisions log, and go on. A red test, a failed command or a moving base branch is the
  work, never a reason to stop.
- **Decisions are logged, and the owner can overturn each.** Each decision made without the
  owner, each breaker and his help on it, through `scripts/decisions.py`: what, what
  was chosen, by whom, why, and what it would take to undo. It writes `decisions.jsonl` in the
  task's directory and an event for the board; nobody writes that file by hand. The report lists
  them as decisions, never as questions, and the pull request lists each one from the record.
- **A destructive or outward step is never yours.** Dropping data, rewriting shared history,
  touching production, bending a check, pushing to a branch the settings do not name: a lead trips
  the breaker (`stages/breaker.md`), and any other session stops and asks, with the evidence.
- **No secret goes into a file.** No agent writes a credential, a key or a value from an `.env`
  file or the environment into a file or a commit: a builder writes the project's name for it,
  and the review reads the diff for one (`prompts/review.md`).
- **The pull request is no step to ask about.** `lem land propose` pushes the task's own branch
  and opens or updates its pull request on GitHub, the one way a task lands, and you run it without
  a question. The owner approved it when he approved the settings at onboarding: they are his
  standing word for exactly this. A question here stops every task one step before its end.
- **One merge, and the merge agent's read before it.** Every proposed task, the fast track's too,
  gets one fresh merge agent (`ask-merger`, `stages/land.md` step 7), which changes nothing and
  writes `merge-review.md`: it merges a green request that is not careful, or calls the owner.
  Every merge, his and the agent's, is `lem land merge SLUG --by owner|merger`, under one lock,
  through GitHub. `--by merger` follows the agent's own verdict only, and the board's server runs
  it: a session writes the review down and never runs that merge. `--by owner` follows only the
  owner's own words, typed in a session or given on the board. Nothing else leaves the machine without his word: a push to another
  branch, a message to a person.
- **What must not go wrong takes the careful flow.** The project names it as topics,
  sentences in the owner's words of what must never go wrong (`flow.topics`), and no list of
  paths: a list goes stale as the code moves, misses new code, and a branch can edit the list
  that guards it. Whether a change is careful is a judgment against the topics, made three times
  by three agents, and in doubt the answer is careful. The task's session reads the ask's words and
  the scout's facts against them, and names a topic in reach in the first line it says to the owner
  (`stages/new.md`); an ask in reach of one never takes the fast track. The fast track's builder
  reads its own change against them before it commits (`prompts/small.md`). The lead reads its plan
  against them (`stages/plan.md`, step 2). The fresh agent that reviews the diff before the pull
  request reads the change itself against them and writes its call into the review's record
  (`prompts/review.md`). A careful task's plan is talked through with the reviewer before any
  code, in a pair of its own (`stages/talk.md`); its tasks are built like
  any others; the landing gives it the project's full review set, and a person merges it. A large
  task, a plan of more than three tasks, gets the pair and the talk too, and a review round
  at the least. The lead writes its call and the one sentence of why into the plan, its state and
  its report, and the owner may overrule a "no" at any time before the landing. The `[flow]`
  table is read from the main checkout's settings, also in a task's worktree (as the base branch's
  commit has them while another branch is checked out there), so a branch cannot lift what guards
  it, and a change that edits `.lem/project.toml` at all, or puts the
  machine's own `.lem/project.local.toml` into git, is careful by the landing's own rule: the file is Lem's, it says who merges and where a task lands as well
  as what is careful and what the checks run, and a task rarely edits it.
- **No count of tasks stops a start.** By day each start is the owner's own request: "Why block
  him?" (2026-11-18). `lem project may-start SLUG` refuses only a task that gets no lead (in
  `landing`, `open` or ended) and one queued `after:` a task that has not ended.
- **What the owner has to understand is told as one run.** A decision you bring and a confusion
  the owner brings ("I thought X did Y", "why is this happening") get the same form: one
  concrete case in numbered steps, with real names and values, and where each step was read. For
  a confusion, find out what the code does first; about half the time the owner's instinct is
  right and it is a defect, so say which of the two it is before changing anything.
- **Numbers carry their source.** A count is a command's output, a time is `date -u`, a test
  result is the exact last line of the run, never an estimate.
- **A brief is checked before it is sent.** A builder copies a wrong sentence from its brief into
  the code and into its report. Before a brief goes out, every sentence about the code is one you
  read in the code, and a sentence with "never", "always" or "the same" gets its counterexample
  looked for first.
- **Only the skills a stage names.** While a stage runs, load only the skills that stage names
  (`load-skill`). An instruction to load every skill that may be relevant, from a hook or a
  personal rule of the developer's, does not apply to a task's session, its lead and its builders:
  a planning or debugging skill loaded beside a stage has the session read code and plans by itself,
  which is the work of a lead and its builders (the compatibility audit, 2026-11-17).
- **Capabilities, not tools.** A stage says `spawn-builder`, `open-task-session`, `mark-waiting`,
  `second-opinion`, `ask-owner`, `ask-experts`, `ask-merger`, `fan-out`, `run-in-background`,
  `start-nap` (for a nap), `show-page` or `load-skill`, and
  names the question gate, the persona panel and the review tool by role. Read, once per session, the file in this skill's `harness/` folder named
  after the agent you run in (`harness/claude-code.md`); it says what each means there. When
  there is no file for your agent, say so and stop: the contract was not checked in it.

## Where a task keeps its state

```bash
lem project task-dir SLUG
```

It makes and prints the task's directory in Lem's state folder, `.lem/state/` of the main checkout,
shared by every worktree, never committed and not removed with a worktree. It holds:

- `ask.txt` and `task.md`: the owner's words as given, and the ask with its outcome. `ticket.txt`
  holds the id of the tracker's ticket, for a task that came from one, and `ticket-steps.txt` what
  Lem did to that ticket; `lem project tasks` gives both, and `ticket_owed`: what an ended task's
  ticket still waits for.
- `session.md`: the first thing a task's session reads, which `lem session open` writes: the task,
  its phase, why the session opened, and where it works.
- `handoff.md`: what the agent that leaves a phase, or trips the breaker, leaves for the next one,
  in the form of `templates/handoff.md`: what is settled, what is open, the next step, what failed,
  and each file it changed with its status. The state is newer than an old handoff, and wins.
- `talk.md`: the turns of the session where the owner typed the request, word for word, which
  `lem session talk` copies. Like every file here, it never reaches git or a pull request.
- `interview-notes.md`: each answer of the owner's that sets the outcome, one line each, which
  the interview writes as it comes, so that a session after it asks nothing again.
- `criteria-read.md`: the personas' answers of the read of the criteria, each persona and family
  with its words, which the interview writes beside its `criteria.read` event, so that a
  session after it puts his page up from it with no second read.
- `scout.md`: the scout's report of the interview, facts of the code around the ask, which only the
  criteria use.
- `investigation.md`: the investigator's report of a bug or a question: reproduced or not and
  how, the cause and its place or the answer, what else the cause reaches, and its call of what
  follows (`prompts/investigator.md`). It stands in for the scout's report in the interview of a
  bug.
- `directions.md`: what the owner named in the interview or in the talk before it (a technology, a
  library, an approach, an option he picked), one line each in his words. The plan follows it.
- `outside.md`: the defects outside the request that the interview found, one line each with its
  place. The landing's polish pass fixes or files each one.
- `criteria.json`: the criteria the owner approved, word for word, with a digest, who approved them
  and when, and the number of the approval, with the earlier approvals under `history`. For a
  task on the standard track from a complete request the lead's read freezes them there too (`by: read`), which is never his yes. Only `lem criteria approve` writes it; `lem criteria approved SLUG` prints it, and the
  plan's criteria must be those, with the test lines added.
- `criteria.md`: the criteria as the interview writes them for his yes. On the fast track it is the one
  criterion, approved in his name, with the test line its builder adds under it, and it stands in
  for a plan: a task on the fast track commits no plan, and `criteria.py` and `land.py` read the criterion
  here when the branch has no plan file. On the standard track the criteria are read only from its plan.
- `brief.md`: the lead's brief, or the fast track's builder's; `talk-brief.md`, the defender's.
- `state.md`: newest block first, written only through the script.
- `report.md`: what the lead did, rewritten whole at each stop. `stages/build.md` gives its form.
- `decisions.jsonl`: each decision taken without the owner, each breaker and his help on it, one
  line for each thing that happened, and each change of an approved criterion with its text before
  and after. Written only through `scripts/decisions.py`; `lem decisions list SLUG` shows each
  decision as it stands, and `lem decisions changes SLUG` the criterion changes with the criteria
  they give.
- `breaker-N.md`: the document a lead that tripped breaker N leaves for the owner, which the lead
  writes as `breaker.md` and the record keeps under its number (`stages/breaker.md`); `resumed-from.txt` names the dropped task a resumed one came from
  (`stages/park.md`).
- `reports/`: one file per builder of a plan's task, which the lead reads.
- `landing.json`, `polish.json`, `gate/`, `read.json`, `reviews/`, `notes.md`, `pr.md`,
  `merge-brief.md` and `merge-review.md`: what the landing keeps: its own record, what the polish
  pass was given, the output of each command of the checks, what each review was given and what it
  found, the notes for the pull request, its text, and the merge agent's brief and review.

The plan of a task on the standard track is a file in the repository, in the settings' `plans` path.

A file that a later step needs (the inputs of a measurement, a probe's output, a benchmark's
kit) goes in the task directory too, never in `/tmp` or a session's scratch folder, which may be
gone when a later task needs it.

```bash
lem project state SLUG STATUS "one line" ["a further line" ...]
```

It puts a block at the top of `state.md` with the clock's time. Write one at every stage boundary
and before you stop. It refuses a move out of an ended state, a lead's state (`queued`,
`building`, `planned`, `ready`) over a task in `landing` or `open`, and any state but `dropped` over a
parked one: such a write is an agent that woke late, and `lem project resume` is the way out of `parked`. A landing that must start over is the one case, and `land.py` gives its
command when it is one. The status says who acts next, and the phase of the task's session:

| Status | Means | Who acts |
| --- | --- | --- |
| `queued` | the ask is written and nothing builds it: it needs the result of the task its `after:` line names | the board's server opens its session when that task ends |
| `building` | a lead plans or builds, or an investigator examines a bug or a question | the task's session |
| `planned` | the plan is committed and nothing builds it: the plan talk runs, or the owner reads the plan | the defender, or the owner |
| `held` | it waits for the owner: the interview, the criteria that wait for his yes, one more fact an investigation needs, a step that is his to do, or a breaker's document (`breaker N waits for the owner`); no choice of a build waits for him | the owner, in the task's session |
| `blocked` | the lead stopped on something it could not settle | the task's session, or the owner |
| `ready` | the report is written and the branch waits for its checks | the landing's session |
| `landing` | the checks and the review run on it, or a builder repairs what they showed | the landing's session |
| `open` | it is proposed: its pull request is open on GitHub | the merge agent reads it and merges it; the owner, when it calls him |
| `landed` | it is on the base branch | its session, for the cleanup |
| `dropped` | nobody will build it | nobody |
| `answered` | it ended with a report and nothing to merge: a question answered, or a bug that is none | nobody |
| `parked` | the owner put it aside (`/lem park`): its worktree, branch and files stay | nobody, until his `/lem resume` |

Every state block is also an event in the log the board draws, with the newest commit of the
task's worktree, so the board needs no second command from anyone. Six lines have a fixed form,
because the board reads them: `lead: builder` (a lead plans or builds) or `lead: session` (the plan
talk's pair runs), `small change: one builder` (the fast track's one builder, which is no lead),
`plan committed` with `N tasks`, `task N of M`, `investigation: bug` or `investigation: question`
(an investigator works before any lead), and `type: TYPE, because WHY`, which `state` refuses in
another form. No state line names a session: `lem session` logs `session.open`, `session.close`
and `session.wake`, and the board knows each task's session from them.

A stage's start is an event too, so that the board's time card has a start and an end for each
span (the owner's pick of 2026-11-17). Each has a fixed form that `lem project log` checks, and
the event that already ends the stage ends it. Logged by the agent that runs the stage, where its
stage text says: `interview.start` (before the first question; it ends at the first
`criteria.read.start` or `criteria.approved` after it), `scout.start` and `scout` (as the
scout starts and when its report is written), `criteria.read.start by=lem|lead` (it ends at
`criteria.read`), `investigation.start type=fix|question` (it ends at `investigation`), and
`builder.start job=JOB` for a builder's job, `task N of M`, `the small change` (the fast track's builder), `the repair of a
conflict with the base`, `the repair of a failed check` or `the fix of a review's findings` (it
ends at the next state block or step of the landing). Logged by `land.py` itself:
`polish.start before=TIP` (it ends at `polish`), `gate.start tip=TIP commands:=N`, the start of
the checks (it ends at `gate.end`) and `review.start attempt:=N floor=KIND`, once for the
attempt that is due (it ends at `review`). `plan.talk.start` and `plan.talk` have the same pairing.

Nothing else keeps a task's place. A session that was compacted or opened fresh reads the state
first, then `handoff.md` where it is newer, then the report, and goes on. No session keeps notes of
its own beside these files.

## The board

```bash
lem board             # the board of all tasks
lem board --task SLUG # the board of one task
```

The board is the machine's board server, `lem serve`, which draws it from the state folder at each
request and tells an open page each change, so it updates by itself. `lem board` makes sure the
server runs and opens the board's address, `http://127.0.0.1:PORT/HOST/WORKSPACE/` (a task's is
`.../tasks/SLUG`), as a page beside the session that opened it. It has four views (keys T, W, B and
A): "Tasks", each task in the column of who acts on it; "Waits for you", one row for each thing the
owner does, with where he does it, and "no session" for a task whose session is gone while it needs
one; "Backlog", the items of the backlog path by their own `worth`, each with "start a task", which
opens a task's session through the server; and "Activity". A task opens in a panel beside the view,
with its tabs "Overview", "Criteria and decisions", "Checks and review", "Timeline" and
"Artifacts", and a button that opens its session when none runs. With the tailnet door on (`/lem
serve tailscale`, docs/board.md), the owner opens the same board on his phone at the address `lem
board --no-open` prints as `tailnet_url`. When the server does not run, the board does not load,
and the next `lem` command of any session starts it.
