# task-skills

One entry point for a unit of work, the same in every repository: `/task new`, `plan`, `build`,
`land`, `review`, `status`, `learn`, `retro` and `init`. The flow lives here. What differs between
projects lives in each project's repository, where `/task init` writes it.

**State: a first version.** No real task has run through it, there is no installer, and the
contract is written for Claude Code only. `task-skills` is a working name.

## How it works

- **Build first, review after.** A builder writes a short plan and builds it; machine checks gate
  the landing; the landed change joins a review queue. Paths the project calls careful keep a
  second opinion on the plan and a review of each task.
- **The review queue is honest.** A high-risk landing is due the day it lands. A normal item
  nobody read in seven days is closed as "not reviewed" and reported, so unread changes are a
  number someone sees.
- **The owner is needed at three points**: the ask, a decision whose options each cost a person
  something, and the report. Every other decision is taken, logged and listed for the owner to
  overturn.
- **A correction edits the file that owns the step**: a stage of this skill, a style guide file,
  a persona, a review lens. Notes read at session start do not hold.
- **Stages name capabilities, not tools**, so another agent is one more file in
  `skills/task/harness/`.

## What a project keeps

`/task init` checks the machine, examines the repository, interviews the owner and writes
`.agents/project.toml` with draft profiles:

```
.agents/
  project.toml   paths, base branch, who lands, gate commands, careful paths
  profile.md     what the project is
  styleguide/    how code is written here, by path
  personas/      the people a decision affects
  review/        the review tool's lenses, profile and rejected findings
  lessons.md     corrections with no better file
```

A repository that already keeps some of these for an older tool (`.claude/rules`, `.revmux`,
`.personas`) may link them instead: the settings file points at them and nothing moves.

## The machine

`python3 skills/task/scripts/doctor.py` says what is there. Required: git, Python 3.11 or newer,
and [revmux](https://github.com/umputun/revmux) for the review rounds. Optional, each with a
plain fallback: agterm and its skill, huddle, Codex, `mailbox-chat.py`, cronn.

## Trying it in Claude Code

Link the skill from a clone, so an edit here is what the next session reads:

```bash
ln -s "$PWD/skills/task" ~/.claude/skills/task
```

## Tests

```bash
bash tests/test-task.sh
```
