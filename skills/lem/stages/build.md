# build

The lead's second stage. Each task of the plan gets a fresh builder with a context of its own.
That is the owner's practice ("I usually start fresh executor for every task", 2026-11-14), and
one run shows why: with one agent for each of 14 coarse tasks, an agent's context peaked at 715k
tokens at the median, 252k to 967k (mybaze, 2026-09-29/30, from that project's run notes). A lead
that plans, briefs and reports while it also writes several tasks loses the plan when its context
fills.

## A builder with a plan of one task: you build it

Your brief says `lead: builder` and the plan has one task: you wrote the plan, and you are its
one builder. A session never takes this section: its lead writes no code, so its one task gets a
builder of its own, as the next section says.

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

You write no code. A builder leads this way as a session does, and a session lead builds its
tasks like any other lead: its plan talk is done (`stages/plan.md`, step 4), and the review comes
at the landing, which reads the whole change. The harness file says whether a builder can start
builders in your agent, and what to do when it cannot.

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
2. **A builder that stops** reports why in its file. Where it goes depends on what stopped it:
   - *a failure nobody can explain after two tries*: the `lem-root-cause` skill, before
     a third try;
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
step that a later "no" cannot reverse. The owner's rule, 2026-11-16: the personas first, a clear
choice taken and logged, an unclear one to him, and with no answer in 15 minutes the recommended
action, logged so that the pull request shows it. Every decision goes into the task's record
through one script, which also puts it on the board:

```bash
python3 SKILL_DIR/scripts/decisions.py --repo WORKTREE log SLUG --what TEXT --chose TEXT --why TEXT --by lead|personas [--said TEXT] [--undo TEXT]
```

A story the owner approved (`stories.py approved SLUG`) changes in the plan only with its own
record, written before the commit that changes it, with its text before and after:

```bash
python3 SKILL_DIR/scripts/decisions.py --repo WORKTREE story SLUG (--changed N --was TEXT --now TEXT | --added N --now TEXT | --removed N --was TEXT) --why TEXT (--choice ID | --by lead|personas [--said TEXT])
```

N is the story's number as the stories stand after every earlier change;
`decisions.py changes SLUG` gives them, and the command refuses a `--was` that is not the text
of story N then. `--choice ID` names the choice of step 2 that led to it, once it is answered or
taken by timeout; without a choice it is the personas' clear pick (`--by personas --said`), or
the lead's own (`--by lead`) for a change that is nobody's choice, such as a typo in an example.
A story whose rule changes, comes or goes is never the lead's alone: it takes step 2 below, the
personas first. The stories script
refuses the plan until its stories are the expected ones, word for word, and the pull request is
not green for each change. The kind (`Kind:`) is the owner's only: a feature that has to become
a correction, or the other way, is a held decision. A plan that departs from a direction
(`directions.md`) is a decision of this section too, with the direction in `--what`.

1. **The stories and the directions stay true**: decide it yourself, from the code, the settings
   and the rulings, and log it with `--by lead` and `--undo`, what it would take to undo it.
2. **Otherwise the persona panel first**, with the personas the choice concerns, in its reviewing
   mode: each option as what a person would see and what it costs, and a short check of outside
   facts when one fact decides it. It asks the owner nothing and decides nothing.
   - *A clear answer* (the personas agree, nobody in doubt): take it, log it with
     `--by personas --said "who picked what"`, and go on. A story that the choice changes gets
     its record, `decisions.py story ... --by personas --said "who picked what"`; change the
     story in the plan in the same commit as the code. The pull request is not green for it.
   - *An unclear answer* (the personas split, or one is in doubt), or a question of what the owner
     meant or of taste, which the personas do not answer for him: ask him.

     ```bash
     python3 SKILL_DIR/scripts/decisions.py --repo WORKTREE ask SLUG --what TEXT --option TEXT --option TEXT --recommended TEXT --why TEXT --said TEXT [--irreversible data|system|person|money]
     ```

     `--said` holds what the personas answered, or why they were not asked. A choice carries no
     story. Whichever way it ends, by his answer, by a decision of his that is none of the
     options, or by the timeout, read what was taken against each story: when one no longer
     holds, or a story has to come or go, record it with `decisions.py story ... --choice N`,
     and change the story in the plan in the commit that builds the option. A forgotten record
     does not pass: the gate refuses a plan whose stories are not the expected ones. The choice waits the
     settings' `flow.decision_wait` (15 minutes unless the project says otherwise). Tell Lem that
     it waits: in a session, `tell-coordinator` with the line `lem: SLUG choice N waits`. A
     builder that leads has no `tell-coordinator` (the harness file defines it from a task's
     session only), so its choice reaches Lem at Lem's next turn, through `decisions.py pending`,
     and may end its wait before the owner sees it.
3. **Go on with the work that does not depend on the choice.** Between two of your tasks, and
   before you start one that depends on it, run `decisions.py --repo WORKTREE wait SLUG N`. It
   returns when the owner answered, when the wait is over, or after nine minutes: run it again
   while it says `still waits`, when nothing else is left to do. When the wait is over, run
   `decisions.py --repo WORKTREE timeout SLUG N`: the recommended option is taken, and the pull
   request is not green for it. `decisions.py list SLUG` shows each decision as it stands; an
   answer that came after the timeout and differs from what was taken is the owner's correction:
   build his answer, and log it with `--by lead` and why.
4. **A step that a later "no" cannot reverse is never taken by timeout.** The four kinds, and no
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
- **decisions**: each one taken without the owner, with why and what it would take to undo, by
  its number in `decisions.py list SLUG`. Each is in that record before the report: the pull
  request takes them from there;
- **held**: each decision that is the owner's, in the form `plan.md` gives under "A held
  decision", and each choice of an irreversible step that still waits, by its number. Leave the
  heading out when there is none;
- **outside defects**: each defect seen in code outside the task, with its file and one line on
  what is wrong. Do not fix it and do not file it: the closing pass of the landing fixes the
  small ones in place and files the others in the backlog (`stages/land.md`, step 3);
- **worth a look**: up to three places of the change a person's eye is worth, each with why;
  and, for a careful task, whether the change holds a migration and how to revert it. Lem
  copies these into the pull request;
- **the commit subject**: one semantic line for the whole task (`type(scope): subject`). Lem
  uses it when the project lands a task as one commit;
- **the branch and its tip**: the branch's name and the commit `git rev-parse HEAD` prints.

Then write the state (`ready`, or `held`, `blocked` or `planned` with the line that says why),
and tell Lem. A builder's reply is the report's path and nothing else. A session uses
`tell-coordinator`.

When your agent refuses you the write of `report.md`, do not go around the refusal. Add the line
`report in the reply` to the state, and make your reply the whole report, in this form: Lem
writes the file from it.

Most real defects are found by the next builder on the same ground, not by a review
(convertiser-server's log of defects outside its tasks held 105 items after about 28 hours). So
the "outside defects" list is a main input, never an appendix.
