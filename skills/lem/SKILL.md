---
name: lem
description: "Lem coordinates the work of coding agents in one repository: `/lem new`, `plan`, `build`, `land`, `night`, `status`, `reviewer`, `learn`, `retro` and `init`, or `/lem` followed by an ask in plain words. One Lem per repository takes the asks, gives each task on the standard track to a lead and each task on the fast track to one builder, each in a context of its own, and takes one branch at a time through the machine checks and a review to a pull request that says green or not green. It reads the repository's own settings (`.lem/project.toml`: checks, what must never go wrong, who lands) and its personas, lessons, rulings and rules, and gives a change that reaches what must never go wrong the full review and a person's merge. Use when the user says \"lem\", \"/lem\", \"lem new\", \"lem status\", \"lem land\", \"lem night\", \"lem init\", \"lem retro\", \"ask Lem\" or \"tell Lem\"."
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
checks and one read review it, it has no polish pass, and it waits for nothing but his merge. Every other request takes the standard track, and the flow asks for his attention at
three touches: the interview, while a scout reads the code around his ask; the criteria, which the
personas read before he does and which he approves, so that they are the contract in plain
language and become the tests; and the pull request, which he merges without a read when it is
green. He answers the interview, his yes to the criteria and a choice that waits for him in a
companion of Lem's session, one for each such need, which opens when it waits and closes when he
answered, so that Lem's own session takes his next ask at once. A task on the standard track from a complete request (a ticket that says what is wanted, a settled
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

## Two levels

**Lem** is the one session of a repository in which the owner types `/lem`. It takes the asks,
opens the tasks, starts each task's lead, takes one branch at a time through the checks and the
review to a pull request, and tells the owner. It holds no task's details. Of a task it reads three things: the ask it wrote
down, the newest state block and the report file; and for a bug the investigator's report,
which gives facts of the code for the criteria and nothing else. It does not read the plan's reasoning, the diff
or what a builder printed, and it writes no code. Lem is the only context that knows every
task. When it fills with one task's code, it loses the others.

**A task's lead** is a builder: one fresh agent, in a context of its own, that owns one task from
its plan to its report. It writes the plan, starts one fresh builder for each task of it, also
for a plan of one task, reads their reports and writes no code. A task on the fast track has no
lead and no plan: Lem starts its one builder with `prompts/small.md`, a brief complete in itself,
and the builder's own check of the change against the topics moves the task to the standard track
when the fast track does not fit after all.

**A plan talk's defender** is the agent of a companion session that Lem opens for a careful or
large plan (a plan of more than three tasks), with the reviewer in its other pane. A builder
writes the plan and stops at it; the defender and the reviewer argue it through the mailbox
before any code; the defender repairs the plan, writes down how the talk went, and stops. Lem
closes the companion, and a fresh builder leads the build of the talked plan like any other.

**A need's companion** is a fresh agent in a session under Lem's that `lem companion open` starts
for one thing that waits for the owner, named for it in the sidebar: an interview (`SLUG ·
interview`), criteria for his yes (`SLUG · criteria`) or a choice (`SLUG · choice N`). It reads
its task's files, with the turns of Lem's talk that led to the ask (`talk.md`), does that one need
with him (`prompts/companion.md`), writes his answer through `lem`, tells Lem in one line and
closes. It takes no ask, starts no lead and lands nothing: Lem starts the lead from the record.

Each task of a plan gets a builder with a context of its own. Every task on the standard track starts with a
builder as its lead, also one the owner calls careful in the ask: there is no talk before there
is a plan. The plan says whether it is careful or large (`stages/plan.md`), because only the plan
names the files and the tasks. A lead and a defender answer to Lem and never ask the owner: what
waits for him opens in a need's companion.

