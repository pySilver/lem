# new

`/lem new <what>` opens one task and starts its lead. `<what>` is the owner's words, an issue link
or a backlog item. This file is Lem's from the ask to the landing line: the second half says what
to do each time a lead stops.

## Open the task

1. **The slug and the branch.** A slug of two to five plain words that say what the owner gets
   ("report-dates-stay-whole"), never a code. The branch is `<type>/<slug>` with a semantic type
   (`feat`, `fix`, `chore`, `docs`), unless the project's `AGENTS.md` gives its own scheme.
2. **The task directory.** `project.py task-dir SLUG`, then write `task.md`:
   - the ask, verbatim;
   - the outcome in one or two sentences, as the person it is for would see it;
   - done when: the evidence that shows the outcome, each line something a command or a look at
     the product can show;
   - out of scope, when the ask has an obvious neighbor this task leaves alone.
   Write it from the ask, the project's profile and the rulings. Do not read the code for it: a
   "done when" line that needs the code is the lead's to sharpen in its plan.
3. **Is the ask clear?** If you cannot write the outcome without choosing between two readings
   that give the owner different things, ask once through `ask-owner`, each reading as what the
   owner would get. Anything else is the lead's to read from the code and log.
4. **Is there a place?** `project.py may-start`. Exit 1: write the state `queued` and tell the
   owner in one line which tasks build; the task starts when one of them stops. Two asks that name
   the same thing (the same screen, the same file, the same command) also run one after the
   other: queue the later one behind the earlier. Do not read the code to find an overlap the
   asks do not show; the landing line settles that one (`stages/land.md`, step 1).
5. **The worktree.** One worktree per task, from the settings' base branch, at the path
   `project.py worktree-dir SLUG` prints. Use the project's own worktree script when `AGENTS.md`
   names one, since it sets up what a plain worktree lacks (a test database, an environment);
   otherwise `git worktree add`. The worktree is in the checkout, not in the task's state
   directory: an agent's sandbox may not write inside the git directory, and the state has to
   outlive the worktree.
6. **Start the lead.** Write the state `building` first, with the line `lead: builder`, so the
   next `may-start` counts this task. Then `spawn-builder` with this brief and nothing more:

   ```
   Read SKILL_DIR/prompts/lead.md and follow it.
   task: SLUG
   worktree: the worktree's absolute path
   task directory: the task directory's absolute path
   lead: builder
   stop after the plan: no
   ```

   The brief says nothing about the code, so it cannot say anything wrong about it. The ask is in
   `task.md`, in the owner's words. When the owner called the task careful or large in the ask,
   start a session instead, as "planned" below does.

`/lem plan <what>` is the same with `stop after the plan: yes`. `/lem build <task>` starts at
step 4 for a task whose state is `drafted` or `planned`, on the branch and the plan it has; when
its worktree is gone, make it again from that branch.

Then go back to the owner. Do not wait for the lead and do not watch it.

## When a lead stops

A builder's reply is the path of its report. A session's lead sends one message that starts with
`lem:` and names the task. Either is only a wake-up. The fact is the task's newest state block:
`project.py tasks`, then read the task's `report.md`. Act on the status:

- **`ready`**: the task joins the landing line. Run `stages/land.md` when no task is in
  `landing`; a `ready` task waits there in the order of its state's time.
- **`planned`**: the report says why the lead stopped at the plan.
  - *It needs a session* (a careful file, or a plan too large for one builder): write the state
    `building` with the line `lead: session`, and `open-task-session` with the brief of step 6,
    `lead: session` and the address the harness file tells you to add. Write the session's name
    or id in a second state line, so the session can be closed after the landing.
  - *The owner asked for the plan only*: show the owner the plan through the settings'
    `tools.annotate`, and leave the task as it is until the owner says build or drop.
- **`held`**: the report holds one or more decisions that are the owner's, each in the form
  `stages/plan.md` step 4 gives. Take each through the `gate` skill, then the `panel` skill with
  the project's cast; the panel writes the card the owner sees and says how its page opens. Put
  the report's run above the card, with whether it was reproduced or derived, and its one line on
  why the case became possible and how far the same cause reaches. Ask all held decisions of one
  task in one go. Write each answer in the task's `decisions.md`, then start a lead again: the
  brief of step 6 for a builder, or one message with the answers to the task's session. The
  `panel` skill asks for what users would see under each option; that is in the report, and what
  is missing there the lead adds, not you.
- **`blocked`**: the report says what the lead could not settle and what it tried. A missing
  tool, a base branch that does not build, a conflict with another task: settle it, or start a
  lead again with what changed. An approach that failed twice goes to a fresh builder with a
  different approach, as `stages/build.md` says. When only the owner can settle it, write the
  state `held` and ask.
- **anything else**, or no new state block: the lead ended without its last step. Start a lead
  again with the same brief; it reads the state and the report and goes on. After a second such
  stop, write `blocked` and tell the owner what the reply or the session's screen shows.

After any of these, look at the queue: when `project.py may-start` exits 0 and a task is
`queued`, start the oldest one at step 5.

A lead you start again is a fresh agent with the same brief. It finds the plan, the report, the
decisions and the commits on the branch; that is the whole handover. It takes a place like a
first start: `project.py may-start` first, then the state `building`, or `queued` when there is
no place.
