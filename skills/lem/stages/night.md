# night

`/lem night` runs with nobody at the terminal, started by a scheduled job. It takes items of the
backlog, the smallest first, and opens them one after another, each in its own session, which runs
it without the owner to its pull request: "night execution is just a fun thing to build something
while nobody's looking and its actually got to be a PR to merge, not a plan" (2026-11-18).
Nothing asks him. This session keeps no watch of the owner's mark and takes no step of
`stages/away.md` on it: its tasks run without him whatever the mark says. It does no task's work.

1. **The brake.** Count the pull requests of earlier nights that wait for the owner's merge: the
   `pull_requests` of `lem project waiting` whose `night` is not null. With two or more, open
   nothing, and write the night report with why: a request nobody reads ages as the base moves.
2. **The candidates.** The items in `lem project path backlog`: one file each, with `worth`,
   `where` and `added` between two `---` lines, then a title and prose. Never a tracker's
   ticket: which ticket comes next is a person's call. Leave out an item that is decided against
   (`worth: no`); one that a branch, a worktree, an open plan or a task already holds; one that
   asks for a choice and states no defect or job; and one in reach of a topic (`flow.topics` in
   `lem project show`) or in doubt, read as step 1 of `stages/new.md` reads an ask: a careful
   change needs the owner and the plan talk. Give the rest a track as that step does for an ask, and order
   them: the fast track first, then the others by how much they change, and within one track
   `worth: yes` first. Take the first four of them, or N when the job's line is `/lem night N`
   (the scheduled job's line is the owner's). Four is how many pull requests the owner finds in
   the morning: a guess, not a measurement ("one task at a time per project is fine default for
   night runs", the owner, 2026-11-18).
3. **One at a time, each without the owner.** In that order, open the next task as "Open the task"
   of `stages/new.md` does, with no talk and no focus: the item's path as the ask, `lem project
   task-dir SLUG --ask PATH --night YYYY-MM-DD` with the night's date, and `lem session open SLUG
   --why night`. The mark makes it the night's: it runs without the owner until it ends, whatever
   his status, and his `/lem im-back` does not change it. Its session takes the path "The request"
   chooses, as any task that runs without the owner does; its brief carries `request by: someone
   else`, since nobody at the terminal read the item, so the criteria of a task on the standard
   track are approved with `--alone` and its pull request is not green for them.
4. **Wait until it stops, then the next.** `run-in-background` with `lem session wait SLUG --until
   open,held,blocked,landed,dropped,answered`; its end wakes this session. The ladder decides each
   choice, as by day; a breaker (`stages/breaker.md`) holds its task for the morning, and the
   report names its document. Then the next item. The night ends when the last one is `open`,
   `held`, `blocked` or ended.
5. **The night report**, `night/YYYY-MM-DD.md` in the folder `lem project state-dir` prints,
   written when the night ends and again at each stop before it:
   - each item that became a task: its path, the task, and its pull request with green or each
     reason it is not, or where the task stands;
   - each task `held` or `blocked`, with the step it waits on, from its state;
   - each item left out, with why: decided against, held by another branch, a choice, a topic
     in reach (the topic in his words), or past the night's count;
   - the brake, when it stopped the night.

In the morning a bare `/lem` lists the night's pull requests among the others, each marked as of
the night, with this report (`stages/status.md`).
