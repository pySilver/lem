---
name: lem
description: "Lem coordinates the work of coding agents in one repository: `/lem new`, `plan`, `build`, `land`, `night`, `status`, `reviewer`, `learn`, `retro` and `init`, or `/lem` followed by an ask in plain words. One Lem per repository takes the asks, gives each task to a lead in a context of its own, and takes one branch at a time through the machine checks and a review to a pull request that says green or not green. It reads the repository's own settings (`.lem/project.toml`: style guide, personas, review configuration, lessons, gate, careful paths), and gives what the project calls careful the full review and a person's merge. Use when the user says \"lem\", \"/lem\", \"lem new\", \"lem status\", \"lem land\", \"lem night\", \"lem init\", \"lem retro\", \"ask Lem\" or \"tell Lem\"."
---

# Lem

One command carries a unit of work from the ask to a pull request that says whether it is green,
the same way in every repository. What differs between repositories is in the repository: its settings file names
the style guide, the personas, the review configuration, the lessons, the checks that gate a
landing and the paths that need more care. This skill holds the flow and knows no project.

The owner is a developer whose attention is short, so the flow asks for it at few places: the
interview when the ask is unclear, the stories, which are the contract in plain language and
become the tests, and the pull request, which he merges without a read when it is green. Between
those a task builds without him. Before a change is proposed it passes the machine checks and a
review by an agent that did not build it, as large as the change needs. Nothing is reviewed after
the merge: in one repository 43 of 48 reviews queued after the landing were still open about 28
hours later (convertiser-server, 2026-11-14). And nothing is argued task by task: three days of a
plan argued before the build and a review of each task produced 37 commits, none in the
application (the same repository, measured 2026-11-13). The price of one review at the end is
not measured: a review of each task found a must-fix on 184 of 414 tasks in another repository
(mybaze, 2026-11-11), and nobody sorted those into defects a user would meet and the rest. So
the event log keeps each review's rounds and counts, and each request that was not green with
its reason.

## Two levels

**Lem** is the one session of a repository in which the owner types `/lem`. It takes the asks,
opens the tasks, starts each task's lead, takes one branch at a time through the checks and the
review to a pull request, and tells the owner. It holds no task's details. Of a task it reads three things: the ask it wrote
down, the newest state block and the report file. It does not read the plan's reasoning, the diff
or what a builder printed, and it writes no code. Lem is the only context that knows every
task. When it fills with one task's code, it loses the others.

**A task's lead** owns one task from its plan to its report, in a context of its own:

- **a builder**, for a plain task: one fresh agent that writes the plan. A plan of one task it
  builds itself. For a plan of more tasks it starts one fresh builder for each task, reads their
  reports and writes no code;
- **a session**, for a careful task: an agent in a session of its own, with the reviewer in its
  other pane. It starts the builders the same way, and each task of its plan is
  reviewed before the next.

Each task of a plan gets a builder with a context of its own, whoever leads. Every task starts
with a builder as its lead, unless the owner calls it careful in the ask. The plan says which of
the two it is (`stages/plan.md`), because only the plan names the files. A lead answers to Lem
and never asks the owner, so the owner has one place to answer.

A lead's standing brief is `prompts/lead.md`. If your first message named that file, you are a
lead: your stages are `stages/plan.md` and `stages/build.md`, and the subcommands below are
Lem's. When the owner types `/lem` in a lead's session, say that the ask belongs in Lem's
session, and change nothing.

## Before any subcommand

`/lem` runs inside agterm only: the reviewer's pane, the pages for the owner and the mailbox
between the two agents are agterm's. When `AGTERM_SESSION_ID` is not set, say that the session
must be started in agterm, and stop.

```bash
python3 SKILL_DIR/scripts/project.py show
```

`SKILL_DIR` is this skill's own directory. The output is the project's settings, resolved: each
path with whether it exists, the base branch, who lands, the gate commands and the careful
patterns. When `settings` is null the repository was never onboarded: only `init` and `status`
run, and every other subcommand says so and stops. Read the project's `AGENTS.md` once per
session; it is where a project says what its own scripts are (a worktree script, a landing
script, a board).

## Subcommands

Read the stage file when the subcommand runs, and follow it. Do not read the others.

