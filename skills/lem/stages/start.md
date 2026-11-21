# The start of the build

Every start of a task's build goes this way: the owner's yes to the criteria, a complete request,
the fast track's builder, a queued task whose turn came (the board's server opens its session),
`/lem build`, and a task he resumed. The investigator of a bug or a question takes steps 1 and 2.

1. **May it start?** After an interview and his yes, ask step 7 of "The request" (`stages/new.md`)
   first: a task that needs another task's result is `queued` behind it as that step says, and
   this session hands over and closes there. Then `lem project may-start SLUG`. No count of tasks
   stops a start. On exit 1 for a task queued `after:` a task that has not ended, it stays
   `queued`: write `handoff.md` and close this session as step 7 of "The request" says; the board's
   server opens it again when that task is `landed` or `answered`. A task queued by the owner's
   order (the first line of its block, `the owner's order`) stays so until that task is landed or
   answered, or his word removes the order ("`/lem build`"). Behind a task that was dropped, the
   refusal names the owner's two words, "start it" and "drop it": say them to him in one line, and
   do what he picks, as step 7 of "The request" says. A task in `landing`, `open`, `parked`,
   `landed`, `answered` or `dropped` gets no lead at all, and the step says so: it is no task to
   queue.
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
   before it has one, with its `careful:` line when it found a topic in reach. When the block is
   the task's first (the fast track, a complete request), its call prints `say`: say it as it is
   before step 4, as step 8 of "The request" says. For a task that came from a ticket, the
   tracker then marks the ticket as started (its "start"), unless the ticket is there already.
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

His "start SLUG now", or `/lem build SLUG`, for a task `queued` by his order (the first line of its
block, `the owner's order`), in any session, removes the order. Log his words first, `lem decisions
log SLUG --by owner --what "the owner's order" --chose "start now" --why "his word" --words "HIS
WORDS"`; then write the `queued` block again with each of its lines but the `after:` line, and the
line `the owner's order was removed: "HIS WORDS"`. Then `lem session wake SLUG --why owner`: it
wakes the task's session when one runs, also when you are that session, and opens one when none
does. A close of step 7 of "The request" that still waits for him to leave the session then ends
with no close (`lem session close` gives up on a session woken after it started), so that the
session is not closed under its work. Typed in the task's own session, go on at once as
`prompts/session.md` says for a queued task whose wait ended; the wake's line that comes back
changes nothing. Typed elsewhere, `lem session open SLUG --why owner --focus` takes him there, and
you say its `say`.
