# The rules of nine pure functions at the unit level, and the criteria's tests once in a landing

careful: yes, because "A criterion's test is taken as its proof when it is not" is in reach: task 3 lets the checks take the polish pass's run of the criteria's tests in place of their own, and a wrong condition there counts a run on another tip or another contract as the proof.

## Acceptance criteria

Size: full, because two parts change: the tests of nine rules of `project.py` move to the unit level, and the landing's checks take the polish pass's result of the criteria's tests.

1. Each of the nine rules of `project.py` (`type_line`, `ticket_owed`, `braces`, `glob_regex`, `investigation_form`, `read_form`, `start_form`, `talk_start_form`, `talk_form`) is checked by unit cases that call the function: the line `type: fix` with no reason is refused with "names the type without its reason" by a call of `type_line`, with no `lem project` process.
2. A shell check of one of the nine rules leaves `tests/lem-settings.sh` only when a unit case holds the same rule, and each command that reads such a rule keeps one journey through the real command: the refusals of an investigation's record become unit cases, and the block keeps one `lem project log` of an investigation that is written and one that is refused with exit 1 and writes nothing.
3. When the checks start on the commit the polish pass ended on, they take the pass's result of the criteria's tests and run them no second time:
   1. The polish pass of a task commits one fix, and ends on commit `a1b2c3d`.
   2. `lem land polish SLUG --done` runs the criteria's tests: each passes on `a1b2c3d` and fails on the base commit.
   3. `lem land checks SLUG` starts on `a1b2c3d`, and its commands are green.
   4. The checks run no criteria's test, and their record says that they took the result of the polish pass at `a1b2c3d`.
4. The checks run the criteria's tests themselves in every other case: when a commit came after the one the pass ended on (a builder's repair of a failed check), when the pass made no commits, and on the fast track, which has no pass. A task whose pass ended on `a1b2c3d` and whose branch is now at `e4f5a6b` gets its criteria's tests run by the checks.
5. The polish pass keeps its own run of the criteria's tests and its own message: a commit of the pass that breaks a criterion's test is refused by `lem land polish SLUG --done` with "after the polish pass the tests of the criteria do not hold", as before this change.
6. The pull request of this task gives the checks, and the seconds of each suite it changed, on the base commit and on the branch.

## How it works

The checks decide where the result of the criteria's tests comes from.

```mermaid
flowchart TD
  A["The commands of the checks are green"] --> B{"The fast track?"}
  B -->|"yes"| R["The checks run the criteria's tests"]
  B -->|"no"| C{"The pass made commits?"}
  C -->|"no"| R
  C -->|"yes"| D{"The tip is the commit the pass ended on?"}
  D -->|"no"| R
  D -->|"yes"| E{"The criteria's record is the one the pass read?"}
  E -->|"no"| R
  E -->|"yes"| T["The checks take the pass's result, and say so"]
```

## Tasks

