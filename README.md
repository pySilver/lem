<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/lem-night.svg">
    <img src="assets/lem.svg" alt="Lem: a tall hooded figure holds one line, and four smaller figures and the name hang from it" width="720">
  </picture>
</p>

# Lem

Lem coordinates coding agents. One command, `/lem`, carries a unit of work from the ask to a
landed, reviewed change, the same way in every repository: `new`, `plan`, `build`, `land`,
`review`, `night`, `status`, `learn`, `retro` and `init`. Lem holds the flow. What differs between
projects lives in each project's repository, where `/lem init` writes it.

There is one Lem per repository, in the session where you type `/lem`. It takes the asks, gives
each task to a lead in a context of its own, lands one branch at a time, queues the reviews and
reports to you. It holds no task's details: of a task it reads the state and the report.

The name is Stanisław Lem's. Lem is the one in the middle: it builds nothing itself, it holds the
line the other agents work on, and it answers to you for all of them.

**State: a first version.** No real task has run through it, there is no installer, and the
contract is written for Claude Code only. Lem runs inside [agterm](https://agterm.com) and
nowhere else.

## How it works

- **Build first, review after.** A builder writes a short plan, and each task of the plan gets a
  fresh builder; machine checks gate the landing; the landed change joins a review queue. A task
  on paths the project calls careful gets a session of its own with a reviewer in its other pane:
  a second opinion on the plan and a review of each task.
- **Only so many tasks build at one time.** The limit is a setting, `flow.max_tasks`; a task over
  it waits in a queue.
- **A board shows all of it.** `/lem status` opens a live page under Lem's session: each task in
  the lane of who acts on it, with its lead, its newest commit, its gate result and its review
  item. `/lem status <task>` opens the board of one task.
- **The review queue is honest.** A high-risk landing is due the day it lands. A normal item
  nobody read in seven days is closed as "not reviewed" and reported, so unread changes are a
  number someone sees.
- **The owner is needed at three points**: the ask, a decision whose options each cost a person
  something, and the report. Every other decision is taken, logged and listed for the owner to
  overturn.
- **A correction edits the file that owns the step**: a stage of this skill, a style guide file,
  a persona, a review lens. Notes read at session start do not hold.
- **Stages name capabilities, not tools**, so another agent is one more file in
  `skills/lem/harness/`.

## What a project keeps

`/lem init` checks the machine, examines the repository, interviews the owner and writes
`.lem/project.toml` with draft profiles:

```
.lem/
  project.toml   paths, base branch, who lands, who reviews and with which model and effort,
                 gate commands, careful paths, how many tasks build at one time
  project.local.toml   this machine's own reviewer for now; git does not track it
  profile.md     what the project is
  styleguide/    how code is written here, by path
  personas/      the people a decision affects
  review/        the review tool's lenses, profile and rejected findings
  lessons.md     corrections with no better file
```

A task's worktree goes under `.lem/worktrees/`, which git ignores, and its state (the ask, the
state blocks, the report, the decisions) inside the git directory, where it outlives the worktree.

A repository that already keeps some of these for an older tool (`.claude/rules`, `.revmux`,
`.personas`) may link them instead: the settings file points at them and nothing moves.

## What comes with it

An opinionated set, kept small. Each shipped skill has the id `lem-<name>` and runs as
`/lem <name>`.

The ones you call:

| Command | For |
| --- | --- |
| `/lem interview-me` | an unclear ask, and the onboarding interview: one question at a time, each with a guess |
| `/lem backlog` | deferred work, one file per item |
| `/lem dialectic` | a claim argued both ways before a decision rests on it |
| `/lem root-cause` | a defect nobody can explain after two tries |
| `/lem webrev` | a document you mark up in an agterm overlay |
| `/lem release`, `/lem last-tag` | cutting a release with notes, and what changed since the last one |
| `/lem pr-review` | reviewing a pull request or an issue and drafting the comment |

The ones Lem uses by itself:

| Skill | For |
| --- | --- |
| `lem-huddle` | every question that asks you to choose or approve, as a page with the options side by side |
| `lem-gate` | whether a question reaches you at all: a ruling, a probe or the agent may answer it |
| `lem-panel` | the people a decision affects answer it first, from the project's own cast |

Not shipped, and checked for by `python3 skills/lem/scripts/doctor.py`. Required: git, Python
3.11 or newer, [revmux](https://github.com/umputun/revmux) for the review rounds, agterm with
its skill, and `mailbox-chat.py` from agterm's cookbook, which carries the messages between the
coordinator and the reviewer in the other pane. Optional, each with a fallback the check names:
plannotator (recommended), Codex, jev and cronn.

The agent that runs `/lem` coordinates and its builders build. The reviewer's pane holds Codex or
a second Claude, as the project's `[seats.reviewer]` says; `/lem reviewer claude` changes that on
one machine, for a day when the usual reviewer is down, and `/lem reviewer default` ends it. A Codex that runs `/lem` itself waits for
its harness file. A project that prefers its own tool for a role points its settings at it.

## Trying it in Claude Code

Link the skill from a clone, so an edit here is what the next session reads:

```bash
for d in "$PWD"/skills/*/; do ln -s "${d%/}" ~/.claude/skills/"$(basename "$d")"; done
ln -s "$PWD/skills/lem-huddle/bin/huddle" ~/.local/bin/huddle
```

A skill of the same name that a plugin already provides has to be switched off first.

## Tests

```bash
bash tests/test-lem.sh
bash tests/test-gate-panel.sh
bash tests/test-huddle.sh
```
