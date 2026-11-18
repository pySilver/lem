# Start a lead

Every start goes this way: a new task, `/lem build`, a queued task whose turn came, and a lead
that is started again after it stopped.

1. **A place.** `lem project may-start SLUG`, with the slug of the task whose lead starts: a task
   that builds already (its investigator called the path, its lead stopped) holds its place, and
   that place is not counted against it. On exit 1 for want of a place the task waits: write its
   state as `queued`, unless it is `queued` already, with the line `investigation: bug` or
   `investigation: question` when its investigator is what starts, tell the owner in one line
   which tasks hold the places, and stop here. A task in `landing`, `open`, `landed`, `answered`
   or `dropped` gets no lead at all, and the step says so: it is no task to queue.
2. **The worktree.** When the task has one, use it. When it has none, make it at the path in the
   brief: from the task's branch when that branch exists (an older night's draft, a task whose worktree
   was removed), otherwise from the settings' base branch. Use the project's own worktree script
   when `AGENTS.md` names one, since it sets up what a plain worktree lacks (a test database, an
   environment), and give it the base as origin has it after `git fetch origin BASE`; otherwise
   `lem project worktree SLUG BRANCH`, which takes a branch that exists as
   it is and starts a new one from origin's base branch after a fetch, not from the local base
   branch, which may be days old; when origin does not answer, it starts from the local one and
   says so in one line. `lem project worktree-dir` already made the folder for worktrees one that
   git ignores. The worktree is in the checkout, not in the task's
   state directory, which is in the main checkout's state folder (`.lem/state/`): the state has
   to outlive the worktree.
3. **The lead.** Write a lead's `coordinator:` and `socket:` lines again with your own
   values when they are not yours (a brief written by a Lem before you, or one with no such
   lines): a lead tells the session those lines name. A small change's brief has none: its
   builder's reply is its only word. Write the state `building` first, with the line `lead:
   builder` or `lead: session` as the brief says, or `small change: one builder` for a brief that
   names `prompts/small.md`, so the next `may-start` counts this task. A small change's builder
   gets one more line, its start for the board, as it starts: `lem
   project log SLUG builder.start "job=the small change"`; its state of
   `ready` or `held` is its end. The task's first block carries the type line of step 1 of "Open
   the task" (`stages/new.md`) too, when no block before it has one. For a task that came from a
   ticket, the tracker then marks the ticket as started (its "start"); it writes nothing when the project's
   settings say that the tracker moves its own tickets. Then, for a
   builder, `spawn-builder` with one line: `Read TASK_DIRECTORY/brief.md and follow it.` For
   `lead: session`, the plan talk's companion: `open-task-session` with the same file, its agent
   on the model and the effort of the settings' `seats.planner` when the seat names them; write the
   state again with the line `session: ID` and the id the session got, so the board can show the
   companion and it can be closed after the talk, and with the line `defender: MODEL, EFFORT` as
   the companion's status line shows them, which the talk's record names. When the companion is
   still there, the start is one message to it with what changed (the owner's answers, a settled
   blocker) instead of a second session.

A lead that is started again is a fresh agent with the same brief. It finds the plan, the report,
the decisions and the commits on the branch; that is the whole handover.

## `/lem build`

`/lem build <task>` is for a task whose state is `drafted` or `planned`: change its brief to
`stop after the plan: no`, take out the `night: yes` line of an older night's draft, and start
its lead. When its `report.md` or a state block of it says `needs a session:` and `lem project
tasks` gives it no `talk`, change the brief to `lead: session` first: that start opens the plan
talk's companion at once, where a builder would only stop at the plan again. A path to a plan file names its task too: the
file's name is the settings' `paths.plan_file` (`YYYY-MM-DD-<slug>.md` unless they say otherwise;
a plan of an older Lem is `YYYYMMDD-<slug>.md`), and the slug is the task's. With no name, list the tasks in those
two states (`lem project tasks`), each with its ask and its plan's path, and ask which one: a
fixed choice, so it stays in the terminal. One such task needs no question.

## The queue

After a lead stopped (`stages/stopped.md`), a landing, a drop or an answer, look at what is owed and
at the queue. A task that ended with a
`ticket_owed` in `lem project tasks` gets those steps from the tracker now. While a task is `open`
with a pull request and no watch of yours runs, start one, as `SKILL.md` says under Status. A `blocked` task whose
state has `the base is red` and an `after:` task that is `landed` gets the state `ready` again,
with the line `the base is green again`, and joins the landing line. Take the `queued` tasks in
the order of their state's time, leave out each one whose `after:` task is not `landed`,
`answered` or `dropped`, and start a lead, or the investigator of a bug or a question
(`stages/investigate.md`), for the first that is left. Step 1 of "Start a lead" decides whether there is a place.

Last, a nap. When a task ended in this turn (`landed`, `answered` or `dropped`), or nothing is left
for you but the owner's word, and `naps.on` is true in `lem project show`, run `lem
project may-nap`. When its `may` is true, read `stages/nap.md` and start the
nap as it says; when it is false, say nothing of it. A nap never comes before what is owed, the
queue or a question.
