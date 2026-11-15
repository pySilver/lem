# build

The lead's second stage. Each task of the plan gets a fresh builder with a context of its own.
That is the owner's practice ("I usually start fresh executor for every task", 2026-11-14), and
one run shows why: with one agent for each of 14 coarse tasks, an agent's context peaked at 715k
tokens at the median, 252k to 967k (mybaze, 2026-09-29/30, from that project's run notes). A lead
that plans, briefs and reports while it also writes several tasks loses the plan when its context
fills.

## A builder with a plan of one task: you build it

Your brief says `lead: builder` and the plan has one task: you wrote the plan, and you are its
one builder. A session never takes this section. Its plan is careful, so its one task gets a
builder of its own and a review of its diff, as the next section says.

1. **Build the task.** Write it, with at least one test for each story of the plan: a test that
   fails on the base commit and passes with your change. A story no test can hold, such as a
   sentence of a document, gets none, and "The report" says how the plan records that. Run the tests of the files you wrote or edited and the
   formatter, linter and type checker the project's `AGENTS.md` names, and commit on the task's
   branch with a semantic message. Never the whole suite unless the plan says so: the gate runs
   it at the landing. Write the state `building` with the line `task 1 of 1`.
2. **When you stop without the outcome**, "A builder that stops" below says where each kind of
   stop goes. Write in `report.md` what you tried and what it assumed, write the state `blocked`,
   and stop: Lem gives the task to a fresh builder.
3. **Go on to "The report".**

## A plan of more tasks, or any plan of a session: you coordinate

You write no code. A builder leads this way as a session does; the harness file says whether a
builder can start builders in your agent, and what to do when it cannot.

1. **One builder per task of the plan**, through `spawn-builder`, in the task's worktree, one
   after the other unless two tasks touch no common file. Its brief names, by path:
   - the worktree;
   - the plan file and the task's section, with the stories the task serves: the builder writes
     at least one test for each, one that fails without its change;
   - the style guide files that cover the files it will touch, as `project.py rules FILE ...`
     prints them for the files the plan names for the task, and the project's lessons;
   - the report file, `reports/NN-<task>.md` in the task directory;
   - the whole suite, only when the plan says a task needs it.
   The rest a builder has with it: what it checks before it reports, how it commits, what it
   never does, and the report's form (what it did in three lines; proofs, each command with the
   exact last line of its output; what it did not verify; the decisions it took that the plan
   did not; the defects it saw outside its task). The harness file says how those standing rules
   reach a builder in your agent.
   Read the report file, never a summary of it. When a builder's reply is the report itself,
   because its agent refused it the write, put that text into the report file word for word.
   Write the state `building` with the line `task N of M` when a builder starts.
2. **A careful task is reviewed before the next one starts.** This is the session's step. Send
   the diff of that task to `second-opinion` with the plan section and the style guide files
   `project.py rules --range BASE..TIP` prints for it: does
   the change deliver the task, and is any existing caller or reverse path left inconsistent?
   Must-fix items go back to a builder. A task of a plan that is not careful is not reviewed here;
   its review comes from the queue after the landing.
3. **A builder that stops** reports why in its file. Where it goes depends on what stopped it:
   - *a failure nobody can explain after two tries*: the `lem-root-cause` skill, before
     a third try;
   - *an approach that failed twice*: it is not tried a third time with a patch. State the problem
     again in plain terms, name what the two tries assumed, and brief the next builder with a
     different approach and why it avoids that assumption;
   - *a question of what a person should see* (which of two results serves the people of the
     project better, where the ask and the rulings leave it open): the `lem-panel` skill in its
     reviewing mode, with the project's cast, gives the people's reading of the two results. It
     asks the owner nothing and decides nothing. Take the decision yourself with that reading,
     write it in `decisions.md` with what the personas said, and brief the next builder. It is
     not a question for the reviewer;
   - *a question of what the owner meant* (two readings of the ask that give the owner different
     things) or of taste: the personas do not answer for the owner, and neither do you. It is a
     held decision;
   - *a held decision*: treat it as `plan.md` does under "A held decision", and keep the other
     tasks moving.
4. **Go on to "The report"** when every task has its report.

## The report

The lead's last act, whichever kind it is, and also what it does before any other stop. Lem reads
this file and the state block and nothing else of the task, and writes the owner's report from it.
Write `report.md` in the task directory, whole, each time. A path in it is relative to the
repository's root, never a path inside the worktree: the worktree is gone when the owner reads.

- **what the owner gets**, in one or two sentences, and how to see it;
- **the stories**: each story of the plan with the tests that hold it. Before the report, write
  under each story in the plan its tests (`- test: ...`, or `- no test: REASON` for a story no
  test can hold, such as a sentence of a document), commit that, and run
  `python3 SKILL_DIR/scripts/stories.py record SLUG` and then `python3 SKILL_DIR/scripts/stories.py
  red SLUG`. The second one runs each story's tests in a worktree of its own, on the branch and
  on the base commit with only the named test files laid over it; the task's worktree has to be
  clean and is not touched. A test that fails there on the branch, that passes on the base
  commit too, or that does not start on the base commit does not hold its story: name every
  file the test needs, one by one. Its `run_without` lists the files of the branch that the base
  run lacked, which the check takes for the change: a helper of a test in that list means the
  test's failure proved nothing, and the helper belongs among the story's files. Repair what the
  check names before the task is `ready`, and give its last line here. A project whose tests need more than a fresh worktree has says what in the
  settings' `gate.setup`; when that is missing, it is an outside defect for your report, not
  yours to set;
- **not verified**: what you could not or did not check;
- **decisions**: each one taken without the owner, with why and what it would take to undo. Add
  the same lines to `decisions.md`;
- **held**: each decision that is the owner's, in the form `plan.md` gives under "A held
  decision". Leave the heading out when there is none;
- **outside defects**: each defect seen in code outside the task, with its file and one line on
  what is wrong. Do not fix it and do not file it: the closing pass of the landing fixes the
  small ones in place and proposes the others to the owner (`stages/land.md`, step 3);
- **review risk**: `high` when the task was careful, or touches authentication, money, a
  migration, a security boundary or the gate's own tooling; `normal` otherwise. One line says
  which of these it was;
- **the commit subject**: one semantic line for the whole task (`type(scope): subject`). Lem
  uses it when the project lands a task as one commit;
- **the branch and its tip**: the branch's name and the commit `git rev-parse HEAD` prints.

A session's lead adds the line `careful: read by a session` to its `ready` block, after the
second opinion on the plan and the review of each task: the landing asks for that line when
the owner called the task careful.

Then write the state (`ready`, or `held`, `blocked` or `planned` with the line that says why),
and tell Lem. A builder's reply is the report's path and nothing else. A session uses
`tell-coordinator`.

When your agent refuses you the write of `report.md`, do not go around the refusal. Add the line
`report in the reply` to the state, and make your reply the whole report, in this form: Lem
writes the file from it.

Most real defects are found by the next builder on the same ground, not by a review
(convertiser-server's log of defects outside its tasks held 105 items after about 28 hours). So
the "outside defects" list is a main input, never an appendix.
