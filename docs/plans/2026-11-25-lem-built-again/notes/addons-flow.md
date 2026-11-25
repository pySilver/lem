# Notes of the step `addons-flow`

What this step needs from files it does not own, and what other steps may count on from it.

## For `land-merge`: the removal of a task's own reviewer item

`app/landing/merged.py` removes the task's own reviewer item through `store/reviewer_items.py`.
The store holds `STATE/proposals.lock` around the removal and accepts a file gone already. If
removal fails, the task stays open and the refusal names the file and `lem land merged SLUG`.
The merge tests and proof rows are in `land-merge`.

## For `board-duties`: the naps in `lem prune`

`lem nap may` removes no nap. The prune of `main` removed each nap folder of `STATE/naps/` older
than `state.keep_days`, by the start in its name (`YYYY-MM-DD-HHMM`, then words), and kept a folder
whose name holds no time, a link, `.asleep` and `.last.log`. `addons/naps/folder.started` reads the
start from a name, if the prune wants the same rule; the add-on cannot be imported from
`store/retention.py`, so the rule is to be copied as a pure function there.

## For the `Terminal` port (`core`) and `adapters/terminal_agterm.py` (`sessions`)

`Terminal.picker` takes `PickRow` values. The agterm adapter sends a JSON array of
`{id, label, subtitle}` and gives the id the owner picked. The picker and `lem picker --list`
use the same rows.

## For `board-acts`: `lem proposals drop PATH`

- Result: `{"item": PATH, "proposals": [NAME, ...], "day": "YYYY-MM-DD"}`; `PATH` is always the
  path from the main checkout, `.lem/state/backlog/NAME.md`, a whole path given or not.
- Refusal codes: `not-reviewer-item`, `item-gone`, `item-held`, `decided-against`,
  `item-unnamed`, `item-unrecorded`, `proposals-record`.
- Locks: the drop takes `STATE/proposals.lock` only. A task claim takes the workspace lock
  first, then the proposal lock through `store/reviewer_items.py`. The board can hold the
  workspace lock while its child drops an item. The child checks who holds the item again
  under the proposal lock.

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