1. **The rules of the task and of the log at the unit level.** Unit cases for `type_line`, `ticket_owed`, `investigation_form`, `read_form`, `start_form`, `talk_start_form` and `talk_form`, each a call of the function, in the unit file of `project.py` that holds a task's rules (`tests/unit/test_task.py`, or a file beside it when that one says it holds other things). Each refusal the shell checks of these rules hold today gets its case, with the words of its message. Then the shell checks in `tests/lem-settings.sh` that only test such a rule go, and each command keeps one journey: `lem project state` with one type line written and one refused, `lem project log` with one record of each form written and one refused with exit 1 and nothing appended, `lem project tasks` with what it gives of a type, a talk, an investigation and a ticket. A shell check that also holds a fact only the real command shows (the event log not growing, the exit status, `tasks` reading the newest record) keeps that fact in the journey. Serves criteria 1 and 2. Files: `tests/unit/test_task.py` (or its neighbor), `tests/lem-settings.sh`.
2. **The rule picker's two rules at the unit level.** Unit cases for `braces` and `glob_regex`: a brace inside a brace, a brace with no comma, `**` as a whole segment and inside a name, `*` and `?` inside one segment, a dot file, a class in brackets and its `!`. The rule picker's shell checks in `tests/lem-settings.sh` that only test a glob's match go; `lem project rules` keeps one journey through the real command, with a rule file found through a link and one in a subfolder, which only the file system shows. Serves criteria 1 and 2. Files: `tests/unit/test_settings.py` (or a unit file of the rules beside it), `tests/lem-settings.sh`.
3. **The checks take the polish pass's result.** `cmd_polish` keeps in the landing's record, with `after` and `commits`, the result of its run of `lem criteria red` and the state of the criteria's record it ran against (the number of the newest approval and the count of recorded changes of a criterion, from `criteria.json` and `lem decisions changes`). A pure function of `land.py` decides, from the polish record, the tip, the fast track and the criteria's record now, whether the checks take that result; `cmd_checks` calls it, and either keeps the taken result in `checks.criteria` with a field that names the pass and its commit, or runs `criteria_red` as today. The polish pass's own run and its refusal stay as they are. Unit cases in `tests/unit/test_land.py` for each branch of the chart; in `tests/lem-land-review.sh`, the journey that already runs the pass with commits and then the checks shows one `task.red` event from the pass and none from the checks, with the record's field. Serves criteria 3, 4 and 5. Files: `skills/lem/scripts/land.py`, `tests/unit/test_land.py`, `tests/lem-land-review.sh`.
4. **The documents.** Each text the change makes false: the polish pass's step (`skills/lem/stages/polish.md`), the checks' step of the landing (`skills/lem/stages/land.md`, step 4, "Each criterion's tests pass on the branch and fail on the base commit"), what green means (`docs/pull-request.md`, where it names the check of the criteria), the docstring of `cmd_checks`, and the top comment of each block whose checks moved (`tests/lem-settings.sh` says which rules are unit cases). `python3 tests/pick.py --check` passes with any new unit file. Serves no criterion.
5. **The seconds before and after.** On the branch's last commit, run each suite the change edited (`lem-settings`, `lem-land-review`, `unit`) once on the base commit and once on the tip, back to back on this machine, with `LEM_TEST_TIMES=FILE`, each in a throwaway worktree of its commit, and write a table of the suite, its `collected N` and its seconds before and after into `notes.md` in the task directory, for the pull request. Serves criterion 6. Files: `notes.md` in the task directory only.

## Decisions

- **The checks take the result only when the criteria's record is the one the pass read** (task 3, the last node of the chart). The failure it prevents: a pull request green on a contract the tests never ran against. The input: an approval or a recorded change of a criterion written between `polish --done` and `checks` with no commit on the branch. Realistic here: rarely; a recorded change edits the plan, which is a commit and moves the tip, so only an approval written in the landing reaches it. What breaks without it: in that one case the checks pass a plan whose criteria differ from the record, which `lem criteria red` refuses. Its cost on a small task: none; the fast track has no pass, and the comparison reads two files the step reads anyway. Kept, for the plan talk to argue.
- **The tip alone says that the code is the same.** `lem criteria red` takes its base commit as the merge-base of the tip and origin's base branch (`cmd_red` in `criteria.py`), and a base branch that moved on keeps that merge-base for the same tip. So the same tip with the same record gives the same run, and no other key (the base, the time) is compared.
- **Criteria 1, 2 and 5 are held by the suite**, not by a test of their own: a unit case of a rule that exists on the base commit passes there too, and so does the polish pass's refusal, which this change keeps, so `lem criteria red` would refuse either as no proof. Their lines say `- no test: the change keeps behavior; the suite holds it`, and the review reads the moved checks against the unit cases.
- **Criterion 6 is the pull request's evidence**, with `- no test:`: it is a fact of this task's pull request, not a rule of Lem.
- **The seconds are measured back to back** (task 5): a time from another day's run on another load says nothing about this change. The rule of `AGENTS.md` that a block is never run to count it is about counts; the counts before are the base's `collected N`, read in the same run.
- **The old plan of `tests-at-the-unit-level` is not read**: its task directory is another task's, and the backlog item gives what was approved.

## What it will not verify

- The seconds the checks save in a real landing of another project: task 5 measures this repository's suites only, and a landing's time depends on the project's tests.