A lead's standing brief is `prompts/lead.md`, and a defender's is `prompts/defender.md`, which
`prompts/lead.md` sends it to. If your first message named either file, your stages are
`stages/plan.md` and `stages/build.md` (a defender's, `stages/talk.md` and step 5 of
`stages/plan.md` for the talk's open questions), and the subcommands below are Lem's. When the owner types `/lem` in a
lead's or a defender's session, say that the ask belongs in Lem's session, and change nothing.
If your first message named `prompts/companion.md`, you are a need's companion: follow that file,
whose stages are the ones its need names. A `/lem` typed there is no subcommand of yours, and that
file says what you do with one.

## Before any subcommand

`/lem` runs inside agterm only: the reviewer's pane, the pages for the owner and the mailbox
between the two agents are agterm's. When `AGTERM_SESSION_ID` is not set, say that the session
must be started in agterm, and stop.

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

Read the stage file when the subcommand runs, and follow it. Do not read the others.

| Subcommand | Does | Read |
| --- | --- | --- |
| `new <what>` | opens the task (its worktree, its branch, the ask in the owner's words) and says its track in one line. The fast track: one builder and the landing, and nothing waits. The standard track: opens the interview in a companion, where a scout reads the code, the personas read the criteria and he gives his yes, and starts its lead after it; a ticket or an item whose whole context is written skips the interview. A bug whose cause the ask does not show is investigated first, and a question ends with its answer. `<what>` may be a tracker's ticket, by its id or its URL | `stages/new.md` |
| `plan <what>` | as `new`, and the lead stops at the committed plan for the owner to read. A plan is the standard track's, so the ask takes the standard track, and Lem's line says so | `stages/new.md` |
| `build [<task> or <plan file>]` | starts a lead on a task whose plan waits: a plan the owner read. With no name it lists those tasks and asks which | `stages/start.md` |
| a lead stopped | its reply or its message arrived: act on the task's newest state, and a `held` one opens the companion of what waits for the owner. An investigator's reply is its report | `stages/stopped.md`; an investigator's `stages/investigate.md` |
| a choice waits | the line `lem: SLUG choice N waits` arrived, or `lem companion due` names a choice: open its companion | `stages/choice.md` |
| a companion's line | `lem: SLUG criteria approved` or `lem: SLUG choice N answered` arrived from a need's companion: a wake-up, and the fact is `lem companion due`; `lem: the owner is away` or `back` is his word, typed there | `stages/stopped.md`; away or back, `stages/away.md` |
| `im-away`, `im-back` | the owner says that he is away, and every task goes on without him, or that he is back; his word holds in every repository on this machine, so the watch of his mark ends here when he says it in another | `stages/away.md` |
| `be-careful`, `standard-track`, `drop` `[<task>]` | the owner corrects a task: careful until its merge, the standard track until its pull request exists, or not wanted | `stages/correct.md` |
| `land` | the oldest ready task: the polish pass on the standard track (the fast track has none), the checks, the review, then a pull request that says green or not green, or a branch ready to land where there is no forge or the project wants no pull requests (`branch.propose = "merge"`). `land <task>` on the owner's word merges an open one | `stages/land.md` |
| `learn`, `retro` | a correction becomes an edit of the file that owns the step | `stages/learn.md` |
| `init` | onboarding: checks the machine, examines the project, interviews the owner, writes the settings and the draft profiles | `stages/init.md` |
| `night` | unattended: takes backlog items, the smallest first, four at most (`/lem night N` takes N), and runs them one after another without the owner, each to its pull request | `stages/night.md` |
| bare `/lem`, `status` | the one list of what waits for the owner, the same every time: each choice of a task, each task whose criteria wait for his yes, each pull request with green or not, those of the night with the night's report, each retro's proposals; and the board of all tasks, with what builds; it opens the companion of each need that waits. A proposal he answers with approve, reject or later, all on one page | `stages/status.md` |
| `status <task>`, `status <task> choice N` | the board of one task, and the companion of what of it waits, or of that one choice | `stages/status.md` |
| `read <ticket>` | reads one ticket of the tracker, by its id (`/lem read MBZ-12`) or its URL, and says what it holds; it opens no task and writes nothing to the ticket. With no tracker in `lem project show`, say that the project has none | the tracker's skill (`load-skill` the one `tracker.kind` names), its "read" |
| `reviewer AGENT/MODEL:EFFORT`, `reviewer default` | who sits in the reviewer's pane on this machine for now, as one seat (`/lem reviewer codex/gpt-6.2-sol:high`; the effort, or the model and the effort, may be left out for the agent's own default), and the project's own reviewer again: `lem project reviewer` with the same words. Say what `lem project show` then gives as the seat | the harness file, `second-opinion` |
| a helper | `/lem interview-me` loads `lem-interview-me` (`load-skill`): read `SKILL_DIR/../lem-interview-me/SKILL.md` by its path and follow it, with the rest of the line as its arguments. In this session plain words start one too, with or without `/lem`: "let's brainstorm this" or "interview me about X" (`interview-me`), "argue both sides of ..." (`dialectic`), "why does this keep breaking" (`root-cause`), "what would the experts say" (`ask-expert`), "how would the users take this" (`panel`). Outside this session a shipped skill never starts by itself. Lem's stages load `ask-expert`, `panel`, `linear`, `lem-ask` and `lem-gate` themselves: Lem opens its question page each time it asks him, and the gate is the first level of the ladder | that skill |
| anything else | an ask in plain words: `/lem the report dates must stay whole` is `new` with that sentence. Words that plainly say one of the rows above go there | `stages/new.md` |

A helper's name at the start of a line does not make the line its call: `/lem root-cause analysis
of the logs is slow`, `/lem panel layout breaks on a phone` and `/lem ask the payment provider for
a sandbox key` are asks, and each opens a task. When you cannot tell a helper from an ask, or one
helper from another, ask once in the terminal, in one line, with your guess first: "Do you want an
interview about this first, before I open a task? (y/n)". Never a page for this.

A task runs on from `new` to its pull request without the owner, unless a stage file names a stop.
Between two of the owner's messages Lem only waits: a lead that stops wakes it, and so do a
lead whose choice waits for the owner, a need's companion that ends, and the end of a command Lem
runs in the background, a task's checks or one of the two watches (Status).

## What holds in every stage

- **The owner is needed at three points.** The interview and his yes to the criteria (`new`), a
  decision in doubt that went past the personas, and the pull request; a task on the fast track needs him at
  its pull request only. He answers the first two in a need's companion, never in your session:
  you open it, say its one line, and go back to his next message. A lead takes a decision in doubt up a ladder of opinions (the gate, the
  personas, the dialectic, the experts; `stages/ladder.md`, the lead's). One that the gate or the
  personas settled is logged: at each of your turns, say each decision taken in a task that runs
  with him since your last turn (`lem decisions list SLUG`), once, in one line, and wait for
  nothing. One that went past the personas is his card (`stages/choice.md`), which waits for
  his answer with no time limit. While he is away (`stages/away.md`) nothing waits for him: the
  ladder's pick is taken, not green. He is away or there for the whole machine: his `/lem im-away`
  in another repository holds here too. A night's task runs without him until it ends, whatever
  his status. A step that a later "no" cannot reverse waits for him in both modes, and so does the
  merge of a task that runs without him. Every other decision is yours: decide
  from the code, the settings and the rulings, write it in the decisions log, and go on.
  A red test, a failed command or a moving base branch is the work, never a reason to stop.
- **At each of your turns, `lem companion due`.** It reads the files and says what you owe the
  needs' companions; nothing opens or starts by itself, and a line from a companion that was lost
  changes nothing it does not see. For each entry of `open`, `lem companion open SLUG --need NEED`
  (with `--choice N` for a choice), and say its `say` line as it is; of `talk`, the copy of the
  talk first (`stages/open-interview.md`), then the open; of `start`, its lead
  (`stages/start.md`, "The queue"); of `close`, `lem companion close SLUG --need NEED --why WHY`
  with the entry's `why`, and of `gone` the same with `--why gone`; of `away`, `stages/away.md`.
- **Decisions are logged, and the owner can overturn each.** Each decision made without the
  owner, each choice that went to him and his answer, through `scripts/decisions.py`: what, what
  was chosen, by whom, why, and what it would take to undo. It writes `decisions.jsonl` in the
  task's directory and an event for the board; nobody writes that file by hand. The report lists
  them as decisions, never as questions, and the pull request lists each one from the record.
- **A destructive or outward step is never yours.** Dropping data, rewriting shared history,
  touching production, bending a check, pushing to a branch the settings do not name: stop and
  ask, with the evidence.
- **No secret goes into a file.** No agent writes a credential, a key or a value from an `.env`
  file or the environment into a file or a commit: a builder writes the project's name for it,
  and the review reads the diff for one (`prompts/review.md`).
- **The pull request is no step to ask about.** `lem land propose` pushes the task's own branch
  and opens or updates its pull request, and you run it without a question. The owner approved
  it when he approved the settings at onboarding: `branch.propose = "pull-request"` is his
  standing word for exactly this. The pull request is the first place he wants to look, and a
  question here stops every task one step before its end. Nothing else leaves the machine without his word: a push to
  another branch, a merge by `land --by owner`, a message to a person.
- **What must not go wrong takes the careful flow.** The project names it as topics,
  sentences in the owner's words of what must never go wrong (`flow.topics`), and no list of
  paths: a list goes stale as the code moves, misses new code, and a branch can edit the list
  that guards it. Whether a change is careful is a judgment against the topics, made three times
  by three agents, and in doubt the answer is careful. Lem reads the ask's words and the
  scout's facts against them, and names a topic in reach in the first line it says to the owner
  (`stages/new.md`); an ask in reach of one never takes the fast track. The fast track's builder
reads its own change against them before it commits (`prompts/small.md`). The lead reads its plan
  against them (`stages/plan.md`, step 2). The fresh agent that reviews the diff before the pull
  request reads the change itself against them and writes its call into the review's record
  (`prompts/review.md`). A careful task's plan is talked through with the reviewer before any
  code, in a companion session of its own (`stages/talk.md`); its tasks are built like
  any others; the landing gives it the project's full review set, and a person merges it. A large
  task, a plan of more than three tasks, gets the companion and the talk too, and a review round
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
  right and it is a defect, so say which of the two it is before changing anything. For a
  decision, the run goes into its ask, with what follows it (`stages/plan.md`, step 5).
- **Numbers carry their source.** A count is a command's output, a time is `date -u`, a test
  result is the exact last line of the run, never an estimate.
- **A brief is checked before it is sent.** A builder copies a wrong sentence from its brief into
  the code and into its report. Before a brief goes out, every sentence about the code is one you
  read in the code, and a sentence with "never", "always" or "the same" gets its counterexample
  looked for first.
- **Only the skills a stage names.** While a stage runs, load only the skills that stage names
  (`load-skill`). An instruction to load every skill that may be relevant, from a hook or a
  personal rule of the developer's, does not apply to Lem's session, its leads and its builders:
  a planning or debugging skill loaded beside a stage has Lem read code and plans by itself, which
  is a lead's work (the compatibility audit, 2026-11-17).
- **Capabilities, not tools.** A stage says `spawn-builder`, `open-task-session`,
  `tell-coordinator`, `second-opinion`, `ask-owner`, `ask-experts`, `fan-out`, `run-in-background`,
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

- `ask.txt` and `task.md`: the owner's words as given, and the ask with its outcome. Lem writes
  them. `ticket.txt` holds the id of the tracker's ticket, for a task that came from one, and
  `ticket-steps.txt` what Lem did to that ticket; `lem project tasks` gives both, and
  `ticket_owed`: what an ended task's ticket still waits for.
- `talk.md`: the turns of Lem's session that led to the ask, word for word, which `lem companion
  talk` copies for the interview's companion. Like every file here, it never reaches git or a
  pull request.
- `companion-NEED.md`: the brief of a need's companion (`companion-interview.md`,
  `companion-criteria.md`, `companion-choice-N.md`), which `lem companion open` writes.
- `interview-notes.md`: each answer of the owner's that sets the outcome, one line each, which
  the interview's companion writes as it comes, so that a companion after it asks nothing again.
- `criteria-read.md`: the personas' answers of the read of the criteria, each persona and family
  with its words, which the interview writes beside its `criteria.read` event, so that a
  companion after it puts his page up from it with no second read.
- `scout.md`: the scout's report of the interview, facts of the code around the ask. The
  interview's companion writes it from the scout's reply, and only the criteria use it.
- `investigation.md`: the investigator's report of a bug or a question: reproduced or not and
  how, the cause and its place or the answer, what else the cause reaches, and its call of what
  follows (`prompts/investigator.md`). The investigator writes it, or Lem from its reply. Lem
  reads it, and it stands in for the scout's report in the interview of a bug.
- `directions.md`: what the owner named in the interview (a technology, a library, an approach,
  an option he picked), one line each in his words. The interview's companion writes it; the
  plan follows it.
- `outside.md`: the defects outside the request that the interview found, one line each with its
  place. The interview's companion writes it; the landing's polish pass fixes or files each one.
- `criteria.json`: the criteria the owner approved, word for word, with a digest, who approved them
  and when, and the number of the approval, with the earlier approvals under `history`. For a
  task on the standard track from a complete request the lead's read freezes them there too (`by: read`), which is never his yes. Only `lem criteria approve` writes it; `lem criteria approved SLUG` prints it, and the
  plan's criteria must be those, with the test lines added.
- `criteria.md`: the criteria as Lem or the interview's companion writes them for his yes. On the fast track it is the one
  criterion, approved in his name, with the test line its builder adds under it, and it stands in
  for a plan: a task on the fast track commits no plan, and `criteria.py` and `land.py` read the criterion
  here when the branch has no plan file. On the standard track the criteria are read only from its plan.
- `brief.md`: the lead's brief, or the fast track's builder's. Lem writes it.
- `state.md`: newest block first. Lem and the lead write it, and only through the script.
- `report.md`: what the lead did and what it leaves to Lem, rewritten whole by the lead that
  stops. `stages/build.md` gives its form.
- `decisions.jsonl`: each decision taken without the owner, each choice that went to him and his
  answer, one line for each thing that happened, and each change of an approved criterion with its
  text before and after. Lem and the lead both write it, and only through
  `scripts/decisions.py`; `lem decisions list SLUG` shows each decision as it stands, and
  `lem decisions changes SLUG` the criterion changes with the criteria they give.
- `experts/`: for each choice given to the experts, the brief they read (`choice-N.brief.md`)
  and each one's answer (`choice-N.fable.md`, `choice-N.astra.md`), which the `lem-ask-expert`
  skill writes into the record.
- `reports/`: one file per builder of a plan's task. Lem does not read these.
- `landing.json`, `polish.json`, `gate/`, `read.json`, `reviews/`, `notes.md` and `pr.md`: what
  the landing keeps: its own record, what the polish pass was given, the output of each command
  of the checks, what each review was given and what it found, Lem's notes for the pull request, and
  the text of the pull request.

The plan of a task on the standard track is a file in the repository, in the settings' `plans` path.

A file that a later step needs (the inputs of a measurement, a probe's output, a benchmark's
kit) goes in the task directory too, never in `/tmp` or a session's scratch folder, which may be
gone when a later task needs it.

```bash
lem project state SLUG STATUS "one line" ["a further line" ...]
```

It puts a block at the top of `state.md` with the clock's time. Write one at every stage boundary
and before you stop. It refuses a move out of an ended state, and a lead's state (`queued`,
`building`, `planned`, `ready`) over a task in `landing` or `open`: such a write is a
lead that woke late. A landing that must start over is the one case, and `land.py` gives its
command when it is one. The status says who acts next:

| Status | Means | Who acts |
| --- | --- | --- |
| `queued` | the ask is written and no lead runs: it needs the result of the task its `after:` line names | Lem, when a lead stops or that task ends |
| `building` | a lead plans or builds, or an investigator examines a bug or a question | the lead, or the investigator |
| `planned` | the plan is committed and nothing builds it | Lem opens the plan talk's companion, or starts a builder after the talk, or the owner reads the plan |
| `held` | it waits for the owner on what is no decision with options: the criteria that wait for his yes, one more fact an investigation needs, a step that is his to do, or an irreversible choice that every task left depends on | the owner: in a companion for the criteria or a choice, through Lem for the rest |
| `blocked` | the lead stopped on something it could not settle | Lem |
| `ready` | the report is written and the branch waits for its checks | Lem |
| `landing` | the checks and the review run on it, or a builder repairs what they showed | Lem |
| `open` | it is proposed: a pull request is open, or the branch is ready to land | the owner merges; Lem, where the project lets an agent merge a green request |
| `landed` | it is on the base branch | nobody |
| `dropped` | nobody will build it | nobody |
| `answered` | it ended with a report and nothing to merge: a question answered, or a bug that is none | nobody |

Every state block is also an event in the log the board draws, with the newest commit of the
task's worktree, so the board needs no second command from anyone. Seven lines have a fixed form,
because the board reads them: `lead: builder` or `lead: session` (the plan talk's companion),
`small change: one builder` (the fast track's one builder, which is no lead), `session: ID`,
`plan committed` with `N tasks`, `task N of M`, `investigation: bug` or `investigation: question`
(an investigator works before any lead), and `type: TYPE, because WHY`, which `state` refuses in
another form.

A stage's start is an event too, so that the board's time card has a start and an end for each
span (the owner's pick of 2026-11-17). Each has a fixed form that `lem project log` checks, and
the event that already ends the stage ends it. Logged by the agent that runs the stage, where its
stage text says: `interview.start` (the interview's companion, before the first question; it ends at the first
`criteria.read.start` or `criteria.approved` after it), `scout.start` and `scout` (the same, as the
scout starts and when its report is written), `criteria.read.start by=lem|lead` (it ends at
`criteria.read`), `investigation.start type=fix|question` (it ends at `investigation`), and
`builder.start job=JOB` for a builder's job, `task N of M`, `the small change` (the fast track's builder), `the repair of a

conflict with the base`, `the repair of a failed check` or `the fix of a review's findings` (it
ends at the next state block or step of the landing). Logged by `land.py` itself:
`polish.start before=TIP` (it ends at `polish`), `gate.start tip=TIP commands:=N`, the start of
the checks (it ends at `gate.end`) and `review.start attempt:=N floor=KIND`, once for the
attempt that is due (it ends at `review`). `plan.talk.start` and `plan.talk` have the same pairing.

