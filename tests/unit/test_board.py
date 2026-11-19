"""board.py's rules for what the board of one task reads beside the page, each called in this
process: what the owner gets, from a task.md's `## Outcome`, and a backlog item's title.

Which items a task's branch adds against its merge base is a fact only git shows: tests/test-board.sh
checks it over a branch that adds an item and one that adds none.

    python3 -B -m unittest discover -s tests/unit
"""

import importlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "lem" / "scripts"))
board = importlib.import_module("board")

# A task.md as `/lem new` writes it (stages/new.md): the ask, the type, the outcome over two
# paragraphs with hard-wrapped lines, then the next sections.
TASK = """# status-boards-steady-look

## The ask, verbatim

I would like to improve our status screens (plan, task).

## Type

feat, because the ask wants a new look for the status screens.

## Outcome

The owner opens the board of all tasks or the board of one task and sees one steady layout in a
modern developer tool's look: no card changes its shape with its text.

The tabbed board of the backlog item is part of it,
built with Lem's own CSS and no library.

### A heading under it

It belongs to the outcome.

## Done when

- The acceptance criteria in `criteria.md` hold.
"""

ITEM = """---
worth: later
where: site/index.html
added: 2026-11-19
---
# The pictures of the `site/` landing page show the new board

After this change lands, the pictures of the landing page show the board of tasks 5 and 6.
"""


class Outcome(unittest.TestCase):
    def test_the_section_with_its_paragraphs_joined_and_its_own_subheading(self):
        self.assertEqual(board.outcome(TASK), (
            "The owner opens the board of all tasks or the board of one task and sees one steady layout in a "
            "modern developer tool's look: no card changes its shape with its text.\n\n"
            "The tabbed board of the backlog item is part of it, built with Lem's own CSS and no library.\n\n"
            "### A heading under it\n\nIt belongs to the outcome."))

    def test_it_ends_at_the_next_section_and_takes_no_other(self):
        self.assertNotIn("Done when", board.outcome(TASK))
        self.assertNotIn("criteria.md", board.outcome(TASK))

    def test_a_task_md_with_no_outcome_or_an_empty_one_gives_nothing(self):
        self.assertEqual(board.outcome("# a task\n\n## The ask, verbatim\n\nFix the typo.\n"), "")
        self.assertEqual(board.outcome("## Outcome\n\n## Done when\n\n- it holds\n"), "")
        self.assertEqual(board.outcome(""), "")

    def test_the_last_section_runs_to_the_end_of_the_file(self):
        self.assertEqual(board.outcome("## Outcome\nOne line\nand its end.\n"), "One line and its end.")


class ItemTitle(unittest.TestCase):
    def test_the_title_line_after_the_head_without_backticks(self):
        fields, title, body = board.parse_item(ITEM)
        self.assertEqual(title, "The pictures of the site/ landing page show the new board")
        self.assertEqual(fields, {"worth": "later", "where": "site/index.html", "added": "2026-11-19"})
        self.assertEqual(body.strip(), "After this change lands, the pictures of the landing page show the board of tasks 5 and 6.")

    def test_an_item_with_no_title_line_has_none(self):
        self.assertEqual(board.parse_item("---\nworth: no\n---\nJust words.\n")[1], "")


class Overview(unittest.TestCase):
    """overview() over a state folder whose tasks have no worktree: each has its outcome, and no list
    of filed items, since nothing tells it."""

    def test_each_task_has_its_outcome_and_none_has_a_list_without_a_worktree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / ".lem" / "state"
            (state / "tasks" / "steady-look").mkdir(parents=True)
            (state / "tasks" / "steady-look" / "task.md").write_text(TASK, encoding="utf-8")
            (state / "tasks" / "no-file").mkdir()
            (state / "tasks" / "Not A Slug").mkdir()
            settings = {"main": str(root), "root": str(root), "branch": {"base": "main"},
                        "places": {"worktrees": {"path": str(root / ".lem" / "worktrees")}, "backlog": {"path": str(root / "docs" / "backlog")}}}
            got = board.overview(settings, state)
        self.assertEqual(sorted(got["tasks"]), ["no-file", "steady-look"])
        self.assertTrue(got["tasks"]["steady-look"]["outcome"].startswith("The owner opens the board"))
        self.assertEqual(got["tasks"]["no-file"], {"outcome": "", "filed": None})
        self.assertIsNone(got["tasks"]["steady-look"]["filed"])
        self.assertRegex(got["written"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")


if __name__ == "__main__":
    unittest.main()
