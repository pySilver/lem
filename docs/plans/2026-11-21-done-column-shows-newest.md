# The board's Done column shows the newest ended tasks

careful: no, because the change only draws fewer cards in one column and adds one page that lists the rest; it writes no record, no state and no event, and it reaches no pull request, merge or settings (checked against each of the thirteen topics of `.lem/project.toml`).

## Acceptance criteria

Size: full, because the board and the picker each change, and the board gets a page of its own.

1. Done shows the 20 tasks that ended last, and no others:
   1. The workspace has 25 ended tasks: landed, dropped or answered.
   2. The owner opens the board's Tasks view.
   3. Done shows 20 cards, the 20 tasks that ended last, the newest on top.
   4. The 5 tasks that ended first have no card in Done.
2. Done's head counts every ended task: with 25 ended tasks, Done's head says 25 while it shows 20 cards, and so does its tab on the phone.
3. Under the 20 cards, one row counts the rest and leads to them:
   1. With 25 ended tasks, the row under the 20 cards says "5 older".
   2. A click on that row opens a list of those 5 tasks.
   3. With 20 ended tasks or fewer, Done shows each of them and no such row.
   4. The list opens as a page of the board, and the board's own Tasks link goes back to the columns.
4. The list of older tasks shows each task that has no card in Done, newest first, with its title, how it ended, when, and a link to its board, and to its pull request when it has one: with 25 ended tasks it lists the 5 that ended first, the one that ended last of them on top, and a click on one opens that task's board.
5. The picker lists the 20 tasks that ended last, whenever they ended:
   1. A repository whose 3 tasks all ended a month ago shows those 3 in the picker.
   2. A repository with 25 ended tasks shows the 20 that ended last.
   3. The tasks that wait for the owner or build stay above the ended ones, as today.

## Tasks

1. **Done keeps the newest 20, with a row to the rest, and the list of the rest is a page of the
   board.** Serves criteria 1 to 4. One constant of the board's model holds the 20, beside `LANES`
   in `skills/lem/scripts/lem_board_model.py`, with its source: "an unmeasured estimate of a column
   that fits one screen of the large board" (the backlog item, 2026-11-21). The model's `done` lane
   keeps every ended task, so the column's head and the phone's tab (`kanban` in
   `skills/lem/scripts/lem_board_pages.py`) still count all of them; only the cards drawn stop at
   the constant, and a foot row under them counts the rest and links the page. The page is one more
   view of a workspace (`PAGES` in `skills/lem/scripts/serve.py`), in the board's look, drawn from
   the same model: no event, file or record is read that the board does not read today. It is no
   key of the nav (T, W, B, A); the foot row is its way in. Unit cases of the pages beside those that
   import `lem_board_pages` today (`tests/unit/test_board_task.py`, or a file of their own),
   `tests/unit/test_board_model.py` when the model gets a function, and `tests/unit/test_serve.py`
   for the route. Files: the three scripts, the tests, and
   `skills/lem/assets/board.css` for the foot row and the list, when the existing classes do not
   draw them. Remove the backlog item `docs/backlog/the-board-s-done-column-has-no-limit.md` in the
   same commit as the board's change.
2. **The picker keeps the newest ended tasks by the same constant, with no time limit.** Serves
   criterion 5. `ENDED_DAYS` in `skills/lem/scripts/picker.py` goes; the picker takes the ended
   tasks newest first and stops at the board's constant, which it reads from `lem_board_model` (it
   imports that module already). Its module docstring says the new rule. A unit case of `rows` in
   `tests/unit/test_picker.py`, which has none for the ended tasks today.

## Decisions

- **20 is a constant, not a key of the settings.** The backlog item says so, after "Opinionated and
  small" in `docs/rulings/rulings.md`. The owner's ruling of 2026-11-21 says "keep `last N` done
  items"; the setting it names, which one machine may set for itself, is how long an ended task's
  files stay (`state.keep_days`, built already).
- **The board and the picker read one constant**, so the two lists of ended tasks cannot drift.
- **The list of older tasks reads the model the board reads today**, which `derive` makes from the
  event log. When `old-task-events-summarized` puts a summary event in place of an old task's
  events, the model still lists the task, and this page with it; that task's plan keeps it so.
- **The task did not wait for `old-task-events-summarized`** (decision 1 of the record): the events
  hold each ended task today, so the limit and the list work before that task lands.

## Not verified

- The page's size and time with a thousand ended tasks: the backlog item measured the cost without
  the limit; this change bounds the cards at 20, and the tests count the cards, not the bytes.