Nothing else keeps a task's place. A session that was compacted or replaced, Lem's or a lead's,
reads `lem project tasks`, then the state file and the report of the task it acts on, and goes on.
Lem keeps no notes of its own beside these files.

## Status

```bash
lem board             # the board of all tasks
lem board --task SLUG # the board of one task
```

The board opens as a page beside the sessions it shows, under Lem's session or under the top of
its group, and stays there. The board of all tasks has three tabs (keys T, W and B): "Tasks", each
task in the lane of who acts on it, with its lead, its newest commit, the result of its checks, its
newest review and, once it is proposed, green or not green, and where each task's time went;
"Waits for you", one row for each thing the owner does, with its verb (answer a choice, approve the
criteria, merge the pull request) and where he does it; and "Backlog". A task's own board has four
(keys 1 to 4): "Overview", which opens with "What we are building" (the goal of its type line, the
outcome of its `task.md`, how many important decisions wait for a look, and the backlog items its
branch filed), then says green or not green with its reasons in plain words, then the large card
and the phases; "Criteria and decisions", each decision one folded row, the important ones (those
that make the pull request not green or went past the personas) marked and first; "Checks and
review", each command of the checks and each review with who answered; and "Timeline", its time
and its activity. It reads the event log by itself every two seconds, so open it once, and again
after agterm was started again. It draws in Lem's own light or dark, in the look of Lem's landing
page, as agterm's theme is light or dark, and outside agterm as the system is.

