# build

You coordinate; builders build. A session that plans, briefs, lands and reports while it also
writes the code loses the plan when its context fills.

1. **One builder per task of the plan**, through `spawn-builder`, in the task's worktree, one
   after the other unless two tasks touch no common file. Its brief names:
   - the plan file and the task's section, by path;
   - the style guide files that cover the files it will touch, and the project's lessons, by path;
   - the checks it runs before it reports: the tests of the files it wrote or edited, and the
     formatter, linter and type checker the project's `AGENTS.md` names; never the whole suite
     unless the plan says so;
   - that it commits its own work on the task's branch with a semantic message, and never pushes,
     merges or changes another branch;
   - the report file, `reports/NN-<task>.md` in the task directory, and its form.
2. **The report form.** A builder's last act is to write the report file, and its reply is the
   path:
   - what it did, in three lines;
   - proofs: each command it ran with the exact last line of its output;
   - not verified: what it could not or did not check;
   - decisions it took that the plan did not, each with its reason;
   - defects it saw in code outside its task and did not touch.
   Read the report file, never a summary of it. Copy its decisions into `decisions.md` and its
   outside defects into the project's backlog path as items, or into the report to the owner when
   the project has no backlog.
3. **A careful task is reviewed before the next one starts.** Send the diff of that task to
   `second-opinion` with the plan section and the style guide files: does the change deliver the
   task, and is any existing caller or reverse path left inconsistent? Must-fix items go back to a
   builder. A task that is not careful is not reviewed here; its review comes from the queue after
   the landing.
4. **A builder that is blocked** reports the blocker in its file. Decide it if it is yours to
   decide; if it is a held decision, treat it as `plan.md` step 4 does and keep the other tasks
   moving.
5. **When every task has its report, go on to `land`.** Write a block in `state.md`.

Most real defects are found by the next builder on the same ground, not by a review
(convertiser-server's log of defects outside its tasks held 105 items after about 28 hours). So a builder's "defects outside my
task" list is a main input, never an appendix.
