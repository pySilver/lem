# Lem

Lem is the `lem` skill and the skills it ships: one flow for a unit of work in any repository, with each project's settings kept
in that project's repository. `README.md` says what it does; this file says how to change it.

## Rules for a change here

- **The skill knows no project.** No repository, product, path or person of a real project appears
  in `skills/lem/SKILL.md`, the stage files, the harness files or the templates, except as the
  dated source of a measurement ("convertiser-server, 2026-11-14"). What a project needs to say,
  it says in its own `.lem/` folder or its own `AGENTS.md`.
- **A stage names a capability or a role, never a tool.** `spawn-builder`, `second-opinion`,
  `ask-owner`, `fan-out`, `show-page`, `load-skill`; the question gate, the persona panel, the
  review tool. `skills/lem/harness/README.md` is the contract. A tool's name belongs in the one
  harness file of its agent. A skill this repository ships is named by its name, which is the
  same in every agent.
- **A harness file exists only for an agent the contract was checked in.** Do not write one from
  another project's notes about an agent.
- **A number in a skill file carries its source and date.** A rule that rests on a measurement
  says so; a rule that rests on a guess says that instead (`EXPIRE_AFTER` in `review_queue.py`).
- **One stage file per subcommand, read only when it runs.** `SKILL.md` holds what is true in
  every stage. A rule that one stage needs goes in that stage.
- **Lem's stages and a lead's stages stay apart.** `plan` and `build` are a lead's; the others
  are Lem's. A step that reads a task's code or its diff goes to a lead or to a fresh agent,
  never into `new`, `land` or `review`.
- **Scripts are standard-library Python, 3.11 or newer**, print JSON for an agent to read, and
  refuse a wrong input with exit 1 and a message that names the fix. No silent default for a
  choice that is the owner's (`project.py init --existing`).
- **Documentation describes the current state.** No changelog paragraphs, no "previously".

## The owner's rulings

Decisions the owner took on 2026-11-14. Each is reopened only by asking him. A quote is his words.

- **agterm is a hard dependency**, and so is the mailbox chat from its cookbook. Lem does not run
  outside agterm.
- **One Lem for one repository.** It coordinates many tasks there. No ability across repositories.
- **Build first, review after.** The persona panel and the review tool with the project's own
  lenses stay; a plan argued question by question and a review of every plain task do not.
- **Claude Code first.** The harness file for Codex comes after that works. The reviewer may be
  Codex or a second Claude; Codex as the builder is wanted later.
- **Opinionated and small.** A developer may use their own tool for a role (`tools.annotate`). Out
  of scope: a peer-planning flow, a skill-activation hook, language-server plugins, output styles,
  a brainstorm skill, clipboard helpers, a writing-style skill.
- **A project can close branches** (`branch.protected`): a rewrite that lands on a branch of its
  own never lands on the release branches.
- **The monitor is required**, "as beautiful as it is now or better" than peer-planning's: a board
  of all tasks, and the board of one task on request.
- **The free hour may edit Lem's skills on a branch of the clone.** It never pushes; the owner or
  a session merges.
- **The first run is in a scratch repository**, then in a real project.
- **The correction hook is an optional part.** Lem recommends jev when it is absent and uses it
  only when the owner agrees.
- **The logo is the owner's pick** ("The Line in the Field"). Change it only on his word. The
  night palette of its dark-theme version is his pick too.
