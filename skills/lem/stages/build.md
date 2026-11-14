# build

The lead's second stage. A builder builds its own plan. A session coordinates builders and writes
no code: a session that plans, briefs, reviews and reports while it also writes the code loses the
plan when its context fills.

## A builder: you build

1. **Task by task, in the plan's order.** For each task: write it, run the tests of the files you
   wrote or edited and the formatter, linter and type checker the project's `AGENTS.md` names,
   and commit on the task's branch with a semantic message. Never the whole suite unless the plan
   says so: the gate runs it at the landing.
2. **Write the state after each commit**: `building`, with the line `task N of M`.
3. **When you are blocked.** A defect you cannot explain after two tries goes to the
   `root-cause-investigator` skill before a third. An approach that failed twice is not tried a
   third time with a patch: write in `report.md` the problem in plain terms and what the two
   tries assumed, write the state `blocked`, and stop. Lem gives the task to a fresh builder
   with a different approach.
4. **Go on to "The report".**

## A session: you coordinate

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
2. **A careful task is reviewed before the next one starts.** Send the diff of that task to
   `second-opinion` with the plan section and the style guide files: does the change deliver the
   task, and is any existing caller or reverse path left inconsistent? Must-fix items go back to a
   builder. A task of a plan that is large and not careful is not reviewed here; its review comes
   from the queue after the landing.
3. **A builder that is blocked** reports the blocker in its file. A defect nobody can explain
   after two tries goes to the `root-cause-investigator` skill before a third. An approach that
   failed twice is not tried a third time with a patch: state the problem again in plain terms,
   name what the two tries assumed, and brief the next builder with a different approach and why
   it avoids that assumption. Decide it if it is yours to decide; if it is a held decision, treat
   it as `plan.md` does under "A held decision" and keep the other tasks moving.
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
- **outside defects**: each defect seen in code outside the task and not touched. Write each as an
  item in the project's backlog path, in the `backlog` skill's item format, commit the items on
  the task's branch, and list their paths here. A project with no backlog gets the defects
  themselves in this list;
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
