"""board.py's rules for what the board of one task reads beside the page, each called in this
process: what the owner gets, from a task.md's `## Outcome`, and a backlog item's title.

Which items a task's branch adds against its merge base is a fact only git shows: tests/lem-serve.sh
reads it on the board of a task whose branch filed one.

    python3 -B -m unittest discover -s tests/unit
"""

import importlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(
    0, str(Path(__file__).resolve().parents[2] / "skills" / "lem" / "scripts")
)
board = importlib.import_module("board")
task_pages = importlib.import_module("lem_board_task")

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
    def test_the_section_with_its_paragraphs_joined_and_its_own_subheading(
        self,
    ) -> None:
        self.assertEqual(
            board.outcome(TASK),
            (
                "The owner opens the board of all tasks or the board of one task and sees one steady layout in a "
                "modern developer tool's look: no card changes its shape with its text.\n\n"
                "The tabbed board of the backlog item is part of it, built with Lem's own CSS and no library.\n\n"
                "### A heading under it\n\nIt belongs to the outcome."
            ),
        )

    def test_it_ends_at_the_next_section_and_takes_no_other(self) -> None:
        self.assertNotIn("Done when", board.outcome(TASK))
        self.assertNotIn("criteria.md", board.outcome(TASK))

    def test_a_task_md_with_no_outcome_or_an_empty_one_gives_nothing(self) -> None:
        self.assertEqual(
            board.outcome("# a task\n\n## The ask, verbatim\n\nFix the typo.\n"), ""
        )
        self.assertEqual(
            board.outcome("## Outcome\n\n## Done when\n\n- it holds\n"), ""
        )
        self.assertEqual(board.outcome(""), "")

    def test_the_last_section_runs_to_the_end_of_the_file(self) -> None:
        self.assertEqual(
            board.outcome("## Outcome\nOne line\nand its end.\n"),
            "One line and its end.",
        )


class ItemTitle(unittest.TestCase):
    def test_the_title_line_after_the_head_without_backticks(self) -> None:
        fields, title, body = board.parse_item(ITEM)
        self.assertEqual(
            title, "The pictures of the site/ landing page show the new board"
        )
        self.assertEqual(
            fields,
            {"worth": "later", "where": "site/index.html", "added": "2026-11-19"},
        )
        self.assertEqual(
            body.strip(),
            "After this change lands, the pictures of the landing page show the board of tasks 5 and 6.",
        )

    def test_an_item_with_no_title_line_has_none(self) -> None:
        self.assertEqual(board.parse_item("---\nworth: no\n---\nJust words.\n")[1], "")


