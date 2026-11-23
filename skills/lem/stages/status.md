# status

A bare `/lem`, `/lem status` and `/lem status <task>`, in any session. Open the board first
(`SKILL.md`, "The board"). In a task's session, say first where its own task stands, in one line
from its newest state block. Nothing here starts a task's work: what merged on GitHub, a conflict
and the queue are the board's server's, and the status only reads.

A task's own board also shows its criteria, as the top of its plan has them: each with the tests
that hold it and what the last check of those tests gave. `lem criteria
show SLUG` prints the same. The criteria are what the owner reads of a task; the rest of the plan
is the agents'. For a status of one task, say its criteria in his words before anything else.
Then, for a task that was proposed and read by the merge agent, say the first line of its
`merge-review.md` in the task directory, its verdict; the board shows the whole review first on the
task's Overview.

Every project of Lem has personas, and a project without them has an onboarding that is not
finished. The machine check (`lem doctor`), run in the repository, has
a `project personas` row that says how many the panel finds, from the checkout or the default
branch. Look at it with the status: with none, say so and name the step, `/lem init`, which
asks who a decision here affects and writes them without touching the settings that exist; with
one, say that a panel needs a second person who would notice other things. A `correction hook`
row is there only when a settings file also names the hook, beside the plugin: say each file and
the entry its `without_it` says to delete by hand, in one line, and ask nothing. Each message is
still judged once, so it waits for no answer.

Then say what waits for him, as one list in one order, the same at every bare `/lem`:

```bash
lem project waiting
```

While `owner` says that he is away, the list's first line says so and since when, in his clock,
and that it holds for the whole machine, since he may have said it in another repository: "You
are away since 14:05, in every repository on this machine; the tasks go on without you until /lem im-back."
Then it gives the board's own rows of "Waits for you", in the board's order (`rows`, each with its
`kind` and its task), and you say them so, in plain names and never in task codes, one line each,
with each kind's entry under its key, and leave out a kind that has none:

1. `breakers`: each breaker of a task that waits for him: the task and the document's title;
2. `no_session`: each task whose session is gone (`need: gone`) or does not answer a wake-up
   (`need: deaf`); the board's "Open a session", or `lem session open SLUG --why dead`, opens one;
3. `stopped`: each task whose live session showed no sign of work after the board server's status
   message and its one restart, or, for a session Lem cannot read, no event of the task after the
   status message alone, the stop the server logged; when its `unread` is true, you say that Lem
   cannot read the task's session; the board's "Open a session", or its `open`, `lem session open
   SLUG --why stopped`, opens a fresh one beside it;
4. `criteria`: each task whose acceptance criteria wait for his yes;
5. `held`: each task that waits for a step of his or one more fact, with that step;
6. `after_dropped`: each task queued after a task that was dropped, with its `where` as it is: the
   dropped task (`after`), "start SLUG now" (`start`), which starts it without that task's result,
   and `/lem drop SLUG` (`drop`), which ends it, either one typed in any Lem session of this
   repository, since no session runs the task;
7. `blocked`: each task its session stopped on something it cannot settle alone, with its `line`;
   he answers in the task's session or with `/lem drop SLUG`;
8. `plans`: each plan that waits for him to read it;
9. `reviews`: each merge review that calls him, "read the merge review" with its `why`;
10. `pull_requests`: each open pull request whose merge waits for him, its address, and green or
    each reason it is not (one the merge agent still reads, or that the board's server merges after
    a `merge` verdict, is not in the list); when `merge_refused` holds GitHub's or Lem's line, that
    line; a task with a `night` says "of the night".

When `sessions.known` is false, say in one line that the tasks' sessions are not known, with
`sessions.said`: no task with no session can show then.

When `count` is 0, say "nothing waits for you" in one line. Then, after the list, what builds and
what each other task waits on, what landed today, and what was answered today with its answer in
one line, from `lem project tasks`.

**Where he answers.** A breaker, criteria, a held step and an interview are answered in the task's
own session: name it for each, from `lem session list` (the task's newest session, and whether it
is `live`). One with no live session gets "no session" on the board, whose button opens one.
`/lem status SLUG` opens the task's session when something of it waits for him and none runs,
`lem session open SLUG --why owner`, and says its `say`. A pull request he reads on GitHub.

A dropped, landed or answered task has no choice that waits. A task whose status is null has a
state nobody wrote through the script: say so. A task with a `ticket_owed` ended, and its ticket in
the tracker does not say so yet: say that too, with the step that pays each owed step, by the
tracker's kind (`tracker.kind` in `lem project show`). For `github` it is one line that any session,
or the owner in a terminal, runs: `lem issue STEP SLUG`, STEP being the owed step's tracker step
(`land` for `landed` or `commented`, `drop` for `dropped`, `answer` for `answered`, and for
`unassigned` the `drop` or `answer` of the task's status). For `linear` it is the `lem-linear`
skill's step of that name, run from a session (`load-skill`). A dropped or answered task whose
newest state block says where its ticket stays (an issue stays open): say that line, since the
session that wrote it may have closed before he saw it. When `night_report` is not null, say after the
list, from that file, which items became which pull request, which the night left out and why,
and which task it left held for him; the files hold no record of a status shown.

## The board's server

`/lem serve` and its words run one `lem serve` command each (the table in `SKILL.md`), and you say
what its JSON says in one line: the board's address (`url`), and the phone's (`tailscale`) when the
door is open. `--tailscale` refuses with the step that is missing (Tailscale not installed, not
signed in, HTTPS off in the admin console): say that step as it is, and nothing else. The door
stays open across restarts, since the machine's settings keep it. A command the owner types in a
terminal with no agent (a remote login) is the plugin's `lem` by its path: the `board server` row of
`lem doctor` gives that line for this computer.

