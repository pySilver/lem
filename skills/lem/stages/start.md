# The start of the build

Every start of a task's build goes this way: the owner's yes to the criteria, a complete request,
the fast track's builder, a queued task whose turn came (the board's server opens its session),
`/lem build`, and a task he resumed. The investigator of a bug or a question takes steps 1 and 2.

1. **May it start?** After an interview and his yes, ask step 7 of "The request" (`stages/new.md`)
   first: a task that needs another task's result is `queued` behind it as that step says, and
   this session hands over and closes there. Then `lem project may-start SLUG`. No count of tasks
   stops a start. On exit 1 for a task queued `after:` a task that has not ended, it stays
   `queued`: write `handoff.md` and close this session as step 7 of "The request" says; the board's
   server opens it again when that task is `landed` or `answered`. Behind a task that was dropped,
   the refusal names the owner's two words, "start it" and "drop it": say them to him in one line,
   and do what he picks, as step 7 of "The request" says. A task in `landing`, `open`, `parked`, `landed`, `answered` or
   `dropped` gets no lead at all, and the step says so: it is no task to queue.
2. **The worktree.** When the task has one, use it. When it has none, make it at the path in the
   brief: from the task's branch when that branch exists (a task whose worktree was removed), otherwise from the settings' base branch. Use the project's own worktree script
   when `AGENTS.md` names one, since it sets up what a plain worktree lacks (a test database, an
   environment), and give it the base as origin has it after `git fetch origin BASE`; otherwise
   `lem project worktree SLUG BRANCH`, which takes a branch that exists as
   it is and starts a new one from origin's base branch after a fetch, not from the local base
   branch, which may be days old; when origin does not answer, it starts from the local one and
   says so in one line. `lem project worktree-dir` already made the folder for worktrees one that
   git ignores. The worktree is in the checkout, not in the task's
   state directory, which is in the main checkout's state folder (`.lem/state/`): the state has
   to outlive the worktree.
3. **The state**: `building`, with the line `lead: builder`, or `small change: one builder` for a
   brief that names `prompts/small.md`, and the type line of step 1 of "The request" when no block
   before it has one. For a task that came from a ticket, the tracker then marks the ticket as
   started (its "start"), unless the ticket is there already.
4. **Who builds.**
   - *The fast track*: `spawn-builder` with one line, `Read TASK_DIRECTORY/brief.md and follow
     it.`, and as it starts, `lem project log SLUG builder.start "job=the small change"`; its state
     of `ready` or `held` is its end. Its reply wakes this session ("The fast track" of
     `stages/new.md`, step 3).
   - *After his yes to an interview's criteria, in the shape's session*: hand the task to a fresh
     lead, as `prompts/session.md` says under "A change of phase": the build is a phase of its own.
     Only an interview's session hands over here.
   - *In a session whose phase is the build, or on the standard track from a complete request*:
     you are the lead. Read `brief.md` and follow it. A lead that stopped for his yes after the
     personas' read (`stages/plan.md`, step 1) goes on as the lead after it: it builds on, and
     hands nothing over.

## `/lem build`

`/lem build <task>` is for a task whose state is `planned`, whose lead stopped at the plan for the
owner to read: change its brief to `stop after the plan: no`. Typed in the task's own session, go on
as its lead. Typed elsewhere, `lem session open SLUG --why owner`, and say its `say`; when
it prints `already: true`, the task's session still waits for his word: say its name, and that
"build" there starts it. A path to a plan file names its task too: the file's name is the settings'
`paths.plan_file` (`YYYY-MM-DD-<slug>.md` unless they say otherwise), and the slug is the task's.
With no name, list the tasks in that state (`lem project tasks`), each with its ask and its plan's
path, and ask which one: a fixed choice, so it stays in the terminal. One such task needs no
question.