class MetaAndTold(unittest.TestCase):
    """What the board reads of a repository beside its events: how many commands one run of the
    checks has, and what "What we are building" says of a task with no worktree."""

    def test_one_run_of_the_checks_counts_the_commands_and_the_serial_ones(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            settings = {
                "main": str(Path(tmp) / "shop"),
                "branch": {"base": "main"},
                "checks": {"commands": ["make test"], "serial": ["make e2e"]},
            }
            got = board.meta_of(settings, Path(tmp))
        self.assertEqual(
            got,
            {"repo": "shop", "base": "main", "gates": 2, "serial": 1, "demo": False},
        )

    def test_a_task_with_no_worktree_has_its_outcome_and_no_list_of_filed_items(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            (state / "tasks" / "steady-look").mkdir(parents=True)
            (state / "tasks" / "steady-look" / "task.md").write_text(
                TASK, encoding="utf-8"
            )
            (state / "tasks" / "no-file").mkdir()
            told = task_pages.told_of(
                state, board, "steady-look", None, "main", "docs/backlog"
            )
            empty = task_pages.told_of(
                state, board, "no-file", None, "main", "docs/backlog"
            )
        self.assertTrue(told["outcome"].startswith("The owner opens the board"))
        self.assertIsNone(told["filed"])
        self.assertEqual(empty, {"outcome": "", "filed": None})


class ReviewerItems(unittest.TestCase):
    """`board.backlog` reads the reviewer's items of `.lem/state/backlog/` beside the backlog folder's,
    each held by the task whose ask.txt is its path and that has not ended, or undecided (criteria 6, 7
    and 9 of docs/plans/2026-11-23-scheduled-runs-one-branch.md). The main checkout is a plain folder:
    git's answer for the backlog folder is not what these cases read."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.main = Path(self.temp.name) / "shop"
        self.state = self.main / ".lem" / "state"
        for folder in (self.main / "docs" / "backlog", self.state / "backlog"):
            folder.mkdir(parents=True)
        item = "---\nworth: later\nwhere: {where}\nadded: 2026-11-23\nproposals: {names}\n---\n\n# {title}\n\nFrom the retro of 2026-11-23.\n"
        (self.state / "backlog" / "the-board-s-colors.md").write_text(
            item.format(
                where="skills/lem/assets/board.css",
                names="retro of 2026-11-23 #7",
                title="The board's colors",
            )
        )
        (self.state / "backlog" / "tests-flaky-check.md").write_text(
            item.format(
                where="tests/lem-serve.sh",
                names="night of 2026-11-24 #1",
                title="A check fails by chance",
            )
        )
        (self.state / "backlog" / ".md").write_text("no item\n")
        (self.main / "docs" / "backlog" / "tests-flaky-check.md").write_text(
            "---\nworth: yes\n---\n\n# A developer's item\n"
        )
        self.settings = {
            "main": str(self.main),
            "root": str(self.main),
            "places": {"backlog": {"path": str(self.main / "docs" / "backlog")}},
        }

    def tearDown(self) -> None:
        self.temp.cleanup()

    def task(self, slug: str, ask: str, status: str | None) -> None:
        folder = self.state / "tasks" / slug
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "ask.txt").write_text(ask + "\n")
        if status:
            (folder / "state.md").write_text(
                f"2026-11-24T09:00Z {status}: it goes on\n"
            )

    def items(self) -> dict:
        return {it["key"]: it for it in board.backlog(self.settings)["items"]}

    def test_both_folders_with_one_stem_are_two_items_and_only_the_reviewer_s_carry_a_mark(
        self,
    ) -> None:
        items = self.items()
        self.assertEqual(
            sorted(items),
            ["-tests-flaky-check", "-the-board-s-colors", "tests-flaky-check"],
        )
        self.assertEqual(
            items["-tests-flaky-check"]["path"],
            ".lem/state/backlog/tests-flaky-check.md",
        )
        self.assertEqual(
            items["tests-flaky-check"]["path"], "docs/backlog/tests-flaky-check.md"
        )
        self.assertEqual(
            (
                items["-the-board-s-colors"]["reviewer"],
                items["-the-board-s-colors"]["held"],
                items["-the-board-s-colors"]["title"],
            ),
            (True, None, "The board's colors"),
        )
        self.assertNotIn("held", items["tests-flaky-check"])
        self.assertEqual(
            board.backlog(self.settings)["reviewer_folder"], ".lem/state/backlog"
        )

    def test_a_task_that_has_not_ended_holds_it_by_its_path_and_one_dropped_gives_it_back(
        self,
    ) -> None:
        self.task(
            "tests-flaky-check", ".lem/state/backlog/tests-flaky-check.md", "building"
        )
        self.assertEqual(
            self.items()["-tests-flaky-check"]["held"],
            {"task": "tests-flaky-check", "status": "building"},
        )
        self.task(
            "tests-flaky-check", ".lem/state/backlog/tests-flaky-check.md", "dropped"
        )
        self.assertIsNone(self.items()["-tests-flaky-check"]["held"])
        # a whole path under the main checkout is the same item, and a task of the backlog folder's item holds no reviewer's item
        self.task(
            "tests-flaky-check-2",
            f"{self.main}/.lem/state/backlog/tests-flaky-check.md",
            None,
        )
        self.task(
            "tests-flaky-check-docs", "docs/backlog/tests-flaky-check.md", "building"
        )
        self.assertEqual(
            self.items()["-tests-flaky-check"]["held"],
            {"task": "tests-flaky-check-2", "status": None},
        )

    def test_the_holder_rule_reads_an_item_of_the_backlog_folder_by_its_path_too(
        self,
    ) -> None:
        self.task(
            "refund-total-zero",
            f"{self.main}/docs/backlog/tests-flaky-check.md",
            "planned",
        )
        self.assertEqual(
            board.lem_project.item_holder(
                self.state, "docs/backlog/tests-flaky-check.md"
            ),
            {"task": "refund-total-zero", "status": "planned"},
        )
        self.assertIsNone(
            board.lem_project.item_holder(
                self.state, ".lem/state/backlog/tests-flaky-check.md"
            )
        )

    def test_a_landed_task_s_item_is_gone_with_its_file(self) -> None:
        # the landing removes the file (land.py `forge_done`): the next read has no such item
        self.task(
            "tests-flaky-check", ".lem/state/backlog/tests-flaky-check.md", "landed"
        )
        (self.state / "backlog" / "tests-flaky-check.md").unlink()
        self.assertNotIn("-tests-flaky-check", self.items())


if __name__ == "__main__":
    unittest.main()
