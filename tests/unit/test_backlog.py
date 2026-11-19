"""land.py's rules for the backlog items a review's defects outside the change become, each called in
this process: which names an item may take, whether an item file is a given defect, and whether a
review still covers a change that only added items after it.

What only git can show (the commits `lem land file` makes, an item removed by a commit, a review
that a later commit asks to run again) stays in tests/lem-land-backlog.sh.

    python3 -B -m unittest discover -s tests/unit
"""

import importlib
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "lem" / "scripts"))
land = importlib.import_module("land")

# Two defects of one place and one title, with two different runs.
D = {"where": "src/json.py:parse", "title": "An item from before", "what": "parse of a document with no root returns None, on the base commit too."}
E = {"where": "src/json.py:parse", "title": "An item from before", "what": "parse of a document of one number returns a string, on the base commit too."}

# A repository that is not on disk, with the backlog folder in its one place. `covers_one` reads
# only the folder of the task it is given.
TASK = SimpleNamespace(settings={"root": "/lem-unit/repo", "places": {"backlog": {"path": "/lem-unit/repo/docs/backlog"}}})
# the folder as `covers` gives it to `covers_one`: from the task's settings, by the script's own function
FOLDER = land.backlog_of(TASK)
NONE = "0" * 40


def item(defect: dict, *, worth: str = "later", reason: str = "") -> str:
    """An item of a defect in the backlog's item format, as `lem land file` writes it, with the owner's
    reason as a paragraph of its own when there is one."""
    said = f"{reason}\n\n" if reason else ""
    return (f"---\nworth: {worth}\nwhere: {defect['where']}\nadded: 2026-11-19\n---\n# {defect['title']}\n\n{defect['what']}\n\n{said}"
            "Seen outside the change by review round 1 of task same-defect (2026-11-19); the base commit has it.\n")


def entry(base: str, tip: str) -> dict:
    """A file of a change as `land.change` lists it: its blob on the base and on the tip."""
    return {"base": base, "tip": tip, "modes": ["100644", "100644"]}


# The change a review saw: one file of the app, changed.
REVIEWED = {"patch": "reviewed", "contents": {"app.txt": entry("a" * 40, "b" * 40)}}


def now(**more: dict) -> dict:
    """The change as it is after the review: the reviewed change, and the files of `more` beside it."""
    return {"patch": "later", "contents": {**REVIEWED["contents"], **more}}


class Names(unittest.TestCase):
    """`land.names_for`: the file names an item of a defect may take, in turn."""

    def first(self, defect: dict, count: int) -> list[str]:
        names = land.names_for(defect)
        return [next(names) for _ in range(count)]

    def test_the_slug_then_the_suffix_of_its_place_then_a_number(self) -> None:
        self.assertEqual(self.first(D, 4), ["an-item-from-before.md", "an-item-from-before-json-parse.md", "an-item-from-before-json-parse-2.md", "an-item-from-before-json-parse-3.md"])

    def test_a_place_with_no_symbol_gives_the_files_stem(self) -> None:
        self.assertEqual(self.first({**D, "where": "src/app.txt"}, 2), ["an-item-from-before.md", "an-item-from-before-app.md"])

    def test_a_long_title_is_cut_at_a_word(self) -> None:
        slug = land.slug_of("word " * 30)
        self.assertLessEqual(len(slug), land.SLUG_AT)
        self.assertFalse(slug.endswith("-"))
        self.assertEqual(set(slug.split("-")), {"word"})


