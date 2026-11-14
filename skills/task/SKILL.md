---
name: task
description: "One entry point for a unit of work in any repository: `/task new`, `plan`, `build`, `land`, `review`, `status`, `learn`, `retro` and `init`. It reads the repository's own settings (`.lem/project.toml`: style guide, personas, review configuration, lessons, gate, careful paths), builds first and reviews the landed change from a queue, and keeps the pair flow for the paths the project calls careful. Use when the user says \"task new\", \"new task\", \"task plan\", \"task build\", \"task land\", \"task review\", \"task status\", \"task learn\", \"task retro\", \"task init\", or a bare \"/task\"."
---

# task

One command carries a unit of work from the ask to a landed, reviewed change, the same way in
every repository. What differs between repositories is in the repository: its settings file names
the style guide, the personas, the review configuration, the lessons, the checks that gate a
landing and the paths that need more care. This skill holds the flow and knows no project.

The flow builds first and reviews after. A plan argued before the build and a review of each task
before the next make few defects and little progress: in one repository three days of that loop
produced 37 commits, none in the application (convertiser-server, measured 2026-11-13). The same
repository then landed 67 branches in about 28 hours with one coordinator and about five builders.
The price is known too. Per-task review found a must-fix on 184 of 414 tasks in another repository
(mybaze, 2026-11-11), so those defects now land and wait for the review, and after those 28 hours
43 of 48 review items were still open. Two rules below pay that price down: the project's
careful paths keep the slow flow, and review takes a fixed share of the same day.

## Before any subcommand

`/task` runs inside agterm only: the reviewer's pane, the pages for the owner and the mailbox
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
| `new <what>` | opens the task: its worktree, its branch and the ask in the owner's words | `stages/new.md` |
| `plan` | a short plan as the branch's first commit; a second opinion when the task is careful | `stages/plan.md` |
| `build` | builders do the plan and report to a file | `stages/build.md` |
| `land` | the gate runs; the change lands or waits for the owner; a review item is queued | `stages/land.md` |
| `review` | works the review queue by risk; confirmed findings become tasks | `stages/review.md` |
| `learn`, `retro` | a correction becomes an edit of the file that owns the step | `stages/learn.md` |
| `init` | onboarding: checks the machine, examines the project, interviews the owner, writes the settings and the draft profiles | `stages/init.md` |
| `night` | unattended: picks a backlog item that needs no decision and leaves its plan for the morning | `stages/night.md` |
| `status`, bare `/task` | every open task, the review queue and what waits for the owner | below |

`new` runs on into `plan`, `build` and `land` without stopping, unless a stage file names a stop.

## What holds in every stage

- **The owner is needed at three points.** The ask (`new`), a held decision, and the report.
  A held decision is one whose options each cost a person something and that no ruling, test or
  probe answers; it goes through the question gate and the persona panel before the owner sees
  it. Every other decision is yours: decide from the code, the settings and the rulings, write it
  in the decisions log, and go on. A red test, a failed command or a moving base branch is the
  work, never a reason to stop.
- **Decisions are logged, and the owner can overturn each.** One line in `decisions.md` per
  decision made without the owner: what, why, what it would take to undo. The report lists them
  as decisions, never as questions.
- **A destructive or outward step is never yours.** Dropping data, rewriting shared history,
  touching production, bending a gate, pushing to a branch the settings do not name: stop and
  ask, with the evidence.
- **Careful paths take the careful flow.** `project.py careful FILE...` says which files of a
  change the project's patterns match. One match makes the task careful: its plan is read by a
  second opinion before the build, and each of its tasks is reviewed before the next.
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
- **Capabilities, not tools.** A stage says `spawn-builder`, `second-opinion`, `ask-owner`,
  `fan-out`, `show-page` or `load-skill`, and names the question gate, the persona panel and the
  review tool by role. Read, once per session, the file in this skill's `harness/` folder named
  after the agent you run in (`harness/claude-code.md`); it says what each means there. When
  there is no file for your agent, say so and stop: the contract was not checked in it.

## Where a task keeps its state

```bash
python3 SKILL_DIR/scripts/project.py task-dir SLUG
```

It makes and prints the task's directory inside the repository's git directory, shared by every
worktree, never committed and not removed with a worktree. It holds `task.md` (the ask and the
outcome), `decisions.md`, `state.md` (newest block first: what is running, what is next) and
`reports/`. A session that was compacted or replaced reads `state.md` and goes on; write a block
there at every stage boundary. The plan itself is a file in the repository, in the settings'
`plans` path.

## Status

`python3 SKILL_DIR/scripts/project.py tasks` lists every task directory with the first line of
its `task.md` and the newest block of its `state.md`. Say, in plain names and never in task
codes: what is in flight and what each waits on, what landed today, how many review items are
open and how many are due today, and what waits for the owner. Open with the newest night report
when one is newer than the last status shown. Change nothing.