- **Each task of a plan gets a fresh builder** ("I usually start fresh executor for every task..
  since forever"). No threshold decides it.
- **A small defect outside the task is fixed at the end**, in the landing's closing pass, and a
  larger one is offered to him as a backlog item ("Polishing step fixes it in place, right away
  if thats cheap small fixes and offer a backlog filing otherwise").
- **A builder's question about the outcome goes to the personas**, not to the reviewer.
- **Lem asks through huddle**, and he never types it: "every question goes via huddle, unless its
  something fixed choice, trivial, without additional context".
- **A shipped skill's name follows `/lem`** ("/lem interview-me sounds perfect like a callout
  command"). The form that was built from it, the id `lem-<name>` and the dispatcher in
  `SKILL.md`, is the starting session's design and open to him.
- **The README is in ASD-STE100 Simplified Technical English**: "We need to use ASD-STE100
  Simplified Technical English (STE) style to describe what we offer here". One topic in each
  sentence, 20 words at most in an instruction and 25 in a description, the active voice, no
  "-ing" verb form except in a technical name, a vertical list for steps. Technical names stay
  exact. This file and the skill files keep their own voice. The README also has diagrams,
  examples and pictures of the board; an example that no run produced says that it is an
  illustration, and a picture of demo data says so in its caption.
- **Linking an older tool's folders is the first step of an adoption, never its end**: "its
  crucial that we first make some test with those linked settings but migrated to settings under
  .lem right after it, like most users will do". `/lem migrate` is that second step; its
  mechanics (a link per moved rule, a link for the review folder) are the starting session's
  design from his remark that "not all rules are about code style".
- **A board of example tasks says so on the page**, and a line that waits for him says where he
  answers. He took a fixture's line for a real one on 2026-11-14.

Designs the starting session took on 2026-11-14 after a question of the owner's. They are open
to him, and they are not his rulings until he says so:

- **The reviewer's seat is a table**, after "should we or can we specify model and effort level
  of the reviewer?": `[seats.reviewer]` with `agent`, `model`, `effort`, `plan_effort`.
- **Lem brings its own builder agent**, after "it feels like we need to bring our own lem-worker
  agent which product may override? ... someone elses setup may have none": `agents/lem-builder.md`
  (his `lem-worker`; named for the role every Lem text uses), on Opus at high effort, overridden
  by a project's own file of the same name.
- **One machine may name its own reviewer for a while**, after "I may want to have a session
  based reviewer ... Codex is down or I run out of tokens there": `.lem/project.local.toml`,
  untracked, read from the main checkout, limited to `[seats]` and `[tools]`, written by
  `/lem reviewer`. Lem never changes the seat by itself.

## Checks

```bash
bash tests/test-lem.sh        # Lem's scripts, in throwaway repositories; loads the board in headless Chrome when one is installed
bash tests/test-gate-panel.sh  # the gate's log and the panel's cast, with the paths a project's settings name
bash tests/test-huddle.sh      # huddle's spec checks and every template; loads pages in headless Chrome when one is installed
shellcheck tests/*.sh
```

A change to a script comes with its test. A change to a stage file has no test: its test is a
real task, so say in the commit which task showed the need.

## Layout

- `skills/lem/SKILL.md`: the entry point and what holds in every stage.
- `skills/lem/stages/`: one file per subcommand.
- `skills/lem/harness/`: the capability contract and one file per agent.
- `skills/lem/scripts/`: `project.py` (a repository's settings, task state and the event log),
  `doctor.py` (the machine), `review_queue.py` (landed changes that wait for a review),
  `board.py` (opens the board), `land.py` (the landing, one refusable step at a time).
- `skills/lem/assets/board.html`: the board of all tasks and of one task, one page for both.
- `skills/lem/templates/`: the shapes onboarding fills.
- `skills/lem/prompts/`: the standing briefs of a task's lead and of the reviewer.
- `scripts/setup.py`: the setup script. It links the skills, the builder agent and the `huddle`
  command from this clone into a home directory, never over something else, and runs the machine
  check.
- `agents/lem-builder.md`: the builder, as a Claude Code agent definition. Its body is the
  builder's standing rules; `harness/claude-code.md` says how it is used and overridden.
- `skills/lem/references/`: the catalog of published style guides.
- `assets/lem.svg`: the logo, and `assets/lem-mark.svg`: the figure alone, for an icon.
  `assets/lem-night.svg` and `assets/lem-mark-night.svg` are the same drawings in the night
  palette, written by `assets/night.py`; the README shows the night one in a dark theme.
- `assets/screens/`: the README's pictures of the board, for a light and a dark theme. They are
  renders of `skills/lem/assets/board.html` over demo data, at two device pixels for each pixel.
- `skills/lem-huddle/`, `skills/lem-webrev/`, `skills/lem-backlog/`, `skills/lem-interview-me/`, `skills/lem-dialectic/`,
  `skills/lem-root-cause/`, `skills/lem-release/`, `skills/lem-last-tag/`, `skills/lem-pr-review/`,
  `skills/lem-gate/`, `skills/lem-panel/`: the skills Lem names and ships. `NOTICE` says where
  each came from.

## The shipped skills are copies, not yet under the rules above

Each was copied from where it worked and changed only as far as the new layout needed. Their text
still names Claude Code's tools, `skills/lem-backlog` and `skills/lem-webrev` use `${CLAUDE_SKILL_DIR}`,
and huddle's Stop hook (`skills/lem-huddle/hooks/hooks.json`) is registered by nothing. Bring one under
the capability rule when a second agent has to run it, not before.

The set is deliberately small. A tool with its own life (revmux, agterm, cronn, plannotator, Codex)
is checked for by `doctor.py` and never copied in, and a project that prefers its own tool for a
role says so in its settings or its `AGENTS.md`.
