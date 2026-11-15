# new

`/lem new <what>` opens one task and starts its lead. `<what>` is the owner's words, an issue link
or a backlog item. This file is Lem's from the ask to the landing line: how a task is opened, how
a lead is started, and what to do each time a lead stops.

## Open the task

0. **An ask that is a ticket.** When the ask is a ticket's id or its URL and `project.py show`
   gives a `tracker`, the tracker reads it (`load-skill` the tracker, its "read"): the title, the
   description, the link, the parent, the labels and the branch name the tracker gives. The
   ticket's words are then the ask. When the settings have no tracker, say that this project has
   none, and ask the owner for the ask in his words. When `project.py tasks` already lists a task
   with this ticket that is not `dropped`, do not open a second one: say which task it is and
   where it stands.
1. **The slug and the branch.** A slug of two to five plain words that say what the owner gets
   ("report-dates-stay-whole"), never a code. The branch is `<type>/<slug>` with a semantic type
   (`feat`, `fix`, `chore`, `docs`), unless the project's `AGENTS.md` gives its own scheme. Take
   the type from the ask alone: `fix` when the ask says that something is wrong today, `feat`
   when it asks for something that is not there, and `feat` when you cannot tell. The branch's
   type binds nobody; each commit of the lead carries its own. A slug that a `landed` or a
   `dropped` task has is taken, since that task's files stay under it: add a word, as
   `task-dir` says when it refuses. For a ticket, the branch is the
   name the tracker gives for it, when it gives one: the tracker and its automation find the
   work by that name.
2. **The task directory.** `project.py task-dir SLUG --ask "the owner's words"` keeps the ask as
   the owner gave it, for the board and the status. For a ticket, add `--ticket ID`, and the ask
   is the ticket's title; the command refuses a ticket another task holds. Then write `task.md`:
   - the ask, verbatim; for a ticket, its id, its link, its title and its description as written;
   - the outcome in one or two sentences, as the person it is for would see it;
   - done when: the evidence that shows the outcome, each line something a command or a look at
     the product can show;
   - out of scope, when the ask has an obvious neighbor this task leaves alone.
   Write it from the ask, the project's profile and the rulings. Do not read the code for it: a
   "done when" line that needs the code is the lead's to sharpen in its plan. A line you put out
   of scope by yourself is a decision taken without the owner: write it in `decisions.md`.
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
6. **Start its lead**, as the next section says. Open the board when this session has not
   opened it yet (`SKILL.md`, Status); it stays in the sidebar beside your session.
7. **Tell the owner**, in a few lines: the task's plain name, the outcome and the "done when"
   lines as you wrote them, each decision you took for him (what you put out of scope), and that
   the report comes after the landing. Then go back to the owner's next message. Do not wait for
   the lead and do not watch it.

`/lem build <task>` is for a task whose state is `drafted` or `planned`: change its brief to
`stop after the plan: no` and start its lead. A path to a plan file names its task too: the
file is `YYYYMMDD-<slug>.md`, and the slug is the task's. With no name, list the tasks in those
two states (`project.py tasks`), each with its ask and its plan's path, and ask which one: a
fixed choice, so it stays in the terminal. One such task needs no question.

The owner may say that a task is careful, at any time before its landing, whatever its lead
called it. At once, add the line `careful: the owner says so` to the task's brief, and write his
words in `decisions.md`. The brief is what holds it: whoever reads the task's next stop reads
that line, also a Lem that started after this one, and `land.py start` refuses the task until
one of its states says `careful: read by a session`, which a session's lead writes with `ready`. A task that still builds finishes its
build. When a builder led it and it stops as `ready`, it does not go to the landing: change the
brief to `lead: session` and start a lead. The session gets the second opinion on the plan and
a review of what was built, and writes `ready` again.
Then ask what the owner's word was about, when it is not plain. A topic or a path the settings
already name, which the lead read wrong, is a lesson about that judgment (`stages/learn.md`).
Something no setting names may be a rule for later tasks or a wish for this one task: only the
owner knows, and only his yes puts a topic or a path into the settings.