| Subcommand | Does | Read |
| --- | --- | --- |
| `new <what>` | opens the task (its worktree, its branch, the ask in the owner's words) and starts its lead. `<what>` may be a tracker's ticket, by its id or its URL | `stages/new.md` |
| `plan <what>` | as `new`, and the lead stops at the committed plan for the owner to read | `stages/new.md` |
| `build [<task> or <plan file>]` | starts a lead on a task whose plan waits: a night draft, a plan the owner read. With no name it lists those tasks and asks which | `stages/new.md` |
| a lead stopped | its reply or its message arrived: act on the task's newest state | `stages/new.md` |
| `land` | the oldest ready task: the machine checks, the review, then a pull request that says green or not green, or a branch ready to land where there is no forge. `land <task>` on the owner's word merges an open one | `stages/land.md` |
| `annotate <file>` | opens a plan, a draft or any text file for the owner to mark up, with what the settings' `tools.annotate` names, and takes his notes as corrections | the harness file, `show-page` |
| `learn`, `retro` | a correction becomes an edit of the file that owns the step | `stages/learn.md` |
| `init` | onboarding: checks the machine, examines the project, interviews the owner, writes the settings and the draft profiles | `stages/init.md` |
| `night` | unattended: picks a backlog item that needs no decision and leaves its plan for the morning | `stages/night.md` |
| `status`, bare `/lem` | the board of all tasks, and in words: every open task, what is proposed and what waits for the owner | below |
| `status <task>` | the board of one task | below |
| `reviewer AGENT [MODEL [EFFORT [PLAN_EFFORT]]]`, `reviewer default` | who sits in the reviewer's pane on this machine for now, and the project's own reviewer again: `project.py reviewer` with the same words. Say what `project.py show` then gives as the seat | the harness file, `second-opinion` |
| a call of a skill Lem ships | `/lem interview-me` loads `lem-interview-me` (`load-skill`) and gives it the rest of the line as its arguments. The owner calls `interview-me`, `backlog`, `release`, `last-tag`, `pr-review`, `dialectic` and `root-cause` this way; `ask`, `gate` and `panel` load the same way, and Lem's stages use those by themselves. See below for a line that only starts with such a word | that skill |
| anything else | an ask in plain words: `/lem the report dates must stay whole` is `new` with that sentence | `stages/new.md` |

A skill's name at the start of a line does not make the line a call of that skill. It is a call
when the name stands alone or is followed by what that skill takes: a slug, a path, a number, a
statement to argue. `/lem release notes are wrong on the site` and `/lem backlog is slow to open`
are sentences about the project, so each is an ask and opens a task. `/lem ask` takes a question
the owner wants put to himself as a page ("`/lem ask` which of the two layouts"); "`/lem` ask
the payment provider for a sandbox key" is a task. When you cannot tell which
of the two a line is, ask the owner once in the terminal, in one line, before anything runs: a
skill such as `lem-release` changes files.

A task runs on from `new` to its pull request without the owner, unless a stage file names a stop.
Between two of the owner's messages Lem only waits: a lead that stops wakes it.

## What holds in every stage

- **The owner is needed at three points.** The ask (`new`), a held decision, and the pull request.
  A held decision is one whose options each cost a person something and that no ruling, test or
  probe answers; it goes through the question gate and the persona panel before the owner sees
  it. The panel asks the project's own personas, which every project of Lem has. Every other decision is yours: decide from the code, the settings and the rulings, write it
  in the decisions log, and go on. A red test, a failed command or a moving base branch is the
  work, never a reason to stop. A choice in the build that the personas leave unclear waits for
  the owner the settings' `flow.decision_wait` at most, 15 minutes unless the project says
  otherwise; then the lead takes the recommended option and the pull request is not green for
  it. A step that a later "no" cannot reverse is the one exception: it waits for his word, and
  the rest of the plan goes on (`stages/build.md`, "A choice in the build").
- **Decisions are logged, and the owner can overturn each.** Each decision made without the
  owner, each choice that went to him and his answer, through `scripts/decisions.py`: what, what
  was chosen, by whom, why, and what it would take to undo. It writes `decisions.jsonl` in the
  task's directory and an event for the board; nobody writes that file by hand. The report lists
  them as decisions, never as questions, and the pull request lists each one from the record.
- **A destructive or outward step is never yours.** Dropping data, rewriting shared history,
  touching production, bending a gate, pushing to a branch the settings do not name: stop and
  ask, with the evidence.
- **What must not go wrong takes the careful flow.** The project names it two ways: paths
  (`project.py careful FILE...` says which files of a change match) and danger topics in the
  owner's words (`flow.topics`), which the lead reads a plan against. One match of either makes
  the task careful: a session leads it, its plan is read by a second opinion before the build,
  and each of its tasks is reviewed before the next. The lead writes its call and the one
  sentence of why into the plan, its state and its report, and the owner may overrule a "no"
  at any time before the landing.
- **Only so many tasks build or land at one time.** `project.py may-start` exits 1 at the
  settings' `flow.max_tasks`; it counts the tasks in `building` and the one in `landing`, where
  the gate runs and a builder may repair what it showed. Four to five tasks ran well on one Mac, and six gave a load average of 12 to
  16 and unstable browser tests (convertiser-server, as its owner reported it on 2026-11-14). A
  task over the limit is queued, never started "just this once"; only the owner raises the limit.
- **What the owner has to understand is told as one run.** A decision you bring and a confusion
  the owner brings ("I thought X did Y", "why is this happening") get the same form: one
  concrete case in numbered steps, with real names and values, and where each step was read. For
  a confusion, find out what the code does first; about half the time the owner's instinct is
  right and it is a defect, so say which of the two it is before changing anything. For a
  decision, `stages/plan.md` says what follows the run.
- **Numbers carry their source.** A count is a command's output, a time is `date -u`, a test
  result is the exact last line of the run. One coordinator made four factual errors in owner
  reports in its first 28 hours: clock values it estimated, a count and a claim about the gate.
- **A brief is checked before it is sent.** A builder copies a wrong sentence from its brief into
  the code and into its report. Before a brief goes out, every sentence about the code is one you
  read in the code, and a sentence with "never", "always" or "the same" gets its counterexample
  looked for first.
- **Capabilities, not tools.** A stage says `spawn-builder`, `open-task-session`,
  `tell-coordinator`, `second-opinion`, `ask-owner`, `fan-out`, `show-page` or `load-skill`, and
  names the question gate, the persona panel and the review tool by role. Read, once per session, the file in this skill's `harness/` folder named
  after the agent you run in (`harness/claude-code.md`); it says what each means there. When
  there is no file for your agent, say so and stop: the contract was not checked in it.

## Where a task keeps its state

```bash
python3 SKILL_DIR/scripts/project.py task-dir SLUG
```

It makes and prints the task's directory inside the repository's git directory, shared by every
worktree, never committed and not removed with a worktree. It holds:

- `ask.txt` and `task.md`: the owner's words as given, and the ask with its outcome. Lem writes
  them. `ticket.txt` holds the id of the tracker's ticket, for a task that came from one, and
  `ticket-steps.txt` what Lem did to that ticket; `project.py tasks` gives both, and
  `ticket_owed`: what an ended task's ticket still waits for.
- `brief.md`: the lead's brief. Lem writes it.
- `state.md`: newest block first. Lem and the lead write it, and only through the script.
- `report.md`: what the lead did and what it leaves to Lem, rewritten whole by the lead that
  stops. `stages/build.md` gives its form.
- `decisions.jsonl`: each decision taken without the owner, each choice that went to him and his
  answer, one line for each thing that happened. Lem and the lead both write it, and only
  through `scripts/decisions.py`; `decisions.py list SLUG` shows each decision as it stands.
- `reports/`: one file per builder of a plan of more tasks. Lem does not read these.
- `landing.json`, `gate/`, `read.json`, `reviews/`, `notes.md` and `pr.md`: what the landing
  keeps: its own record, the output of each gate command, what each review was given and what
  it found, Lem's notes for the pull request, and the text of the pull request.

The plan itself is a file in the repository, in the settings' `plans` path.

A file that a later step needs (the inputs of a measurement, a probe's output, a benchmark's
kit) goes in the task directory too, never in `/tmp` or a session's scratch folder. One run's
measurement kit was gone from the disk when a later task needed it, and the task built it again
(mybaze, 2026-11-03, from that project's notes).

```bash
python3 SKILL_DIR/scripts/project.py state SLUG STATUS "one line" ["a further line" ...]
```

It puts a block at the top of `state.md` with the clock's time. Write one at every stage boundary
and before you stop. The status says who acts next:

| Status | Means | Who acts |
| --- | --- | --- |
| `queued` | the ask is written and no lead runs: the limit was reached | Lem, when a lead stops |
| `building` | a lead plans or builds | the lead |
| `planned` | the plan is committed and nothing builds it | Lem opens a session, or the owner reads the plan |
| `held` | it waits for the owner: a held decision | the owner, through Lem |
| `blocked` | the lead stopped on something it could not settle | Lem |
| `ready` | the report is written and the branch waits for its checks | Lem |
| `landing` | the checks and the review run on it, or a builder repairs what they showed | Lem |
| `open` | it is proposed: a pull request is open, or the branch is ready to land | the owner merges; Lem, where the project lets an agent merge a green request |
| `landed` | it is on the base branch | nobody |
| `drafted` | a plan written at night that waits for the owner's word | the owner |
| `dropped` | nobody will build it | nobody |

Every state block is also an event in the log the board draws, with the newest commit of the
task's worktree, so the board needs no second command from anyone. Four lines have a fixed form,
because the board reads them: `lead: builder` or `lead: session`, `session: ID`, `plan committed`
with `N tasks`, and `task N of M`.

Nothing else keeps a task's place. A session that was compacted or replaced, Lem's or a lead's,
reads `project.py tasks`, then the state file and the report of the task it acts on, and goes on.
Lem keeps no notes of its own beside these files.

## Status

```bash
python3 SKILL_DIR/scripts/board.py             # the board of all tasks
python3 SKILL_DIR/scripts/board.py --task SLUG # the board of one task
```

The board opens as a page beside the sessions it shows, under Lem's session or under the top of
its group, and stays there: each task in the lane of who acts
on it, with its lead, its newest commit, its gate result, its newest review and, once it is
proposed, green or not green; and where each task's time went. A task's own board adds its
state blocks, each gate command and each review with who answered.
It reads the event log by itself every two seconds, so open it once, and again after agterm was
started again.

A task's own board also shows its stories, as the top of its plan has them: each with the tests
that hold it and what the last check of those tests gave. `python3 SKILL_DIR/scripts/stories.py
show SLUG` prints the same. The stories are what the owner reads of a task; the rest of the plan
is the agents'. For a status of one task, say its stories in his words before anything else.

The board of all tasks has a second tab, the backlog: the items of the backlog path in groups by
who can act on each (when the `lem-backlog` skill's sorting has verdicts, by each item's own
verdict otherwise), with an item whose place in the code is gone marked as such. An item's one
action there, "start a task", types `/lem new PATH` into Lem's session, which is the ask
`stages/new.md` takes for a backlog item; the owner confirms it on the page first. `board.py`
writes the tab's file at every run, and the page reads it when the tab opens and on a key. So
after an item was filed, taken or removed, run `board.py --no-open`, which writes the file again
and opens nothing.

Every project of Lem has personas, and a project without them has an onboarding that is not
finished. The machine check (`python3 SKILL_DIR/scripts/doctor.py`), run in the repository, has
a `project personas` row that says how many the panel finds, from the checkout or the default
branch. Look at it with the status: with none, say so and name the step, `/lem init`, which
asks who a decision here affects and writes them without touching the settings that exist; with
one, say that a panel needs a second person who would notice other things.

Then say the same in words. `python3 SKILL_DIR/scripts/project.py tasks` lists every task
directory with the first line of its `task.md`, its status and the newest block of its
`state.md`. Say, in plain names and never in task codes: what builds and what each other task
waits on, what landed today, and what
waits for the owner. That includes each `open` task: its pull request's address, or that its
branch is ready to land, and green or the reasons it is not, as the newest state block has
them. It includes each choice of a build that waits for him, as `python3
SKILL_DIR/scripts/decisions.py pending` lists them under `waiting`: the task, the choice, and the
minutes its wait has left, or that it waits for his word. A dropped or landed task has no
choice that waits. A task whose status is null has a state nobody wrote through the script: say
so. A task with a `ticket_owed` ended, and its ticket in the tracker does not say so yet: say
that too. Open with the newest night report when one is newer than the last status shown. The status
itself changes nothing.
