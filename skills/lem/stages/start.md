# The start of the build

Every start of a task's build goes this way: the owner's yes to the criteria, a complete request,
the fast track's builder, a queued task whose turn came (the board's server opens or wakes its
session), `/lem build`, and a task he resumed. The investigator of a bug or a question takes steps 1 and 2.

1. **May it start?** After an interview and his yes, ask step 7 of "The request" (`stages/new.md`)
   first: a task that needs the result of another task that has not ended (not landed, answered
   or dropped) is `queued` behind it as that step says, and this session hands over and closes
   there. A dropped task is no task to queue behind again: what a task started past a dropped task
   still needs is planned inside it. Then `lem task may-start SLUG`. No count of tasks
   stops a start. On exit 1 for a task queued after a task that has not ended, it stays
   `queued`: write `handoff.md` and close this session as step 7 of "The request" says; the board's
   server opens it again when that task is `landed` or `answered`, or wakes it when it still runs.
   A task queued by the owner's order (`order` in `lem task show SLUG`) stays so until that task
   is landed or answered, or his word removes the order ("`/lem build`"). Behind a task that was
   dropped, the refusal names his word: tell him in one line that the task waits for it, "start
   SLUG now" or `/lem drop SLUG`, and on his word do what "`/lem build`" says. A task in `landing`,
   `open`, `landed`, `answered` or `dropped`, or one he parked, gets no lead at all, and the step
   says so: it is no task to queue.
2. **The worktree.** When the task has one, use it. When it has none, make it at the path in the
   brief: from the task's branch when that branch exists (a task whose worktree was removed, a request a
   resume made from a task the release stop blocked), otherwise from the settings' base branch. Use the project's own worktree script
   when `AGENTS.md` names one, since it sets up what a plain worktree lacks (a test database, an
   environment), and give it the base as origin has it after `git fetch origin BASE`; otherwise
   `lem task worktree SLUG --branch BRANCH`, which takes a branch that exists as
   it is and starts a new one from origin's base branch after a fetch, not from the local base
   branch, which may be days old; when origin does not answer, it starts from the local one and
   says so in one line. It runs the settings' `checks.setup` in a new worktree, and the folder for
   worktrees is one that git ignores. The worktree is in the checkout, not in the task's
   state directory, which is in the main checkout's state folder (`.lem/state/`): the state has
   to outlive the worktree.
3. **The state**: `lem task move SLUG building`. The type, the track and each careful topic are
   on the record already, from the read of step 8 of "The request", which printed the first line;
   a move prints no `say` of its own. For a task that came from a ticket, the tracker then marks
   the ticket as started (its "start"), unless the ticket is there already.
4. **Who builds.**
   - *The fast track*: `spawn-builder` with one line, `Read TASK_DIRECTORY/brief.md and follow
     it.`, and as it starts, `lem task span SLUG small start`; its state of `ready`, or of
     `shaping` when the fast track does not fit, is its end. Its reply wakes this session ("The fast track" of
     `stages/new.md`, step 3).
   - *After his yes to an interview's criteria, in the shape's session*: hand the task to a fresh
     lead, as `prompts/session.md` says under "A change of phase": the build is a phase of its own.
     Only an interview's session hands over here.
   - *In a session whose phase is the build, or on the standard track from a complete request*:
     you are the lead. Mark its start, `lem task span SLUG lead start`, then read `brief.md` and
     follow it. A lead that stopped for his yes after the
     personas' read (`stages/plan.md`, step 1) goes on as the lead after it: it builds on, and
     hands nothing over.

## `/lem build`

`/lem build <task>` is for a task whose state is `planned`, whose lead stopped at the plan for the
owner to read: `lem task build SLUG` moves it to `building`, and you change its brief to `stop after
the plan: no`. Typed in the task's own session, go on as its lead. Typed elsewhere, `lem session open SLUG --why owner`, and say its `say`; when
it prints `already: true`, the task's session still waits for his word: say its name, and that
"build" there starts it. A path to a plan file names its task too: the file's name is the settings'
`paths.plan_file` (`YYYY-MM-DD-<slug>.md` unless they say otherwise), and the slug is the task's:
`lem task build PLAN-FILE` takes the path as it is.
With no name, list the tasks in that state (`lem task list`), each with its ask and its plan's
path, and ask which one: a fixed choice, so it stays in the terminal. One such task needs no
question.

His "start SLUG now", or `/lem build SLUG`, in any session, removes the order of a task `queued` by
his order (`order` in `lem task show SLUG`), and starts a task queued behind a task that was
dropped, by his order or by a need, without that task's result. Behind a task that has not ended
and behind a dropped one alike, run `lem task start SLUG --words "HIS WORDS"`, with his words as
he typed them: it records his words and takes the task out of the queue, its order and the task
it waited for. Then `lem session wake SLUG --why owner`: it
wakes the task's session when one runs, also when you are that session, and opens one when none
does. A close of step 7 of "The request" that still waits for him to leave the session then ends
with no close (`lem session close` gives up on a session woken after it started), so that the
session is not closed under its work. Typed in the task's own session, go on at once as
`prompts/session.md` says for a queued task whose wait ended; the wake's line that comes back
changes nothing. Typed elsewhere, say the wake's `say`, which names the task's session: it opens
with no focus, and never takes it, also when it asks him a question.
