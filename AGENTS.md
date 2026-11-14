# task-skills

The `task` skill: one flow for a unit of work in any repository, with each project's settings kept
in that project's repository. `README.md` says what it does; this file says how to change it.

## Rules for a change here

- **The skill knows no project.** No repository, product, path or person of a real project appears
  in `skills/task/SKILL.md`, the stage files, the harness files or the templates, except as the
  dated source of a measurement ("convertiser-server, 2026-11-14"). What a project needs to say,
  it says in its own `.agents/` folder or its own `AGENTS.md`.
- **A stage names a capability or a role, never a tool.** `spawn-builder`, `second-opinion`,
  `ask-owner`, `fan-out`, `show-page`, `load-skill`; the question gate, the persona panel, the
  review tool. `skills/task/harness/README.md` is the contract. A tool's name belongs in the one
  harness file of its agent. A skill this repository ships is named by its name, which is the
  same in every agent.
- **A harness file exists only for an agent the contract was checked in.** Do not write one from
  another project's notes about an agent.
- **A number in a skill file carries its source and date.** A rule that rests on a measurement
  says so; a rule that rests on a guess says that instead (`EXPIRE_AFTER` in `review_queue.py`).
- **One stage file per subcommand, read only when it runs.** `SKILL.md` holds what is true in
  every stage. A rule that one stage needs goes in that stage.
- **Scripts are standard-library Python, 3.11 or newer**, print JSON for an agent to read, and
  refuse a wrong input with exit 1 and a message that names the fix. No silent default for a
  choice that is the owner's (`project.py init --existing`).
- **Documentation describes the current state.** No changelog paragraphs, no "previously".

## Checks

```bash
bash tests/test-task.sh        # the task skill's three scripts, in throwaway repositories
bash tests/test-huddle.sh      # huddle's spec checks and every template; loads pages in headless Chrome when one is installed
shellcheck tests/*.sh
```

A change to a script comes with its test. A change to a stage file has no test: its test is a
real task, so say in the commit which task showed the need.

## Layout

- `skills/task/SKILL.md`: the entry point and what holds in every stage.
- `skills/task/stages/`: one file per subcommand.
- `skills/task/harness/`: the capability contract and one file per agent.
- `skills/task/scripts/`: `project.py` (a repository's settings and task state), `doctor.py`
  (the machine), `review_queue.py` (landed changes that wait for a review).
- `skills/task/templates/`: the shapes onboarding fills.
- `skills/huddle/`, `skills/webrev/`, `skills/backlog/`, `skills/interview-me/`, `skills/dialectic/`,
  `skills/root-cause-investigator/`: the skills the task skill names and ships. `NOTICE` says where
  each came from.

## The shipped skills are copies, not yet under the rules above

Each was copied from where it worked and changed only as far as the new layout needed. Their text
still names Claude Code's tools, `skills/backlog` and `skills/webrev` use `${CLAUDE_SKILL_DIR}`,
and huddle's Stop hook (`skills/huddle/hooks/hooks.json`) is registered by nothing. Bring one under
the capability rule when a second agent has to run it, not before.

The set is deliberately small. A tool with its own life (revmux, agterm, cronn, plannotator, Codex)
is checked for by `doctor.py` and never copied in, and a project that prefers its own tool for a
role says so in its settings or its `AGENTS.md`.
