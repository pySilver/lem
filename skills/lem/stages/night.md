# night

`/lem night` runs with nobody at the terminal, started by a scheduled job. The session it starts
is Lem for that night. It takes items of the backlog, the smallest first, and runs each one
without the owner to its pull request: "night execution is just a fun thing to build something
while nobody's looking and its actually got to be a PR to merge, not a plan" (2026-11-18).
Nothing asks him. In the morning he finds pull requests, each green or not green with its
reasons, and the night's report.

1. **The brake.** Count the pull requests of earlier nights that nobody merged or closed: the
   `pull_requests` of `lem project waiting` whose `night` is not null. With two or more, open
   nothing, and write the night report with why. A request nobody reads ages as the base moves,
   and a third one only adds to the pile.
2. **The candidates.** The items in `lem project path backlog`: one file each, with `worth`,
   `where` and `added` between two `---` lines, then a title and prose. Never a tracker's
   ticket: which ticket comes next is a person's call. Leave out an item that is decided against
   (`worth: no`); one that a branch, a worktree, an open plan or a task already holds; one that
   asks for a choice and states no defect or job; and one in reach of a topic (`flow.topics` in
   `lem project show`): read its words and its `where` against each, as step 1 of
   `stages/new.md` reads an ask, and in doubt leave it out, since a careful change needs the
   owner and the plan talk. Size the rest as that step sizes an ask, and order them: the small
   changes first, then the others by how much they change, and within one size `worth: yes`
   first. Take the first `flow.max_tasks` of them.
3. **Each one runs without the owner.** In that order, open the task as `stages/new.md` does,
   with the item's path as the ask, and right after `lem project task-dir`:

   ```bash
   lem project mode SLUG alone --by lem --words "the night of YYYY-MM-DD"
   ```

   with the night's date, in that form: it tells the task from a day's task in the morning list.
   From there the task takes the path that `stages/new.md` chose, as any task that runs without
   the owner does (`stages/mode.md`): a small change has its one builder and Lem's approval; a
   bug has its investigator first; a full change has its criteria from the item, or from an
   interview in which you take your own guess for each question, then the personas' read, the
   ladder for a flagged criterion, and `--alone` for the approval. A lead's brief carries the
   line `request by: someone else`, since nobody at the terminal read the item. Where a stage
   file says to tell the owner a line, write it into the night report. `lem project may-start`
   queues a task over the limit, as by day.
4. **Stay until each one stops.** A lead or a builder that stops wakes this session, which acts
   as `stages/stopped.md` and `stages/land.md` say, up to the pull request. An agent never merges
   a task that runs without the owner. A step that a later "no" cannot reverse waits for him as
   his card (`stages/choice.md`), and only the part of the plan that needs it waits; when every
   task left needs it, the task is `held`. The night ends when each of its tasks is `open`,
   `held`, `blocked` or ended.
5. **The night report**, `night/YYYY-MM-DD.md` in the folder `lem project state-dir` prints.
   Write it when the night ends, and again at each stop before it, so that an early morning
   finds it:
   - each item that became a task: its path, the task, and its pull request with green or each
     reason it is not, or where the task stands;
   - each task `held` for him, with the step it waits on;
   - each item left out, with why: decided against, held by another branch, a choice, a topic
     in reach (the topic in his words), or past `flow.max_tasks`;
   - the brake, when it stopped the night.
