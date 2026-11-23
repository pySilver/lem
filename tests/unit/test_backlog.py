"""land.py's rules for the backlog items a review's defects outside the change become, each called in
this process: which names an item may take, whether an item file is a given defect, whether a
review still covers a change that only added items after it or removed the task's own, and which
item a task was started from.

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

    def test_the_deletion_of_the_tasks_own_item_keeps_the_review(self) -> None:
        own = "docs/backlog/existing.md"
        deleted = now(**{own: entry("d" * 40, NONE)})
        self.assertTrue(land.covers_one(FOLDER, REVIEWED, deleted, own))
        self.assertTrue(land.covers_one(FOLDER, REVIEWED, now(**{own: entry("d" * 40, NONE), "docs/backlog/new.md": entry(NONE, "c" * 40)}), own))
        self.assertTrue(land.covered(FOLDER, REVIEWED, deleted, own))
        self.assertIsNone(land.why_uncovered([{**REVIEWED, "round": 1, "must_fix": 0}], FOLDER, deleted, own))

    def test_an_edit_of_the_tasks_own_item_or_the_deletion_of_another_asks_for_another(self) -> None:
        own = "docs/backlog/existing.md"
        self.assertFalse(land.covers_one(FOLDER, REVIEWED, now(**{own: entry("d" * 40, "e" * 40)}), own))
        self.assertFalse(land.covers_one(FOLDER, REVIEWED, now(**{"docs/backlog/other.md": entry("d" * 40, NONE)}), own))
        self.assertFalse(land.covers_one(FOLDER, REVIEWED, now(**{own: entry("d" * 40, NONE)})))

    def test_a_form_a_rebase_carried_covers_too(self) -> None:
        rebased = {"patch": "rebased", "contents": {"app.txt": entry("1" * 40, "2" * 40)}}
        read = {"patch": "older", "contents": {"app.txt": entry("a" * 40, "9" * 40)}, "carried": [rebased]}
        self.assertTrue(land.covers(TASK, read, {"patch": "later", "contents": {**rebased["contents"], "docs/backlog/new.md": entry(NONE, "c" * 40)}}))
        self.assertFalse(land.covers(TASK, {**read, "carried": []}, {**rebased}))


class TaskItem(unittest.TestCase):
    """`land.item_of_ask`: the backlog item a task was started from, found from its ask and the base."""

    ROOTS = ("/lem-unit/repo", "/private/lem-unit/repo")
    # the files of the base commit
    BASE = {"docs/backlog/two-guides.md", "docs/backlog/old/two-guides.md", "docs/backlog/notes.txt", "docs/two-guides.md"}

    def item(self, ask: str) -> str | None:
        return land.item_of_ask(ask, FOLDER, self.ROOTS, self.BASE.__contains__)

    def test_the_path_alone_as_the_board_and_the_night_write_it(self) -> None:
        self.assertEqual(self.item("docs/backlog/two-guides.md\n"), "docs/backlog/two-guides.md")
        self.assertEqual(self.item("  docs/backlog/two-guides.md  "), "docs/backlog/two-guides.md")
        self.assertEqual(self.item("/lem-unit/repo/docs/backlog/two-guides.md\n"), "docs/backlog/two-guides.md")
        self.assertEqual(self.item("/private/lem-unit/repo/docs/backlog/two-guides.md"), "docs/backlog/two-guides.md")

    def test_an_ask_with_a_word_beside_the_path_has_no_item(self) -> None:
        self.assertIsNone(self.item("Do docs/backlog/two-guides.md"))
        self.assertIsNone(self.item("docs/backlog/two-guides.md, and keep the README short"))
        self.assertIsNone(self.item("docs/backlog/two-guides.md\nand the README too"))
        self.assertIsNone(self.item("`docs/backlog/two-guides.md`"))

    def test_a_path_outside_the_folder_or_one_the_base_lacks_is_no_item(self) -> None:
        self.assertIsNone(self.item("docs/two-guides.md"))
        self.assertIsNone(self.item("docs/backlog/old/two-guides.md"))
        self.assertIsNone(self.item("docs/backlog/notes.txt"))
        self.assertIsNone(self.item("docs/backlog/gone.md"))
        self.assertIsNone(self.item("docs/backlog/../backlog/two-guides.md"))
        self.assertIsNone(self.item("/elsewhere/repo/docs/backlog/two-guides.md"))
        self.assertIsNone(self.item("/lem-unit/repo-old/docs/backlog/two-guides.md"))
        self.assertIsNone(self.item(""))


class StateItem(unittest.TestCase):
    """`land.state_item_of_ask` and `land.remove_item`: the reviewer's item of the state folder a task
    was started from, by project.py's one rule (`backlog_item_of`), and the removal of its file when
    the task lands."""

    def setUp(self) -> None:
        # a real folder: on macOS its path and its resolved path differ (/var and /private/var), the two roots a whole path may start with
        self.temp = tempfile.TemporaryDirectory()
        self.main = Path(self.temp.name) / "repo"
        self.state = self.main / ".lem" / "state"
        self.state.mkdir(parents=True)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def item(self, ask: str) -> str | None:
        return land.state_item_of_ask(ask, self.state)

    def test_the_path_relative_to_the_root_or_whole_under_the_main_checkout(self) -> None:
        self.assertEqual(self.item(".lem/state/backlog/tests-flaky-check.md\n"), ".lem/state/backlog/tests-flaky-check.md")
        self.assertEqual(self.item(f"{self.main}/.lem/state/backlog/tests-flaky-check.md"), ".lem/state/backlog/tests-flaky-check.md")
        self.assertEqual(self.item(f"{self.main.resolve()}/.lem/state/backlog/tests-flaky-check.md"), ".lem/state/backlog/tests-flaky-check.md")

    def test_an_item_of_the_backlog_folder_or_another_ask_is_none(self) -> None:
        self.assertIsNone(self.item("docs/backlog/tests-flaky-check.md"))
        self.assertIsNone(self.item(".lem/state/backlog/old/tests-flaky-check.md"))
        self.assertIsNone(self.item(".lem/state/backlog/notes.txt"))
        # a file named `.md` alone is no item: the drop and the board's mark refuse it by the same rule
        self.assertIsNone(self.item(".lem/state/backlog/.md"))
        self.assertIsNone(self.item(".lem/state/tasks/tests-flaky-check/ask.txt"))
        self.assertIsNone(self.item("Fix .lem/state/backlog/tests-flaky-check.md"))
        self.assertIsNone(self.item("/elsewhere/repo/.lem/state/backlog/tests-flaky-check.md"))
        self.assertIsNone(self.item("make the flaky check of tests/lem-serve.sh pass every time"))

    def test_the_removal_of_a_file_there_or_gone_already_and_one_that_fails(self) -> None:
        with tempfile.TemporaryDirectory() as scratch:
            state = Path(scratch)
            (state / "backlog").mkdir()
            item = state / "backlog" / "tests-flaky-check.md"
            item.write_text("---\nworth: later\n---\n# A check of the board fails by chance\n", encoding="utf-8")
            path = ".lem/state/backlog/tests-flaky-check.md"
            self.assertTrue(land.remove_item(state, path, "tests-flaky-check", "https://github.com/acme/shop/pull/7"))
            self.assertFalse(item.exists())
            self.assertFalse(land.remove_item(state, path, "tests-flaky-check", "https://github.com/acme/shop/pull/7"))
            # a folder in the item's place: the unlink fails with an error that is not "no such file"
            item.mkdir()
            with self.assertRaisesRegex(land.LandError, r"the task stays open, and `lem land merged tests-flaky-check` tries again"):
                land.remove_item(state, path, "tests-flaky-check", "https://github.com/acme/shop/pull/7")
            self.assertTrue(item.is_dir())


class Unfiled(unittest.TestCase):
    """`land.to_file`: a defect over the bar waits to be filed until it has an item, whatever the branch holds."""

    def test_a_defect_with_an_item_or_of_a_review_nobody_answered_waits_for_nothing(self) -> None:
        reads = [
            {"round": 1, "answered": True, "outside": [{**D, "bar": "over", "number": "r1.1", "item": "docs/backlog/an-item-from-before-json-parse.md"}, {**E, "bar": "over", "number": "r1.2"}]},
            {"round": 2, "answered": False, "outside": [{**D, "bar": "over", "number": "r2.1"}]},
        ]
        self.assertEqual(land.to_file(reads, lambda path: False), [{"round": 1, "number": "r1.2", **E}])


# The notes of a task on the standard track as `tests/lib.sh` writes them, with nothing outside the change.
NOTES = "## Decisions\n\nnone\n\n## Left open\n\nnone\n\n## Worth a look\n\n- the one line of the file.\n\n## Filed in the backlog\n\nnone\n\n## Not done\n\nnone\n"


def entry_of(defect: dict, call: str, number: str, **more: str) -> dict:
    """One entry of `outside` as `lem land read --record` keeps it."""
    return {**defect, "bar": call, "number": number, **more}


class TheText(unittest.TestCase):
    """What the pull request's text says of the defects outside the change: `land.outside_parts`,
    `land.named_by` and `land.with_outside`."""

    GUARD = {"where": "tests/unit/test_board_model.py", "title": "two test classes come after the main guard", "what": "python3 -m unittest of the file runs them, a reader does not find them."}

    def test_an_under_defect_is_one_line_with_its_place_and_why_and_no_item(self) -> None:
        reads = [{"round": 1, "answered": True, "outside": [entry_of(self.GUARD, "under", "r1.1", why="only a reader of the code meets it")]}]
        self.assertEqual(land.outside_parts(reads, ""), ([], ["- `tests/unit/test_board_model.py`: two test classes come after the main guard; only a reader of the code meets it"]))

    def test_an_open_entry_names_its_item_and_a_filed_one_is_under_filed(self) -> None:
        held = "docs/backlog/the-first-line-skips-a-bold-outcome.md"
        reads = [{"round": 1, "answered": True, "outside": [
            entry_of(D, "over", "r1.1", open=held),
            entry_of(E, "over", "r1.2", item="docs/backlog/an-item-from-before-json-parse.md"),
        ]}]
        filed, seen = land.outside_parts(reads, "")
        self.assertEqual(filed, ["- `docs/backlog/an-item-from-before-json-parse.md`: An item from before"])
        self.assertEqual(seen, [f"- `src/json.py:parse`: An item from before; an open item holds it, `{held}`"])

    def test_a_cheap_entry_is_a_line_unless_a_fix_line_names_its_number(self) -> None:
        # D and E have one place and one title: only the number tells them apart
        reads = [{"round": 1, "answered": True, "outside": [entry_of(D, "cheap", "r1.1", why="a comment says the opposite"), entry_of(E, "cheap", "r1.2", why="a comment says the opposite")]},
                 {"round": 2, "answered": True, "outside": [entry_of(D, "cheap", "r2.1", why="an outdated suppression")]}]
        line = "- `src/json.py:parse`: An item from before; a comment says the opposite"
        # nobody fixed one: each is a line, a second round's among them
        self.assertEqual(land.outside_parts(reads, "")[1], [line, line, "- `src/json.py:parse`: An item from before; an outdated suppression"])
        # a fix line for r1.2 leaves r1.1's line, and r1.20 or r11.2 is no fix of r1.2
        self.assertEqual(land.outside_parts(reads, "- `src/json.py` (abc1234): r1.2, the comment said the opposite")[1], [line, "- `src/json.py:parse`: An item from before; an outdated suppression"])
        self.assertEqual(len(land.outside_parts(reads, "- r1.20 and r11.2 were fixed")[1]), 3)
        self.assertTrue(land.named_by("r1.2", "fixed r1.2."))

    def test_notes_with_nothing_outside_come_back_as_they_are(self) -> None:
        self.assertEqual(land.with_outside(NOTES, [], []), NOTES)

    def test_the_records_lines_join_the_notes_and_a_lone_none_gives_way(self) -> None:
        out = land.with_outside(NOTES, ["- `docs/backlog/x.md`: X"], ["- `a.py`: a; why"])
        self.assertEqual([line for line in out.splitlines() if line.startswith("## ")],
                         ["## Decisions", "## Left open", "## Worth a look", "## Filed in the backlog", "## Seen, not filed", "## Not done"])
        self.assertIn("## Filed in the backlog\n\n- `docs/backlog/x.md`: X\n\n## Seen, not filed\n\n- `a.py`: a; why\n\n## Not done", out)

    def test_the_seen_lines_come_after_the_notes_fixed_lines_and_keep_the_notes_own(self) -> None:
        notes = NOTES.replace("## Not done", "## Fixed on the way\n\n- `b.py` (abc1234): a false docstring\n\n## Seen, not filed\n\n- `c.py`: polish saw it; why\n\n## Not done")
        out = land.with_outside(notes, ["- `docs/backlog/x.md`: X"], ["- `a.py`: a; why"])
        self.assertIn("## Fixed on the way\n\n- `b.py` (abc1234): a false docstring\n\n## Seen, not filed\n\n- `c.py`: polish saw it; why\n- `a.py`: a; why\n\n## Not done", out)
        # an item the notes list already is not written twice
        self.assertEqual(land.with_outside(out, ["- `docs/backlog/x.md`: X"], []), out)


if __name__ == "__main__":
    unittest.main()