class Holds(unittest.TestCase):
    """`land.holds` and `land.item_of`: whether an item file is a given defect."""

    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.folder = Path(folder.name)

    def file(self, text: str, name: str = "an-item.md") -> Path:
        path = self.folder / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_the_item_of_a_defect_holds_it_and_not_another_run_of_its_place_and_title(self) -> None:
        written = self.file(item(D))
        self.assertTrue(land.holds(written, D))
        self.assertFalse(land.holds(written, E))

    def test_the_owners_no_and_his_reason_leave_it_the_same_defect(self) -> None:
        said_no = self.file(item(D, worth="no", reason="The owner: a document always has a root here."))
        self.assertTrue(land.holds(said_no, D))
        self.assertEqual(land.item_of(said_no)[0]["worth"], "no")

    def test_an_item_with_no_place_is_no_defect(self) -> None:
        plain = self.file("# An item from before\n")
        self.assertEqual(land.item_of(plain), ({}, ["# An item from before"]))
        self.assertFalse(land.holds(plain, D))

    def test_another_title_or_another_place_is_another_defect(self) -> None:
        written = self.file(item(D))
        self.assertFalse(land.holds(written, {**D, "title": "Another item"}))
        self.assertFalse(land.holds(written, {**D, "where": "src/csv.py:read"}))

    def test_a_file_that_is_no_item(self) -> None:
        self.assertIsNone(land.item_of(self.file("no title here\n")))
        self.assertIsNone(land.item_of(self.folder / "missing.md"))
        self.assertFalse(land.holds(self.folder / "missing.md", D))


class Covers(unittest.TestCase):
    """`land.covers_one` and `land.covers`: whether a review still covers the change after it."""

    def test_the_same_change(self) -> None:
        self.assertTrue(land.covers_one(FOLDER,REVIEWED, {**REVIEWED}))

    def test_a_new_item_in_the_backlog_folder_keeps_the_review(self) -> None:
        self.assertTrue(land.covers_one(FOLDER,REVIEWED, now(**{"docs/backlog/new.md": entry(NONE, "c" * 40)})))

    def test_an_item_that_was_on_the_base_edited_or_deleted_asks_for_another(self) -> None:
        self.assertFalse(land.covers_one(FOLDER,REVIEWED, now(**{"docs/backlog/existing.md": entry("d" * 40, "e" * 40)})))
        self.assertFalse(land.covers_one(FOLDER,REVIEWED, now(**{"docs/backlog/existing.md": entry("d" * 40, NONE)})))

    def test_a_new_file_outside_the_folder_asks_for_another(self) -> None:
        self.assertFalse(land.covers_one(FOLDER,REVIEWED, now(**{"docs/new.md": entry(NONE, "c" * 40)})))
        self.assertFalse(land.covers_one(FOLDER,REVIEWED, now(**{"docs/backlog-old/new.md": entry(NONE, "c" * 40)})))

    def test_a_reviewed_file_that_changed_again_asks_for_another(self) -> None:
        changed = now(**{"docs/backlog/new.md": entry(NONE, "c" * 40)})
        changed["contents"]["app.txt"] = entry("a" * 40, "f" * 40)
        self.assertFalse(land.covers_one(FOLDER,REVIEWED, changed))

    def test_a_record_with_no_contents_covers_only_the_same_change(self) -> None:
        bare = {"patch": "reviewed"}
        self.assertTrue(land.covers_one(FOLDER,bare, {**REVIEWED}))
        self.assertFalse(land.covers_one(FOLDER,bare, now(**{"docs/backlog/new.md": entry(NONE, "c" * 40)})))

    def test_a_form_a_rebase_carried_covers_too(self) -> None:
        rebased = {"patch": "rebased", "contents": {"app.txt": entry("1" * 40, "2" * 40)}}
        read = {"patch": "older", "contents": {"app.txt": entry("a" * 40, "9" * 40)}, "carried": [rebased]}
        self.assertTrue(land.covers(TASK, read, {"patch": "later", "contents": {**rebased["contents"], "docs/backlog/new.md": entry(NONE, "c" * 40)}}))
        self.assertFalse(land.covers(TASK, {**read, "carried": []}, {**rebased}))


class Unfiled(unittest.TestCase):
    """`land.to_file`: a defect waits to be filed until it has an item, whatever the branch holds."""

    def test_a_defect_with_an_item_or_of_a_review_nobody_answered_waits_for_nothing(self) -> None:
        reads = [
            {"round": 1, "answered": True, "outside": [{**D, "item": "docs/backlog/an-item-from-before-json-parse.md"}, E]},
            {"round": 2, "answered": False, "outside": [D]},
        ]
        self.assertEqual(land.to_file(reads), [{"round": 1, **E}])


if __name__ == "__main__":
    unittest.main()