The tab "Backlog" holds the items of the backlog path in groups by
each item's own `worth`, with an item whose place in the code is gone marked as such. An item's one
action there, "start a task", types `/lem new PATH` into Lem's session, which is the ask
`stages/new.md` takes for a backlog item; the owner confirms it on the page first. `board.py`
writes the tab's file at every run, and the page reads it when the tab opens and on a key; it
writes the file of each task's outcome and filed items at every run too. So when a task starts
(`stages/start.md`, step 2) and after an item was filed, taken or removed, run `lem board
--no-open`, which writes both files again and opens nothing.

Before a status, and at each of your turns, find out what merged. The owner merges and closes
pull requests on the forge, and the forge tells Lem nothing by itself: for each `open` task whose `proposal` in `lem project
tasks` has a `pull_request`, run `lem land merged SLUG`. One that is
merged becomes `landed`, and one he closed with no merge becomes `dropped`; take step 9 of
`stages/land.md` for them (the ticket, `clean`, a conflicting pull request onto the new base), then the
queue, as `stages/start.md` says under "The queue", since a task queued `after:` one may start now. "Not merged yet" is
no news; "not merged yet, and the forge calls it conflicting with main" is: `lem project waiting`
then gives that pull request `conflict: true`, you say "#4 is green by its checks, and conflicts
with main" (or not green, with its reasons), and you take step 9 of `stages/land.md` for it at
once, without waiting for the watch.

