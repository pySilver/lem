# build

The lead's second stage. Each task of the plan gets a fresh builder with a context of its own.
That is the owner's practice ("I usually start fresh executor for every task", 2026-11-14), and
one run shows why: with one agent for each of 14 coarse tasks, an agent's context peaked at 715k
tokens at the median, 252k to 967k (mybaze, 2026-09-29/30, from that project's run notes). A lead
that plans, briefs and reports while it also writes several tasks loses the plan when its context
fills.

## You coordinate

You write no code, also for a plan of one task: that task gets a fresh builder too. The owner's
ruling has no threshold ("I usually start fresh executor for every task.. since forever",
2026-11-14), and a lead
that builds carries the plan, the persona read and its own code in one context. A careful or
large plan comes here once its plan talk is done (`stages/plan.md`, step 3), and its tasks are
built like any others: the review comes at the landing, which reads the whole change. The
harness file says whether a builder can start builders in your agent; when your agent refuses
you the start of one, write the state `blocked` with that refusal, and stop.

1. **One builder per task of the plan**, through `spawn-builder`, in the task's worktree, one
   after the other unless two tasks touch no common file. Its brief names, by path:
   - the worktree;
   - the plan file and the task's section, with the acceptance criteria the task serves: the builder
     writes at least one test for each, one that fails without its change, except for a criterion
     whose change keeps behavior (a rename, a bump, a refactor), which the whole suite holds at
     the checks;
   - what the change is for, in the forms it was settled in: the `## Outcome` of `task.md` (its
     story of Today and After, and its chart), each criterion's case, and the plan's `## How it
     works` chart. They are the builder's contract beside the prose: where its reading of the
     task's section and a story or a chart differ, the story and the chart are right, and it says
     so in its report;
   - the rule files that cover the files it will touch, as `lem project rules FILE ...`
     prints them for the files the plan names for the task, and the project's lessons;
   - the report file, `reports/NN-<task>.md` in the task directory, and, for a task that changes
     what a person sees or builds a flow, `SKILL_DIR/prompts/writing.md` for the picture and the
     chart its report carries;
   - the tests it runs: those of the files it changes and of their direct callers, and never the
     whole suite, also not for a change that keeps behavior. The whole suite runs one time, in the
     checks before the pull request (`stages/land.md`, step 4), and it is the proof for such a
     change. The owner: "what worked for us is to run only subset of tests during plan execution,
     not the whole suite that takes ages. whole test suite run at the very late stage"
     (2026-11-17);
   - when the settings' `checks.serial` names commands (`lem project show`), those commands, and the
     line that runs a test of such a suite: `lem project --repo WORKTREE
     serial -- COMMAND`, with `SKILL_DIR` and `WORKTREE` written out. Two tasks cannot run such a
     test at the same time (fixed ports, one database, a browser), and several builders may run at one moment, so
     it runs under that one lock and never bare: "e2e is a bit of different beast as it may have
     troubles to execute when multiple worktrees wants them" (the owner, the same day).
   The rest a builder has with it: what it checks before it reports, how it commits, what it
   never does, and the report's form (what it did in three lines; proofs, each command with the
   exact last line of its output; what it did not verify; the decisions it took that the plan
   did not; the defects it saw outside its task). The harness file says how those standing rules
   reach a builder in your agent.
   Read the report file, never a summary of it. When a builder's reply is the report itself,
   because its agent refused it the write, put that text into the report file word for word.
   Write the state `building` with the line `task N of M` when a builder starts, and log its
   start for the board, `lem project --repo WORKTREE log SLUG
   builder.start "job=task N of M"`: two builders may run at one time, and a state block names
   only the newest.
2. **A builder that stops** reports why in its file. Where it goes depends on what stopped it:
   - *a failure nobody can explain after two tries*: the `lem-root-cause` skill, before
     a third try. A task that came from a bug had that method once already, before its criteria
     (`prompts/investigator.md`): read its `investigation.md` first, since the failure may be
     what else the same cause reaches;
   - *an approach that failed twice*: it is not tried a third time with a patch. State the problem
     again in plain terms, name what the two tries assumed, and brief the next builder with a
     different approach and why it avoids that assumption;
   - *a choice the plan did not see*: "A choice in the build" below. It is not a question for
     the reviewer, and not for the owner.
   A builder's report also lists the decisions it took that the plan did not. Write each one into
   the record, as the next section says, before the next builder starts.
3. **Go on to "The report"** when every task has its report.

## A choice in the build

A surprise in the build asks the owner nothing: the ladder decides it, its pick is taken at once,
with him there or away, and he reads it at the pull request. Only the circuit breaker stops the
task (`stages/breaker.md`). A decision of the plan takes these steps too (`stages/plan.md`, step
5): there is one path for every decision. Every decision goes into the task's record through one
script, which also puts it on the board:

```bash
lem decisions --repo WORKTREE log SLUG --what TEXT --chose TEXT --why TEXT --by lead [--undo TEXT]
```

A criterion the owner approved, or that the lead's read froze on the standard track from a complete
request (`lem criteria approved SLUG`), changes in the plan only with its own record, written
before the commit that changes it, with its text before and after:

