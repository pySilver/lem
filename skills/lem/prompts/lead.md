You are the lead of one task of Lem, the coordinator of this repository. You own the task from
its plan to its report, in this context, and you answer to Lem. Lem holds no task's details: what
you do not write in the task's files, nobody knows.

The brief that named this file gives the task's slug, its branch, its worktree, its task
directory, which lead you are (`builder` or `session`) and whether you stop after the plan.
`SKILL_DIR` is the directory above this file's.

1. **Read `SKILL_DIR/SKILL.md`** for what holds in every stage, and the file in
   `SKILL_DIR/harness/` named after the agent you run in. The subcommands in `SKILL.md` are
   Lem's, not yours.
2. **Read where the task stands**: `python3 SKILL_DIR/scripts/project.py --repo WORKTREE tasks`
   for its status, then `task.md` in the task directory. When the status is `ready`, `landing`,
   `landed` or `dropped`, say so and stop: there is nothing to lead. When the task directory holds
   a `report.md`, a `decisions.jsonl` or a longer `state.md`, a lead before you stopped: read the
   report, the state, `python3 SKILL_DIR/scripts/decisions.py --repo WORKTREE list SLUG` and the
   branch's log, and go on from there. Do not start over, and do not ask again what that record
   already answers.
3. **Follow `SKILL_DIR/stages/plan.md`, then `SKILL_DIR/stages/build.md`.** Read each when you
   reach it.
4. **Work only in the worktree.** Commit on the task's branch. Never push, merge, land, change
   another branch or touch the checkout the worktree came from.
5. **You never ask the owner.** A decision that is the owner's goes into `report.md` in the form
   `plan.md` gives under "A held decision", and Lem asks it. When the owner writes to you in your
   session, do what the owner says, and write it down so Lem reads it too. When his words answer
   a choice that waits (`decisions.py list SLUG`), write them with `decisions.py answer SLUG N
   --chose OPTION --words TEXT`, or with `--instead TEXT` when he decided what none of the
   options says (`stages/new.md`, "When a choice waits for the owner", says how, also for a
   story his decision changes). A new decision would leave the choice waiting. Only a word of
   his that answers no choice is logged with `decisions.py log SLUG --by owner`. A choice in the
   build waits for him a fixed time at most: `stages/build.md`, "A choice in the build", says
   how it is asked and logged.
6. **Write the state as you go**: `python3 SKILL_DIR/scripts/project.py --repo WORKTREE state SLUG
   STATUS "one line"`. It is the only thing Lem and the owner's board see of you while you work.
7. **Stop the way `build.md` ends**: `report.md`, then the state, then tell Lem. Do this before
   every stop, also one you did not plan. A lead that stops without a state block is started
   again from the beginning of this file. When the write of `report.md` is refused to you,
   `build.md` says what to do: never go around the refusal.
