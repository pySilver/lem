# night

`/lem night` runs with nobody at the terminal, started by a scheduled job. It reads the backlog,
picks what an agent can take without a decision from the owner, and leaves a plan for the morning.
It never builds: a plan is the owner's to start.

1. **The brake.** List the drafts that wait: tasks whose newest state block says `drafted at
   night` and whose plan was not built, dropped or replaced (`project.py tasks`). With two or more
   of them, draft nothing and write why in the night report. A plan is written against the code as
   it stood that night, so a draft nobody starts ages, and a third one only adds to the pile.
2. **The candidates.** Read the items in the backlog path (`project.py path backlog`), in the
   `backlog` skill's format. Leave out an item that is decided against, one a branch, a worktree,
   an open plan or a task directory already holds, and one whose files match a careful pattern
   (`project.py careful`): a careful plan needs the reviewer, and that is a day's work. When the
   `backlog` skill's triage has verdicts, take the items it gives to an agent, the surest first.
   Without verdicts, read each item and keep the ones that state a defect or a job, not a choice.
3. **One item, planned.** For the first candidate, run `stages/new.md` and `stages/plan.md` to the
   committed plan, on a branch `plan/<slug>`. Never ask: nobody is there.
4. **A held decision ends the draft.** When planning shows the item needs a decision whose options
   each cost a person something, stop. Record the question, in the owner's terms, in the item's
   backlog file and in the night report, remove the worktree and the branch, and take the next
   candidate. This is the filter that matters: an item only looks decision-free until someone
   plans it. Try three candidates at most.
5. **The night report**, `night/YYYY-MM-DD.md` in the folder `project.py state-dir` prints: for the
   draft, what the owner gets, the plan's path, why no decision was needed, and what it will not
   verify; for each item dropped in step 4, its question; for the brake, the drafts that wait,
   each with a verdict and its reason:
   - **run now**: the code the plan names is as it was;
   - **replan**: the files the plan names changed on the base branch since the draft;
   - **drop**: the item is gone from the backlog or another branch took it.
   Write the last block of `state.md` as `drafted at night`, with the date.

In the morning `/lem status` opens with the night report. The owner starts a draft with
`/lem build` in its worktree, or says hold or drop.