## When a task is dropped

The owner says that a task is not wanted, at any point before its landing. Write the state
`dropped` with his reason in one line. Close the task's session when it has one, and remove its
worktree the way the project does; the branch stays, because its commits are on no other branch
(`land.py clean` does both and says so). For a task that came from a ticket, the tracker then
says so on the ticket (its "drop") and changes no status: tell the owner which status the ticket
has, since where it goes now is his call. Then look at the queue, as the last section says.

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
   environment); otherwise `git worktree add -b BRANCH PATH BASE` for a new branch, and
   `git worktree add PATH BRANCH` for a branch that exists. `project.py worktree-dir` already made the folder for worktrees one that
   git ignores. The worktree is in the checkout, not in the task's
   state directory: an agent's sandbox may not write inside the git directory, and the state has
   to outlive the worktree.
3. **The lead.** Write the state `building` first, with the line `lead: builder` or
   `lead: session` as the brief says, so the next `may-start` counts this task. For a task that
   came from a ticket, the tracker then marks the ticket as started (its "start"); it writes
   nothing when the project's settings say that the tracker moves its own tickets. Then, for a
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
`project.py tasks`, then read the task's `report.md`.

A lead whose agent refused it the write of `report.md` says so in its state (`report in the
reply`), and its reply is the whole report. Write that text into `report.md` word for word, with
one line at the top that says who copied it and why. Change nothing in it. The harness file says
when this happens.

Act on the status:

- **`ready`**: when the brief holds `careful: the owner says so` and no state of the task says
  `careful: read by a session`, it goes to a session first, as "The owner may say that a task is careful" above says. Otherwise
  the task joins the landing line. Run `stages/land.md` when no task is in
  `landing`; a `ready` task waits there in the order of its state's time.
- **`planned`**: the report says why the lead stopped at the plan.
  - *It needs a session* (the plan is careful): change the brief to `lead: session`, and start
    a lead.
  - *The owner asked for the plan only*: show the owner the plan through the settings'
    `tools.annotate`, and leave the task as it is until the owner says build or drop.
- **`held`**: the report holds one or more decisions that are the owner's, each in the form
  `stages/plan.md` gives under "A held decision". Take each through the `lem-gate` skill, then the
  `lem-panel` skill with the project's cast; the panel writes the card the owner sees. The card
  reaches him through `ask-owner`, which shows it as the settings' `tools.ask` says: that key
  outranks the way of asking either skill names. Put the report's run above the card, with whether it was reproduced or derived,
  and its one line on why the case became possible and how far the same cause reaches. Ask all
  held decisions of one task in one go. Write each answer in the task's `decisions.md`, then
  start a lead. The `lem-panel` skill asks for what users would see under each option; that is in
  the report, and what is missing there the lead adds, not you.
  A task is also `held` when a step is the owner's to do and no decision at all: a trust prompt
  of the reviewer's agent, a command an agent is refused. Tell the owner that step as it is, with
  where he does it; it needs no gate and no panel. The lead goes on when the step is done.
- **`blocked`**: the report says what the lead could not settle and what it tried. A missing
  tool, a base branch that does not build, a conflict with another task: settle it, then start a
  lead. An approach that failed twice goes to a fresh builder with a different approach, as
  `stages/build.md` says: add one line to the brief, `do not repeat:` and what the report says
  the two tries assumed. When only the owner can settle it, write the state `held` and ask.
- **anything else**, or no new state block: the lead ended without its last step. Start a lead;
  it reads the state and the report and goes on. After a second such stop, write `blocked` and
  tell the owner what the reply or the session's screen shows.

After any of these, look at what is owed and at the queue. A task that ended with a
`ticket_owed` in `project.py tasks` gets those steps from the tracker now. Take the `queued` tasks in the order of their state's
time, leave out each one whose `after:` task is neither `landed` nor `dropped`, and start a lead
for the first that is left. Step 1 of "Start a lead" decides whether there is a place.
