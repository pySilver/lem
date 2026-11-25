# Notes of the step `addons-flow`

What this step needs from files it does not own, and what other steps may count on from it.

## For `land-merge`: the removal of a task's own reviewer item

`land-merge` gave two rows to this step (`check:tests/lem-land-shop.sh:a-task-started-from-a-reviewer-s-item-of-the-eafd80c5b089c4ca`
and `refusal:remove_item:...`): "merged calls the removal once it exists". The removal cannot be
the add-on's: the core never imports an add-on (the design's part 2, import-linter's first
contract), and `app/landing/merged.py` is core. Giving the rows back is a move loop, which
`owners.py` refuses, so they stay with this step unfated; the orchestrator decides.

The rule, from `main`'s `land.remove_item`, for `merged` (and Lem's merge) to hold:

- the task's `backlog_item` is a reviewer's item when it is `.lem/state/backlog/NAME.md`
  (`app/tasks/opening.REVIEWER_ITEMS`);
- after the forge merged, remove `STATE/backlog/NAME.md`; a file gone already is no failure;
- a removal that fails leaves the task open with the refusal "GitHub merged URL, and the file of
  the backlog item the task was started from, ENTRY, was not removed (WHY); the task stays open,
  and `lem land merged SLUG` tries again";
- take `STATE/proposals.lock` (`addons/proposals/days.LOCK`, the lock of the records and the
  items) around the removal, so that a drop from the board comes before it or after it.

## For `board-duties`: the naps in `lem prune`

`lem nap may` removes no nap. The prune of `main` removed each nap folder of `STATE/naps/` older
than `state.keep_days`, by the start in its name (`YYYY-MM-DD-HHMM`, then words), and kept a folder
whose name holds no time, a link, `.asleep` and `.last.log`. `addons/naps/folder.started` reads the
start from a name, if the prune wants the same rule; the add-on cannot be imported from
`store/retention.py`, so the rule is to be copied as a pure function there.

## For the `Terminal` port (`core`) and `adapters/terminal_agterm.py` (`sessions`)

`Terminal.picker(rows: tuple[str, ...], cwd)` sends lines, and agterm makes each line both the id
and the label. `main`'s picker sent agterm's JSON array of `{id, label, subtitle}`, so the state,
track, age and pull request showed as a subtitle under the ask, and were never searched. The
add-on sends `LABEL · SUBTITLE` as one line until the port takes typed rows
(`addons/picker/row.PickRow`: `id`, `label`, `subtitle`) and the adapter writes them as the JSON
array (agterm's reference, "pick": the first byte `[` selects that form).

## For `board-acts`: `lem proposals drop PATH`

- Result: `{"item": PATH, "proposals": [NAME, ...], "day": "YYYY-MM-DD"}`; `PATH` is always the
  path from the main checkout, `.lem/state/backlog/NAME.md`, a whole path given or not.
- Refusal codes: `not-reviewer-item`, `item-gone`, `item-held`, `decided-against`,
  `item-unnamed`, `item-unrecorded`, `proposals-record`.
- Locks: the drop takes `STATE/proposals.lock` only, never `store/workspace.LOCK`
  (`test_the_drop_takes_the_proposals_lock_and_never_the_workspace_lock` runs it while the test
  holds the workspace lock).

## For `docs/rulings/history.md`

"A chord opens a list of the tasks" names `src/lem/picker.py` (its module docstring) as its one
place; the place is now the module docstring of `src/lem/addons/picker/picking.py`, held by
`unit.addons.flow.test_texts.test_a_chord_opens_the_list_of_the_tasks`.

## For `core`: the type stubs of PyYAML

`addons/proposals/heads.py` catches `yaml.YAMLError` from python-frontmatter's read of an item's
head. pyrefly warns that `types-PyYAML` is not installed (a warning, not an error); adding it to the
dev dependencies removes the warning.

## What the board and the night may count on

- The records: `STATE/night/DAY.json` and `STATE/retros/DAY.json` (`addons/proposals/record.py`,
  `DayRecord`), written whole under `STATE/proposals.lock`; the reviewer's items in
  `STATE/backlog/NAME.md`, each with a YAML head of `worth` (`later` or `no`), `where`, `added` and
  `proposals` (a list of names `KIND of DAY #N`; read with `addons/proposals/heads.head_of`).
- `lem proposals list`: `undecided`, `refuted`, `passed` (with `item` and `there`), `dropped`, and
  `newest.night` and `newest.retro` (`date`, `at`, `read`, or null).
- The correction queue: `STATE/corrections.jsonl` (`records.corrections.Correction`, with
  `p_lesson` and `why`), `STATE/corrections-reviews.jsonl` (`CorrectionReview`) and
  `STATE/corrections.log` (`{at, session, error|note}`), all read and written by the owner alone.
- `lem nap may`: `may`, `why`, `folder`, `time`, `newest`; the start is `STATE/naps/.asleep`.
