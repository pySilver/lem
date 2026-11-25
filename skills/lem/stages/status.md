# status

A bare `/lem`, `/lem status` and `/lem status <task>`, in any session. Open the board first
(`SKILL.md`, "The board"). In a task's session, say first where its own task stands, in one line
from its record (`lem task show SLUG`: its status, its hold and its line). Nothing here starts a
task's work: what merged on GitHub, a conflict and the queue are the board's server's, and the
status only reads.

A task's own board also shows its criteria, as the top of its plan has them: each with the tests
that hold it and what the last check of those tests gave. `lem criteria show SLUG` prints the
same. The criteria are what the owner reads of a task; the rest of the plan is the agents'. For a
status of one task, say its criteria in his words before anything else. Then, for a task that was
proposed and read by the merge agent, say the first line of its `merge-review.md` in the task
directory, its verdict; the board shows the whole review first on the task's Overview.

Every project of Lem has personas, and a project without them has an onboarding that is not
finished. The machine check (`lem doctor`), run in the repository, has a `project personas` row
that says how many the panel finds, from the checkout or the default branch. Look at it with the
status: with none, say so and name the step, `/lem init`, which asks who a decision here affects
and writes them without touching the settings that exist; with one, say that a panel needs a
second person who would notice other things. A `correction hook` row is there only when a
settings file also names the hook, beside the plugin: say each file and the entry its
`without_it` says to delete by hand, in one line, and ask nothing. Each message is still judged
once, so it waits for no answer.

Then say what waits for him, as one list in one order, the same at every bare `/lem`:

```bash
lem waiting
```

While `owner` says that he is away, the list's first line says so and since when, in his clock,
and that it holds for the whole machine, since he may have said it in another repository: "You
are away since 14:05, in every repository on this machine; the tasks go on without you until
/lem im-back." Then it gives the board's own entries of "Waits for you", in the board's order
(`tasks`): one for each task, with each of its things in its order (`things`, each with its
`key`, its `kind` and its `verb`, the board's words for it). You say them so, in plain names and
never in task codes. A task of one thing is one line, as the board's plain row. A task of two or
more is one line with the task's name, as the board's stack, and under it one line for each of
its things, in its words: "Refund line on receipt", then "Read the merge review" and "Merge the
pull request #44". Each thing's line carries the facts of its kind, from the entry of the same
task in the group of that kind (`breaker` in `breakers`, `session` in `no_session`, `card` in
`cards`, `plan` in `plans`, `review` in `reviews`, `merge` in `pull_requests`, and every other
kind in the group of its own name), as the list below gives them:

1. `breakers`: each breaker of a task that waits for him, as `lem decisions pending` gives it:
   the task and the document's title;
2. `no_session`: each task whose session is gone (`need: gone`) or does not answer a wake-up
   (`need: deaf`); the board's "Open a session", or `lem session open SLUG --why dead`, opens one;
3. `stopped`: each task whose live session showed no sign of work after the board server's status
   message and its one restart, or, for a session Lem cannot read, no event of the task after the
   status message alone, the stop the server logged; when its `unread` is true, you say that Lem
   cannot read the task's session; the board's "Open a session", or its `open`, `lem session open
   SLUG --why stopped`, opens a fresh one beside it;
4. `criteria`: each task whose acceptance criteria wait for his yes;
5. `held`: each task that waits for a step of his or one more fact, with its `line`;
6. `cards`: each card the task's live session put up and waits on, with its `prompt`; he answers it
   on the board or on the card in the session;
7. `after_dropped`: each task queued after a task that was dropped, with its words as they are:
   the list of its dropped dependencies (`after`), "start SLUG now" (`start`), which lifts the
   queue and starts it, and `/lem drop SLUG` (`drop`), which ends it. He can type either one in
   any Lem session of this repository, since no session runs the task;
8. `blocked`: each task its session stopped on something it cannot settle alone, with its `line`
   and its `fix`, or the release stop's message as its `line`; he answers in the task's session or
   with `/lem drop SLUG`;
9. `plans`: each plan that waits for him to read it;
10. `reviews`: each merge review that calls him, "Read the merge review" with its `why`;
11. `pull_requests`: each open pull request whose merge waits for him, its address
    (`pull_request`), and green or each reason it is not (`not_green`). Say "Check the pull request
    on GitHub" when that is its verb. The owner checks GitHub before he asks Lem to retry the
    merge. A request the merge agent still reads, or that the board's server merges after a
    `merge` verdict, is not in the list. When
    `conflict` is true, GitHub calls it conflicting, and the board's server wakes its session; when
    `merge_refused` holds GitHub's or Lem's refusal, say its `line`; a task with a `night` says "of
    the night".

When `sessions.known` is false, say in one line that the tasks' sessions are not known, with
`sessions.said`: no task with no session can show then.

When `forge.said` is present, say why the forge facts are unknown, in one line.

When `count` is 0, say "nothing waits for you" in one line. The tasks in `parked` wait for nobody
and are not counted: name them in one line after the list. Then what builds and what each other
task waits on, from `lem task list`. From `lem task list --ended`, say what landed today and
what was answered today, by `status` and `since` in the owner's clock. For each answered task,
read `investigation.md` in the folder that `lem task dir SLUG` prints. If the report is gone,
read `task.json` in that folder. Use `task.investigation.line` or, if it is absent, the newest
state's `line` in the journal (the summary's `last_state.line` after retention). Give the
answer in one line.

**Where he answers.** A breaker, criteria, a held step and an interview are answered in the task's
own session: name it for each, from `lem session list`. Its newest session must have both `live`
and `agent` true. One with no live session gets "no session" on the board, whose button opens one.
`/lem status SLUG` opens the task's session when something of it waits for him and none runs,
`lem session open SLUG --why owner`, and says its `say`. A pull request he reads on GitHub.

A dropped, landed or answered task has no choice that waits. For an ended task, `ticket.owed` in
the output of `lem task show SLUG` lists the tracker steps still due. Say which step the tracker
needs, by its kind (`settings.tracker.kind` in `lem settings show`). For
`github` it is one line that any session, or the owner in a terminal, runs: `lem issue STEP SLUG`,
STEP being the owed step's tracker step (`land` for `landed` or `commented`, `drop` for `dropped`,
`answer` for `answered`, and for `unassigned` the `drop` or `answer` of the task's status). For
`linear` it is the `lem-linear` skill's step of that name, run from a session (`load-skill`). A
dropped or answered task whose newest line in its record says where its ticket stays (an issue
stays open): say that line, since the session that wrote it may have closed before he saw it. When
`night_report` is not null, say after the list, from its `file`, which items became which pull
request, which the night left out and why, and which task it left held for him; no record of a
status shown is kept.

## The board's server

`/lem serve` and its words run one `lem serve` command each (the table in `SKILL.md`), and you say
what its JSON says in one line: the board's address (`url`), and the phone's (`tailscale`) when the
door is open. `lem serve door on` refuses with the step that is missing (Tailscale not installed,
not signed in, HTTPS off in the admin console): say that step as it is, and nothing else. The door
stays open across restarts, since the machine's settings keep it. A command the owner types in a
terminal with no agent (a remote login) is the app's `lem` by the path an update keeps: the `board
server` row of `lem doctor` gives that line for this computer.
