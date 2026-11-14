# build

The lead's second stage. Each task of the plan gets a fresh builder with a context of its own.
That is the owner's practice ("I usually start fresh executor for every task", 2026-11-14), and
one run shows why: with one agent for each of 14 coarse tasks, an agent's context peaked at 715k
tokens at the median, 252k to 967k (mybaze, 2026-09-29/30, from that project's run notes). A lead
that plans, briefs and reports while it also writes several tasks loses the plan when its context
fills.

## A plan of one task: you build it

You wrote the plan, and you are its one builder.

1. **Build the task.** Write it, run the tests of the files you wrote or edited and the
   formatter, linter and type checker the project's `AGENTS.md` names, and commit on the task's
   branch with a semantic message. Never the whole suite unless the plan says so: the gate runs
   it at the landing. Write the state `building` with the line `task 1 of 1`.
2. **When you stop without the outcome**, "A builder that stops" below says where each kind of
   stop goes. Write in `report.md` what you tried and what it assumed, write the state `blocked`,
   and stop: Lem gives the task to a fresh builder.
3. **Go on to "The report".**

## A plan of more tasks: you coordinate

You write no code. A builder leads this way as a session does; the harness file says whether a
builder can start builders in your agent, and what to do when it cannot.

1. **One builder per task of the plan**, through `spawn-builder`, in the task's worktree, one
   after the other unless two tasks touch no common file. Its brief names:
   - the plan file and the task's section, by path;
   - the style guide files that cover the files it will touch, and the project's lessons, by path;
   - the checks it runs before it reports: the tests of the files it wrote or edited, and the
     formatter, linter and type checker the project's `AGENTS.md` names; never the whole suite
     unless the plan says so;
   - that it commits its own work on the task's branch with a semantic message, and never pushes,
     merges or changes another branch;
   - the report file, `reports/NN-<task>.md` in the task directory, and its form: what it did in
     three lines; proofs, each command it ran with the exact last line of its output; what it did
     not verify; decisions it took that the plan did not, each with its reason; defects it saw in
     code outside its task and did not touch.
   Read the report file, never a summary of it. Write the state `building` with the line
   `task N of M` when a builder starts.
2. **A careful task is reviewed before the next one starts.** This is the session's step. Send
   the diff of that task to `second-opinion` with the plan section and the style guide files: does
   the change deliver the task, and is any existing caller or reverse path left inconsistent?
   Must-fix items go back to a builder. A task of a plan that is not careful is not reviewed here;
   its review comes from the queue after the landing.
3. **A builder that stops** reports why in its file. Where it goes depends on what stopped it:
   - *a failure nobody can explain after two tries*: the `root-cause-investigator` skill, before
     a third try;
   - *an approach that failed twice*: it is not tried a third time with a patch. State the problem
     again in plain terms, name what the two tries assumed, and brief the next builder with a
     different approach and why it avoids that assumption;
   - *a question of what the right outcome is* (what a person should see, which of two readings
     of the ask holds): the `panel` skill with the project's cast answers it. Write the answer in
     `decisions.md` and brief the next builder with it. It is not a question for the reviewer;
   - *a held decision*: treat it as `plan.md` does under "A held decision", and keep the other
     tasks moving.
4. **Go on to "The report"** when every task has its report.

## The report

The lead's last act, whichever kind it is, and also what it does before any other stop. Lem reads
this file and the state block and nothing else of the task, and writes the owner's report from it.
Write `report.md` in the task directory, whole, each time:

- **what the owner gets**, in one or two sentences, and how to see it;
- **done when**: each line of the plan's "done when" with the command or the look that shows it,
  and the exact last line of the command's output;
- **not verified**: what you could not or did not check;
- **decisions**: each one taken without the owner, with why and what it would take to undo. Add
  the same lines to `decisions.md`;
- **held**: each decision that is the owner's, in the form `plan.md` gives under "A held
  decision". Leave the heading out when there is none;
- **outside defects**: each defect seen in code outside the task, with its file and one line on
  what is wrong. Do not fix it and do not file it: the closing pass of the landing fixes the
  small ones in place and files the others (`stages/land.md`, step 3);
- **review risk**: `high` when the task was careful, or touches authentication, money, a
  migration, a security boundary or the gate's own tooling; `normal` otherwise. One line says
  which of these it was;
- **the commit subject**: one semantic line for the whole task (`type(scope): subject`). Lem
  uses it when the project lands a task as one commit;
- **the branch and its tip**: the branch's name and the commit `git rev-parse HEAD` prints.

Then write the state (`ready`, or `held`, `blocked` or `planned` with the line that says why),
and tell Lem. A builder's reply is the report's path and nothing else. A session uses
`tell-coordinator`.

Most real defects are found by the next builder on the same ground, not by a review
(convertiser-server's log of defects outside its tasks held 105 items after about 28 hours). So
the "outside defects" list is a main input, never an appendix.
