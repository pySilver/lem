"""land.py's rules for the backlog items a review's defects outside the change become, each called in
this process: whether a review still covers a change that only added items after it.

What only git can show (the commits `lem land file` makes, an item removed by a commit, a review
that a later commit asks to run again) stays in tests/lem-land-backlog.sh.

    python3 -B -m unittest discover -s tests/unit
"""

import importlib
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "lem" / "scripts"))
land = importlib.import_module("land")

# A repository that is not on disk, with the backlog folder in its one place. `covers_one` reads
# only the folder of the task it is given.
TASK = SimpleNamespace(settings={"root": "/lem-unit/repo", "places": {"backlog": {"path": "/lem-unit/repo/docs/backlog"}}})
NONE = "0" * 40


def entry(base: str, tip: str) -> dict:
    """A file of a change as `land.change` lists it: its blob on the base and on the tip."""
    return {"base": base, "tip": tip, "modes": ["100644", "100644"]}


# The change a review saw: one file of the app, changed.
REVIEWED = {"patch": "reviewed", "contents": {"app.txt": entry("a" * 40, "b" * 40)}}


def now(**more: dict) -> dict:
    """The change as it is after the review: the reviewed change, and the files of `more` beside it."""
    return {"patch": "later", "contents": {**REVIEWED["contents"], **more}}


class Covers(unittest.TestCase):
    """`land.covers_one` and `land.covers`: whether a review still covers the change after it."""

    def test_the_same_change(self) -> None:
        self.assertTrue(land.covers_one(TASK, REVIEWED, {**REVIEWED}))

    def test_a_new_item_in_the_backlog_folder_keeps_the_review(self) -> None:
        self.assertTrue(land.covers_one(TASK, REVIEWED, now(**{"docs/backlog/new.md": entry(NONE, "c" * 40)})))

    def test_an_item_that_was_on_the_base_edited_or_deleted_asks_for_another(self) -> None:
        self.assertFalse(land.covers_one(TASK, REVIEWED, now(**{"docs/backlog/existing.md": entry("d" * 40, "e" * 40)})))
        self.assertFalse(land.covers_one(TASK, REVIEWED, now(**{"docs/backlog/existing.md": entry("d" * 40, NONE)})))

    def test_a_new_file_outside_the_folder_asks_for_another(self) -> None:
        self.assertFalse(land.covers_one(TASK, REVIEWED, now(**{"docs/new.md": entry(NONE, "c" * 40)})))
        self.assertFalse(land.covers_one(TASK, REVIEWED, now(**{"docs/backlog-old/new.md": entry(NONE, "c" * 40)})))

    def test_a_reviewed_file_that_changed_again_asks_for_another(self) -> None:
        changed = now(**{"docs/backlog/new.md": entry(NONE, "c" * 40)})
        changed["contents"]["app.txt"] = entry("a" * 40, "f" * 40)
        self.assertFalse(land.covers_one(TASK, REVIEWED, changed))

    def test_a_record_with_no_contents_covers_only_the_same_change(self) -> None:
        bare = {"patch": "reviewed"}
        self.assertTrue(land.covers_one(TASK, bare, {**REVIEWED}))
        self.assertFalse(land.covers_one(TASK, bare, now(**{"docs/backlog/new.md": entry(NONE, "c" * 40)})))

    def test_a_form_a_rebase_carried_covers_too(self) -> None:
        rebased = {"patch": "rebased", "contents": {"app.txt": entry("1" * 40, "2" * 40)}}
        read = {"patch": "older", "contents": {"app.txt": entry("a" * 40, "9" * 40)}, "carried": [rebased]}
        self.assertTrue(land.covers(TASK, read, {"patch": "later", "contents": {**rebased["contents"], "docs/backlog/new.md": entry(NONE, "c" * 40)}}))
        self.assertFalse(land.covers(TASK, {**read, "carried": []}, {**rebased}))


if __name__ == "__main__":
    unittest.main()