```bash
lem decisions --repo WORKTREE criterion SLUG (--changed N --was TEXT --now TEXT | --added N --now TEXT | --removed N --was TEXT) --why TEXT (--decision ID | --by lead|personas [--said TEXT])
```

N is the criterion's number as the criteria stand after every earlier change;
`lem decisions changes SLUG` gives them, and the command refuses a `--was` that is not the text
of criterion N then. `--decision ID` names the decision of the record that led to it: a pick of the
ladder, or the owner's help on a breaker; a decision the personas settled is `--by personas --said
"who picked what"`, and the lead's own change that is nobody's decision, such as a typo in an
example, is `--by lead`. `criteria.py` refuses the plan until its criteria are the expected ones,
word for word, and the pull request is not green for each change but one his help led to. A plan's
`Size:` line always says `full`, and `criteria.py` refuses a plan that says `Size: small`: a build
never moves a task from the standard track to the fast track, which has no plan, and the track is
no choice of this section. A plan that departs from a direction (`directions.md`) is a decision of
this section too, with the direction in `--what`.

1. **The criteria and the directions stay true**: decide it yourself, from the code, the settings
   and the rulings, and log it with `--by lead` and `--undo`, what it would take to undo it.
2. **Otherwise it is in doubt**: `stages/ladder.md`, read at the first such decision. The ladder
   always ends in a pick: log it as that file says, read the pick against each criterion, record a
   criterion it changes with `--decision ID`, change the plan in the commit that builds it, and go
   on. A pick that changes the rule of an approved criterion, or the next step that a later "no"
   cannot reverse, is no pick to take: the breaker trips (`stages/breaker.md`).

A builder that is not the lead and meets such a choice asks nobody: it stops its task with the
question in its report, with the options and what it would choose, and the lead takes it from
there by these steps.

## The report

The lead's last act, and also what it does before any other stop. The landing reads this file
and the state block and nothing else of the build, and writes the pull request's notes from it.
Write `report.md` in the task directory, whole, each time, each part below under a heading of its
name (`## What the owner gets`): the merge agent's review of the task tells that part. A path in it is
relative to the repository's root, never a path inside the worktree: the worktree is gone when the
owner reads.

- **what the owner gets**, in one or two sentences, and how to see it. When behavior changed, the
  run that shows it follows them, told as `prompts/writing.md` tells a story, with the chart of a
  new flow and the builders' pictures of `media/`: the owner's "What was built" opens with this part;
- **the criteria**: each criterion of the plan with the tests that hold it. Before the report, write
  under each criterion in the plan its tests (`- test: ...`, or `- no test: REASON` for a criterion
  no test can hold, such as a sentence of a document, and `- no test: the change keeps behavior; the
  suite holds it` for a rename, a bump or a refactor, which the checks prove with the whole suite
  before the pull request), commit
  that, and run
  `lem criteria record SLUG` and then `lem
  criteria red SLUG`. The second one runs each criterion's tests in a worktree
  of its own, on the branch and on the base commit with only the named test files laid over it; the
  task's worktree has to be clean and is not touched. A test that fails there on the branch, that
  passes on the base commit too, or that does not start on the base commit does not hold its
  criterion: name every file the test needs, one by one. Its `run_without` lists the files of the
  branch that the base run lacked, which the check takes for the change: a helper of a test in that
  list means the test's failure proved nothing, and the helper belongs among the criterion's files.
  Repair what the check names before the task is `ready`, and give its last line here. A project
  whose tests need more than a fresh worktree has says what in the settings' `checks.setup`, which
  `lem project worktree` runs in each worktree it makes; when that is missing, it is an outside
  defect for your report, not yours to set;
- **not verified**: what you could not or did not check;
- **decisions**: each one taken without the owner, with why and what it would take to undo, by
  its number in `lem decisions list SLUG`. Each is in that record before the report: the pull
  request takes them from there, an important one with its story and its chart;
- **held**: what the task waits on when its state is `held`: the criteria with the answers that
  flagged them, or the breaker by its number, with its cause in one line. Leave the heading out
  when there is none;
- **outside defects**: each defect seen in code outside the task, with its file and one line on
  what is wrong. Do not fix it and do not file it: the polish pass of the landing fixes the
  small ones in place and files the others in the backlog (`stages/land.md`, step 3), with those
  of the interview's `outside.md`;
- **worth a look**: up to three places of the change a person's eye is worth, each with why;
  and, for a careful task, whether the change holds a migration and how to revert it. The
  landing puts these into the pull request's notes (`stages/land.md`, step 6);
- **the commit subject**: one semantic line for the whole task (`type(scope): subject`). The
  landing makes it the pull request's title, and the one commit's subject where
  `branch.history` is `"squash"` (`stages/land.md`, steps 6 and 8);
- **the branch and its tip**: the branch's name and the commit `git -C WORKTREE rev-parse HEAD` prints.

Then write the state: `ready`, and the landing comes, a phase of its own (`prompts/session.md`,
"A change of phase"); or `held` or `blocked` with the line that says why, and wait in this session
for the owner.

Most real defects are found by the next builder on the same ground, not by a review
(convertiser-server's log of defects outside its tasks held 105 items after about 28 hours). So
the "outside defects" list is a main input, never an appendix.