While a task is in `landing`, at each of your turns run `lem land checks SLUG --status` too. When
its `overdue` turns true, say its `say` once, with no question. When nothing runs and `ended` is a
run that your session did not start and whose line you did not say yet, take it as
`stages/land.md` says at its top.

While a task is `open` with a pull request, keep one watch of the forge in the background, never
two: `run-in-background` with `lem land watch`. It looks once every
60 seconds with one call for all the pull
requests, reads the list of open tasks again at each look, so that a pull request opened after
it started is watched too, and ends when the owner merged or closed one, or when the forge calls a pull request
conflicting that it did not call so before; its end wakes you, and you take step 9 of
`stages/land.md`, which starts it again while a task is still open. Start it after a proposal
(`stages/land.md`, step 6), and when a session of yours starts while a task is open with a pull
request: a watch that an earlier session started wakes that session, not you. A watch that ends
with exit 1 says why: nothing open to watch, `gh` missing or not signed in (tell the owner that
line once, as it is), no forge in this project, or it was stopped. Start no other one until that
reason is gone. The board says when the forge was last looked at, and that nobody watches when
the watch's last look is older than three of its intervals.

The owner's status is one mark of the machine, which every repository on it reads: his `/lem
im-away` or `/lem im-back` in another repository holds in this one, and nothing tells this
session but a watch. So keep one watch of the mark in the background, from the session's start,
never two: read `owner` of `lem project waiting`, take "When the watch ends" of `stages/away.md`
once when it says away, and `run-in-background` with `lem project owner watch --seen N`, N being
its `seen`, the number of records in the mark. It looks at the mark once every 5 seconds (a guess,
not a measurement) and ends with exit 0 and his status (`away`, `since`, `words`, `seen`) as soon
as the mark holds another number of records than N, at once when it does at its start. Its end
wakes you: take "When the watch ends" of `stages/away.md`, which starts it again. A watch that
ends with exit 1 was stopped, or the mark has a line that does not read (its message names the
file and the line): start no other until that reason is gone. A session that a scheduled job
started (`/lem night`, `/lem retro`) keeps no watch of the mark and takes no step of
`stages/away.md` on it, so two sessions of one repository never both act on one word of his.
