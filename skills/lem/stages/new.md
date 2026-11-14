# new

`/lem new <what>` opens one task and starts its lead. `<what>` is the owner's words, an issue link
or a backlog item. This file is Lem's from the ask to the landing line: how a task is opened, how
a lead is started, and what to do each time a lead stops.

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
4. **The brief.** Write `brief.md` in the task directory, with this and nothing more:

   ```
   Read SKILL_DIR/prompts/lead.md and follow it.
   task: SLUG
   branch: the branch of step 1
   worktree: the path `project.py worktree-dir SLUG` prints
   task directory: the task directory's absolute path
   lead: builder
   stop after the plan: no
   ```

   The brief says nothing about the code, so it cannot say anything wrong about it. The ask is in
   `task.md`, in the owner's words. The brief is a file because a task may wait in the queue or
   get a second lead, and each start has to find the same answers: `/lem plan <what>` writes
   `stop after the plan: yes` here, and that line is what keeps a queued plan from being built.
   When the owner called the task careful in the ask, write `lead: session`.
5. **Does it wait for another task?** Two asks that name the same thing (the same screen, the
   same file, the same command) run one after the other. Write the later one's state as `queued`
   with the line `after: SLUG` of the earlier one, and stop here: it starts when that task is
   `landed` or `dropped`, so it builds on what the earlier one changed. Do not read the code to
   find an overlap the asks do not show; the landing line settles that one (`stages/land.md`,
   step 1).
6. **Start its lead**, as the next section says. Then go back to the owner. Do not wait for the
   lead and do not watch it.

`/lem build <task>` is for a task whose state is `drafted` or `planned`: change its brief to
`stop after the plan: no` and start its lead.

## Start a lead

Every start goes this way: a new task, `/lem build`, a queued task whose turn came, and a lead
that is started again after it stopped.

1. **A place.** `project.py may-start`. On exit 1 the task waits: write its state as `queued`,
   unless it is `queued` already, tell the owner in one line which tasks hold the places, and
   stop here.
2. **The worktree.** When the task has one, use it. When it has none, make it at the path in the
   brief: from the task's branch when that branch exists (a night draft, a task whose worktree
   was removed), otherwise from the settings' base branch. Use the project's own worktree script
   when `AGENTS.md` names one, since it sets up what a plain worktree lacks (a test database, an
   environment); otherwise `git worktree add`. The worktree is in the checkout, not in the task's
   state directory: an agent's sandbox may not write inside the git directory, and the state has
   to outlive the worktree.
3. **The lead.** Write the state `building` first, with the line `lead: builder` or
   `lead: session` as the brief says, so the next `may-start` counts this task. Then, for a
   builder, `spawn-builder` with one line: `Read TASK_DIRECTORY/brief.md and follow it.` For a
   session, `open-task-session` with the same file; write the state again with the line
   `session: ID` and the id the session got, so the board can show the session and it can be
   closed after the landing. When the task's session is still there, the start is one message to
   it with what changed (the owner's answers, a settled blocker) instead of a second session.

A lead that is started again is a fresh agent with the same brief. It finds the plan, the report,
the decisions and the commits on the branch; that is the whole handover.

## When a lead stops

A builder's reply is the path of its report. A session's lead sends one message that starts with
`lem:` and names the task. Either is only a wake-up. The fact is the task's newest state block:
`project.py tasks`, then read the task's `report.md`. Act on the status:

- **`ready`**: the task joins the landing line. Run `stages/land.md` when no task is in
  `landing`; a `ready` task waits there in the order of its state's time.
- **`planned`**: the report says why the lead stopped at the plan.
  - *It needs a session* (the plan is careful): change the brief to `lead: session`, and start
    a lead.
  - *The owner asked for the plan only*: show the owner the plan through the settings'
    `tools.annotate`, and leave the task as it is until the owner says build or drop.
- **`held`**: the report holds one or more decisions that are the owner's, each in the form
  `stages/plan.md` gives under "A held decision". Take each through the `gate` skill, then the
  `panel` skill with the project's cast; the panel writes the card the owner sees and says how
  its page opens. Put the report's run above the card, with whether it was reproduced or derived,
  and its one line on why the case became possible and how far the same cause reaches. Ask all
  held decisions of one task in one go. Write each answer in the task's `decisions.md`, then
  start a lead. The `panel` skill asks for what users would see under each option; that is in
  the report, and what is missing there the lead adds, not you.
- **`blocked`**: the report says what the lead could not settle and what it tried. A missing
  tool, a base branch that does not build, a conflict with another task: settle it, then start a
  lead. An approach that failed twice goes to a fresh builder with a different approach, as
  `stages/build.md` says: add one line to the brief, `do not repeat:` and what the report says
  the two tries assumed. When only the owner can settle it, write the state `held` and ask.
- **anything else**, or no new state block: the lead ended without its last step. Start a lead;
  it reads the state and the report and goes on. After a second such stop, write `blocked` and
  tell the owner what the reply or the session's screen shows.

After any of these, look at the queue. Take the `queued` tasks in the order of their state's
time, leave out each one whose `after:` task is neither `landed` nor `dropped`, and start a lead
for the first that is left. Step 1 of "Start a lead" decides whether there is a place.
