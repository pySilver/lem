# night

`/lem night` runs with nobody at the terminal, started by a scheduled job. It takes items of the
backlog, the smallest first, and opens them one after another, each in its own session, which runs
it without the owner to its pull request: "night execution is just a fun thing to build something
while nobody's looking and its actually got to be a PR to merge, not a plan" (2026-11-18).
Nothing asks him. This session keeps no watch of the owner's mark and takes no step of
`stages/away.md` on it: its tasks run without him whatever the mark says. It does no task's work.
Where the project's own `AGENTS.md` says that its night proposes, the night also does what "A night
that proposes" below says, and opens a task only where that file lets it.

1. **The brake.** Count the pull requests of earlier nights that wait for the owner's merge: the
   `pull_requests` of `lem waiting` whose `night` is not null. With two or more, open
   nothing, and write the night report with why: a request nobody reads ages as the base moves.
2. **The candidates.** The items in the folder `lem path backlog` prints: one file each, with `worth`,
   `where` and `added` between two `---` lines, then a title and prose. Never a tracker's
   ticket: which ticket comes next is a person's call. Never an item of the state folder's
   `backlog/` either: those are the reviewer's, and each waits for the owner's start or drop on
   the board. Leave out an item that is decided against
   (`worth: no`); one that a branch, a worktree, an open plan or a task already holds; one that
   asks for a choice and states no defect or job; and one in reach of a topic (`flow.topics` in
   `lem settings show`) or in doubt, read as step 1 of `stages/new.md` reads an ask: a careful
   change needs the owner and the plan talk. Give the rest a track as that step does for an ask, and order
   them: the fast track first, then the others by how much they change, and within one track
   `worth: yes` first. Take the first four of them, or N when the job's line is `/lem night N`
   (the scheduled job's line is the owner's). Four is how many pull requests the owner finds in
   the morning: a guess, not a measurement ("one task at a time per project is fine default for
   night runs", the owner, 2026-11-18).
3. **One at a time, each without the owner.** In that order, open the next task as "Open the task"
   of `stages/new.md` does, with no talk and no focus: the item's path as the ask and as the item, `lem task
   open SLUG --ask PATH --item PATH --night YYYY-MM-DD` with the night's date, and `lem session open SLUG
   --why night`. The mark makes it the night's: it runs without the owner until it ends, whatever
   his status, and his `/lem im-back` does not change it. Its session takes the path "The request"
   chooses, as any task that runs without the owner does; its brief carries `request by: someone
   else`, since nobody at the terminal read the item, so its criteria are approved with `--alone`
   on both tracks (the fast track's with `lem criteria approve SLUG --file TASK_DIR/criteria.md
   --alone`), and its pull request is not green for them: the merge agent calls the owner.
4. **Wait until it stops, then the next.** `run-in-background` with `lem session wait SLUG --until
   open,held,blocked,landed,dropped,answered`; its end wakes this session. When it ends with
   `"gone": true`, the task's session is gone: open it again once, `lem session open SLUG --why
   dead`, and wait again; when it is gone a second time, name the task in the night report and go
   on with the next item. The ladder decides each
   choice, as by day; a breaker (`stages/breaker.md`) holds its task for the morning, and the
   report names its document. Then the next item. The night ends when the last one is `open`,
   `held`, `blocked` or ended.
5. **The night report**, `night/YYYY-MM-DD.md` in the folder `lem path state` prints,
   written when the night ends and again at each stop before it:
   - each item that became a task: its path, the task, and its pull request with green or each
     reason it is not, or where the task stands;
   - each task `held` or `blocked`, with the step it waits on, from its state;
   - each item left out, with why: decided against, held by another branch, a choice, a topic
     in reach (the topic in his words), or past the night's count;
   - the brake, when it stopped the night;
   - for a night that proposes, the names of its proposals, each with its move.
6. **The end.** `run-in-background` with `lem session close-job`, as the last step, after the last
   write of the report. It closes the session once the owner is not looking at it. A refusal says
   that the session is the owner's (no job started its agent for this run) or a task's: say its
   line, and the session stays open. Two answers say that there is nothing to close, and the run
   ends: exit 0 with `"closed": false`, "the session ID is no longer in agterm's tree", and the
   refusal "no session to close", for a run with no agterm session (a `claude -p` from a plain
   shell).

In the morning a bare `/lem` lists the night's pull requests among the others, each marked as of
the night, with this report (`stages/status.md`).

## A night that proposes

Where the project's own `AGENTS.md` says that its night proposes, the night does the search that
file names, and each thing it finds is a proposal, never a change: no branch, no worktree and no
commit for it, and no file that git tracks changes. The morning's retro hands the proposals to its
reviewer (`stages/learn.md`, "retro"), and what passes reaches the owner as an item of the board's
"Backlog". The night adds its run to the day's file, with the night's date, also when it found
nothing, on stdin as a quoted heredoc:

```bash
lem proposals add --kind night --date 2026-11-24 --file - <<'JSON'
{"read": "the whole test suite, run twice in the main checkout", "proposals": [
  {"area": "tests", "move": "The refund check waits for its event, not for one second", "body": "the file, the change, and the run that failed: its output and its time", "source": "the first run of the suite this night", "where": "tests/test_refunds.py:test_refund_event"}
]}
JSON
```

The input has the form of the retro's (`stages/learn.md`, "retro", step 4): `read`, and each
proposal with exactly `area`, `move`, `body`, `source` and `where`. The command writes
`night/YYYY-MM-DD.json` in the state folder, or adds after a run already there, and its result's
`names` gives each proposal's name (`night of 2026-11-24 #1`). Where that file says the night opens no task, steps 1
to 4 do not run, and the report holds the proposals' names alone.
