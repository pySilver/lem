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
   - the rule files that cover the files it will touch, as `lem project rules FILE ...`
     prints them for the files the plan names for the task, and the project's lessons;
   - the report file, `reports/NN-<task>.md` in the task directory;
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
     the reviewer.
   A builder's report also lists the decisions it took that the plan did not. Write each one into
   the record, as the next section says, before the next builder starts.
3. **Go on to "The report"** when every task has its report.

## A choice in the build

A surprise in the build stops the task for the owner's wait at most, never longer, except for a
step that a later "no" cannot reverse. A decision of the plan takes these steps too
(`stages/plan.md`, step 5): there is one path for every decision. Every decision goes into the
task's record through one script, which also puts it on the board:

```bash
lem decisions --repo WORKTREE log SLUG --what TEXT --chose TEXT --why TEXT --by lead [--undo TEXT]
```

A criterion the owner approved, or that the lead's read froze on the standard track from a complete
request (`lem criteria approved SLUG`), changes in the plan only with its own record, written
before the commit that changes it, with its text before and after:

```bash
lem decisions --repo WORKTREE criterion SLUG (--changed N --was TEXT --now TEXT | --added N --now TEXT | --removed N --was TEXT) --why TEXT (--choice ID | --by lead|personas [--said TEXT])
```

N is the criterion's number as the criteria stand after every earlier change;
`lem decisions changes SLUG` gives them, and the command refuses a `--was` that is not the text
of criterion N then. `--choice ID` names the choice of step 2 that led to it, once it is answered or
taken by timeout; a decision the personas settled is `--by personas --said "who picked what"`,
one another level of the ladder settled is `--by lead` with its number in `--why`, and so is the
lead's own change that is nobody's choice, such as a typo in an example.
A criterion whose rule changes, comes or goes is never the lead's alone: it climbs the ladder
(step 2). `criteria.py`
refuses the plan until its criteria are the expected ones, word for word, and the pull request is
not green for each change. A plan's `Size:` line always says `full`, and `criteria.py` refuses
a plan that says `Size: small`: a build never moves a task from the standard track to the fast
track, which has no plan, and the track is no choice of this section.
 A plan that departs from a direction
(`directions.md`) is a decision of this section too, with the direction in `--what`.

1. **The criteria and the directions stay true**: decide it yourself, from the code, the settings
   and the rulings, and log it with `--by lead` and `--undo`, what it would take to undo it.
2. **Otherwise it is in doubt**: `stages/ladder.md`, read at the first such decision. With the
   owner, a decision that went past the personas, and a step that a later "no" cannot reverse,
   end as his card:

   ```bash
   lem decisions --repo WORKTREE ask SLUG --what TEXT --case STEPS --case-was reproduced|derived --cause TEXT --option TEXT --option TEXT --recommended TEXT --why TEXT --said TEXT [--irreversible data|system|person|money]
   ```

   `--case` is one concrete case in numbered steps that ends badly, with real names and values
   and where each step was read, one step to a line; `--case-was` says whether you reproduced
   it or derived it; `--cause` is one line on why the case became possible and how far the same
   cause reaches. They go above the owner's card, so that he decides from one run and not from
   the code. `--recommended` is the ladder's pick, and `--said` what each level answered. A
   choice carries no criterion. Whichever way it ends, by his answer, by a decision of his that
   is none of the options or taken when he went away, read what was taken against each criterion: when
   one no longer holds, or a criterion has to come or go, record it with `lem decisions
   criterion ... --choice N`, and change the criterion in the plan in the commit that builds the
   option. A forgotten record does not pass: the checks refuse a plan whose criteria are not the
   expected ones. The choice waits for his answer with no time limit, so tell Lem at once: `tell-coordinator` with
   the line `lem: SLUG choice N waits`, to the address of the brief's `coordinator:` line. The
   defender of a plan talk sends it from its companion, and a builder that leads sends it from
   Lem's own session; the harness file says what of that was checked. A brief with no
   `coordinator:` line has no address: the choice then reaches Lem at its next turn, through
   `lem decisions pending`.
3. **Go on with the work that does not depend on the choice.** Between two of your tasks, and
   before you start one that depends on it, run `lem decisions --repo WORKTREE wait SLUG N`. It
   returns when the owner answered, when the task runs without him (he said he is away; it then
   takes the ladder's pick, on a choice the experts advised the option every expert picked, and the pull
   request is not green for it), or after nine minutes: run it again while it says `still
   waits`, when nothing else is left to do. `lem decisions list SLUG` shows each decision as it
   stands; an answer that came after it was taken and differs from what was taken is the owner's correction:
   build his answer, and log it with `--by lead` and why.
4. **A step that a later "no" cannot reverse is never taken without his answer or by a level of
   the ladder**, with the owner or without him. The four kinds, and no
   other: it destroys or rewrites data outside the worktree (`data`); it writes to a system
   outside the repository beyond what the settings already allow, such as the tracker's ticket
   (`system`); it sends something to a person (`person`); it spends money (`money`). Ask it with
   `--irreversible` and the kind. Only the part of the plan that needs that step waits, however
   long; the rest goes on. When every task that is left needs it, write the report with the
   choice under "held", write the state `held` with the line `choice N waits for the owner`, and
   stop: Lem starts a lead again after his answer.

A builder that is not the lead and meets such a choice asks nobody: it stops its task with the
question in its report, with the options and what it would choose, and the lead takes it from
there by these steps.

## The report

The lead's last act, and also what it does before any other stop. Lem reads
this file and the state block and nothing else of the task, and writes the owner's report from it.
Write `report.md` in the task directory, whole, each time, each part below under a heading of its
name (`## What the owner gets`): the owner's page of the task takes that part. A path in it is
relative to the repository's root, never a path inside the worktree: the worktree is gone when the
owner reads.

- **what the owner gets**, in one or two sentences, and how to see it;
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
  request takes them from there;
- **held**: what the task waits on when its state is `held`: the criteria with the answers that
  flagged them, or the irreversible choice that every task left depends on, by its number. A
  choice that waits while the work goes on is in the record, not here. Leave the heading out when
  there is none;
- **outside defects**: each defect seen in code outside the task, with its file and one line on
  what is wrong. Do not fix it and do not file it: the polish pass of the landing fixes the
  small ones in place and files the others in the backlog (`stages/land.md`, step 3), with those
  of the interview's `outside.md`;
- **worth a look**: up to three places of the change a person's eye is worth, each with why;
  and, for a careful task, whether the change holds a migration and how to revert it. Lem
  copies these into the pull request;
- **the commit subject**: one semantic line for the whole task (`type(scope): subject`). Lem
  uses it when the project lands a task as one commit;
- **the branch and its tip**: the branch's name and the commit `git rev-parse HEAD` prints.

Then write the state (`ready`, or `held`, `blocked` or `planned` with the line that says why),
and stop. A builder that leads tells Lem by its reply, which is the report's path and nothing
else, and sends no mailbox line for it: its reply already wakes Lem, and a line too would wake it
twice for one stop. Its only line is `choice N waits`. The defender of a
plan talk has no such reply and uses `tell-coordinator` (`prompts/defender.md`).

When your agent refuses you the write of `report.md`, do not go around the refusal. Add the line
`report in the reply` to the state, and make your reply the whole report, in this form: Lem
writes the file from it.

Most real defects are found by the next builder on the same ground, not by a review
(convertiser-server's log of defects outside its tasks held 105 items after about 28 hours). So
the "outside defects" list is a main input, never an appendix.
