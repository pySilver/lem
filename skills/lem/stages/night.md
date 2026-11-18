# night

`/lem night` runs with nobody at the terminal, started by a scheduled job. The session it starts
is Lem for that night. It takes items of the backlog, the smallest first, and runs each one
without the owner to its pull request: "night execution is just a fun thing to build something
while nobody's looking and its actually got to be a PR to merge, not a plan" (2026-11-18).
Nothing asks him.

1. **The brake.** Count the pull requests of earlier nights that nobody merged or closed: the
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
   `worth: yes` first. Take the first `flow.max_tasks` of them.
3. **Each one runs without the owner.** In that order, open the task as `stages/new.md` does,
   with the item's path as the ask and `--night YYYY-MM-DD` on its `lem project task-dir`, with
   the night's date: it marks the task as the night's, and it runs without the owner until he
   says `/lem im-back`. From there the task takes the path that `stages/new.md` chose, as any
   task that runs without the owner does (`stages/away.md`). A lead's brief carries `request by: someone else`, since nobody at the
   terminal read the item, so the criteria of a task on the standard track are approved with `--alone` and its pull
   request is not green for them. A line a stage file tells the owner goes into the night
   report. `lem project may-start` queues a task over the limit, as by day.
4. **Stay until each one stops.** A lead or a builder that stops wakes this session, which acts
   as `stages/stopped.md` and `stages/land.md` say, up to the pull request. A step that a later
   "no" cannot reverse waits for him as his card (`stages/choice.md`); when every task left
   needs it, the task is `held`. The night ends when each of its tasks is `open`, `held`,
   `blocked` or ended.
5. **The night report**, `night/YYYY-MM-DD.md` in the folder `lem project state-dir` prints,
   written when the night ends and again at each stop before it:
   - each item that became a task: its path, the task, and its pull request with green or each
     reason it is not, or where the task stands;
   - each task `held` for him, with the step it waits on;
   - each item left out, with why: decided against, held by another branch, a choice, a topic
     in reach (the topic in his words), or past `flow.max_tasks`;
   - the brake, when it stopped the night.

In the morning a bare `/lem` lists the night's pull requests among the others, each marked as of
the night, with this report (`stages/status.md`).
