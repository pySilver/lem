# Notes of the step `addons-flow`

What this step needs from files it does not own, and what other steps may count on from it.

## For `land-merge`: the removal of a task's own reviewer item

`app/landing/merged.py` removes the task's own reviewer item through `store/reviewer_items.py`.
The store holds `STATE/proposals.lock` around the removal and accepts a file gone already. If
removal fails, the task stays open and the refusal names the file and `lem land merged SLUG`.

## Files touched for the join

- `src/lem/model/task/resumes.py` (`task`) carries the reviewer item into the request that follows a release stop.
- `src/lem/hooks/corrections.py` (`sessions`) checks for the team file in the worktree where the owner typed, then uses the main checkout's queue.
- `src/lem/hooks/where.py` (`sessions`) lets the correction hook find that worktree with `checkout_of(..., main=False)`.
- `docs/free-hour.md` (`addons-flow` in the ledger) names the task journals and gives the full test command, `.venv/bin/python -I -B tests --level full`.
- `src/lem/app/tasks/opening.py` (`task`) claims reviewer items by their path from the main checkout and refuses an explicit path outside it or a tracked link.
- `src/lem/store/workspace.py` (`core`) checks the reviewer item and creates its task record under the proposal lock, inside the workspace lock.
- `src/lem/cli/place.py` (`tree`) lets the picker use the caller's agterm session folder as its default after `--repo` and before the working directory.
- `src/lem/app/landing/merge_item.py` (`land-merge`) removes the task's reviewer item after the forge merge and gives the retry command if removal fails.
- `tests/unit/task/test_open.py` (`task`) checks that a tracked backlog link cannot claim its target.
- `tests/unit/task/test_park.py` (`task`) checks that a release stop's successor keeps the item claimed and prevents its drop.
- `tests/journeys/landing/test_merge.py` (`land-merge`) checks that `lem land merged` removes the item after a Lem or GitHub merge and keeps it after a close without a merge.
- `tests/ledger/fates/land-merge.tsv` (`land-merge`) adds proof rows for removal after a merge, an item already gone, and a failed removal that `lem land merged` can retry.

## After `land-propose` and `addons-outside` join

Round 2's finding 5 waits for both steps to join. The retro loses earlier green proposals when
`app/landing/propose_made.py` replaces the latest proposal and journals only proposals with reasons.
The fix belongs there. Write a journal entry for each proposal so the retro can read each one.

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
`unit.addons.flow.test_picker.test_the_generated_picker_chord_opens_the_list_of_the_tasks`.

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
