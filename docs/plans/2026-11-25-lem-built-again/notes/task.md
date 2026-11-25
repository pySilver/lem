# Notes of the step `task`

What the step `task` needs in files it does not own, the local stand-in it built until each
exists, and what other steps may count on.

## For every step that acts on one named task: the release stop

Read the task's record through `lem.app.tasks.release.checked(state, slug, *, ends=False)`, not
`store.tasks.read`, in every command that acts on one named task (`land`, `criteria`,
`decisions`, `session`, `seat`). It sets the hold `release` once on a task two releases back and
refuses `release` with the way on (`/lem drop SLUG`, then `/lem resume SLUG`); `ends=True` is for a
command that ends the task or pays a step its end owes (the end of a merge, a drop, a tracker
step of the end), which goes on with the hold kept. `BEFORE` is in `lem.model.task.release`; a
release moves it (`AGENTS.md`, "A release", still names `src/lem/release.py`: `guides`).

## For `core` (`records/`)

1. **`Parked.held: OwnerHold | BreakerHold | Blocked | None = None`.** A park puts the hold it
   replaces aside, and the resume gives it back (a breaker that waited waits again). Meanwhile
   `app/tasks/park.py` writes it to `tasks/SLUG/parked.json` before the record, and the resume
   reads and removes it.
2. **The read of the request's one question has no owner hold.** `OwnerWait` has no value for it
   (`stages/new.md` step 1 asked it under the old `held "the request waits for one answer"`).
   Asked: `request` in `OwnerWait`, and `task read`'s `--wait` takes it (then the leaf's
   `Wait` and `model/task/read.py: WAITS`).
3. **The first line has no field.** `task read` says it (its envelope's `say`) and `task show`
   gives it, composed from the record and the task's files when asked
   (`app/tasks/first_line.py`). On `main` it was written once into the state event. A
   `Shape.first_line` written by `task read` would keep the line the session said.

## For `core` (`ports/tracker.py`): the parts of a tracker's step

The `Tracker` port has `read` and `step`; `lem issue` writes `assigned LOGIN` between the read of
who is signed in and the add, and reads the comments before it posts. The adapter gives the
parts (`origin`, `who`, `issue`, `comments`, `check`, `assign`, `unassign`, `comment`, `close`),
and the app reaches them through the local Protocol `lem.app.tasks.issues.facts.Issues`, with
the structs in `src/lem/adapters/tracker_gh_facts.py`. Asked: the methods on `Tracker` (or a
second Protocol `IssueTracker`), the four structs in `ports/`, and `FakeTracker` with them; then
`facts.Issues` and `facts.of` go.

## For `settings`

- `[tracker] kind`: `lem.app.tasks.tracker.kind_of(checkout)` reads it from the team's file with
  `settings.load.tables`, a stand-in until `Team` has a `Tracker` table.
- The plan file's name and folder (`[paths] plans`, `plan_file`): read the same way by the plan's
  commands of this step until `Team` has `[paths]`.

## For `land-base`

- **The start over.** `lem task move SLUG ready --start-over WHY` changes the landing's record
  itself (`model/task/ending.py: started_over`: the reviews archived, the reads and the standing
  merge cleared, the owner's merge ended with "the landing started over: WHY") and writes the
  journal line `the landing starts over: WHY` (`ending.START_OVER`). `lem land start` reads that
  newest line for `Started.start_over`. The phase is left as it was.
- **`project may-land` rows** (`unit:tests/unit/test_task.py:MayLand.*`) are moved to you: each
  landing step refuses `protected` itself.

## For `land-checks`: the drop stops the checks

`lem task move SLUG dropped` sends a term to the process the step lock names when its step is
`checks` (`app/tasks/drop.py: stop_checks`), then waits for the lock
(`store.steps.waited`). The checks' process must end its commands and let the lock go on a term,
as `land.checks_stop` on `main` did.

## For `sessions`

- Where a task's worktree is: `lem.app.tasks.where.worktree(workspace, slug)`, and its branch on
  the record, `Task.branch`; `lem task worktree SLUG --path` prints it.
- `lem session wait SLUG --first-line` prints the first line that `task read` said:
  `lem.app.tasks.first_line.said(workspace, record, named=True)` gives the form another session
  says.
- The rows of `seat show|failed|again` (`SeatCall`, `SeatCommands`, `FailedLine` of
  `test_task_rules.py`) are moved to you. A seat's block is `Blocked(seat=...)`: `task move`
  refuses every move over it but a drop, and `lem seat again` lifts it.

## For `owner`

- `lem task show SLUG` and `lem task list` give the mode the record keeps (`Task.mode`, a night
  task runs alone from its open); whether the owner is away now joins in `lem waiting`.
- The owner's checks of `tests/lem-state.sh` (his status, its watch, a task's span without him) and
  the ruling "A helper starts from plain words" (`SKILL.md`) are moved to you.

## For `board-duties` and `board-service`

- The rows of the prune and of what an old ended task keeps (`Summarized`, `SmallRecord`,
  `Prune` of `test_task.py`, three checks of `lem-state.sh`) are moved to `board-duties`. A
  dropped task whose journal is folded into its `Summary` is refused by `lem task resume` with its
  ask (`app/tasks/resume.py`).
- The workspaces' list at a task's open (`task-dir` put the main checkout there on `main`) is
  moved to `board-service`: `workspaces.json` is `board/workspaces.py`'s, which `app/` may not
  import.

## For `criteria`

The rows of `criteria read SLUG done` (`ReadForm` of `test_task_rules.py`) are moved to you.

## For `settings`: the table `[paths]`

`lem task plan-file`, `planned` and `build` read `[paths]` of the team's file through a local
stand-in, `lem.app.tasks.plans.paths_of(checkout)`: `plans` (default `docs/plans`), `plan_file`
(default `YYYY-MM-DD-<slug>.md`), `rulings` (read past). Main's `project.file_pattern_of` checked
the pattern (`<slug>` once, no `/` or `\`, `.md`, only `YYYY`, `MM`, `DD`, `<slug>`, none twice);
the stand-in does not, and the table's struct should. Then `paths_of` becomes
`team_of(checkout).paths`.

## For `criteria`: two starts that are no spans

`criteria.read.start by=lem|lead` and `read.skip.asked` (main's `STARTS`) are not spans of
`lem task span` (`SpanName` has no criteria read): they are `criteria read SLUG start` and
`criteria skip SLUG asked`.

## For `tree`: `task build` with no name

`tests/unit/cli/tree.json` gives `task build`'s `target` the count `?`: with no name it lists the
plans that wait, as the owner's ruling "`/lem build` takes a plan file too, and lists the waiting
plans when it gets no name" asks.
