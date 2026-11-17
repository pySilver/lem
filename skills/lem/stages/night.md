# night

`/lem night` runs with nobody at the terminal, started by a scheduled job. The session it starts
is Lem for that night. It reads the backlog, picks what an agent can take without a decision from
the owner, and leaves a plan for the morning. It never builds: a plan is the owner's to start.

1. **The brake.** List the drafts that wait: tasks whose status is `drafted`
   (`project.py tasks`). With two or more of them, draft nothing and write why in the night
   report. A plan is written against the code as
   it stood that night, so a draft nobody starts ages, and a third one only adds to the pile.
2. **The candidates.** Read the items in the backlog path (`project.py path backlog`), in the
   `lem-backlog` skill's format. The backlog only: a tracker's ticket is never a night's
   candidate, because which ticket is next is a person's call. Leave out an item that is decided against, one a branch, a worktree,
   an open plan or a task directory already holds, and one in reach of one of the project's
   topics (`flow.topics`): read the item's words and its `where` against each, as `stages/new.md`
   step 1 reads an ask, and leave it out in doubt. A careful plan needs the reviewer, and that is
   a day's work. When the
   `lem-backlog` skill's triage has verdicts, take the items it gives to an agent, the surest first.
   Without verdicts, read each item and keep the ones that state a defect or a job, not a choice.
3. **One item, planned.** For the first candidate, open the task as `stages/new.md` does, on a
   branch `plan/<slug>`, and start a builder with `stop after the plan: yes` and one more line in
   its brief, `night: yes`. Never ask: nobody is there. Wait for the builder; this session has
   nothing else to do.
4. **A decision of the owner's ends the draft.** By day such a decision is asked and waits its
   time while the work goes on, and at its end the experts' shared pick or the recommended option
   is taken. A night never takes one so: nobody is there to answer, and every wait would end in
   a pick that nobody made. The builder knows it is night from the `night: yes` line of its brief,
   and `decisions.py ask` refuses a task whose brief has it. So the builder writes each such
   decision into its report under "for the owner" and stops with the line `the plan ends on a
   decision of the owner's` (`stages/plan.md`, step 5). Record the question, in the owner's
   terms, in the item's backlog file and in the night report, remove the worktree and the
   branch, write the state `dropped`, and take the next candidate. This is the filter that
   matters: an item only looks decision-free until someone plans it. Try three candidates at
   most.
5. **The night report**, `night/YYYY-MM-DD.md` in the folder `project.py state-dir` prints: for the
   draft, what the owner gets, the plan's path, why no decision was needed, and what it will not
   verify; for each item dropped in step 4, its question; for the brake, the drafts that wait,
   each with a verdict and its reason:
   - **run now**: the code the plan names is as it was;
   - **replan**: the files the plan names changed on the base branch since the draft;
   - **drop**: the item is gone from the backlog or another branch took it.
   Write the draft's state as `drafted`. When its report says the plan needs a session (a careful
   or a large plan), say so in the night report: the draft stands, and `/lem build` opens the
   plan talk's companion at once (`stages/new.md`), then a builder leads the build.

In the morning `/lem status` opens with the night report, while it is of that night or the one
before and names a draft that is still `drafted`. The owner starts a draft with `/lem build
<task>`, or says hold or drop.
