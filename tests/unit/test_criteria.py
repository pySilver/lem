"""criteria.py's reading of a plan's criteria, each called in this process: a criterion's case and its
chart, the plan's `## How it works`, and which of them the digests mark."""

import importlib
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "lem" / "scripts"))
criteria = importlib.import_module("criteria")

PLAN = """## Acceptance criteria

Size: full, because a refund has two outcomes.

1. A refund lowers the invoice's total, and never below 0:
   1. Invoice 1042 is 100 EUR.
   2. A refund of 130 EUR comes in.
   3. The invoice shows 0, and a credit
      note holds the other 30 EUR.
    ```mermaid
    flowchart TD
      A["A refund comes in"] --> B{"Larger than the total?"}
        B -->|"yes"| C["The total shows 0"]
    ```
   - test: `sh tests/refund.sh` in `tests/refund.sh`
2. The invoice keeps its number.

## How it works

The refund, from its arrival to the invoice:

```mermaid
flowchart LR
  A["A refund"] --> B["The invoice"]
```

## Tasks

1. The refund.
"""


class CaseAndChart(unittest.TestCase):
    """A criterion's steps stay lines of their own and its chart is its own, at any indent."""

    def test_the_steps_and_a_chart_at_four_spaces(self) -> None:
        first, second = criteria.parse(PLAN, "plan.md")["criteria"]
        self.assertEqual(first["text"], "A refund lowers the invoice's total, and never below 0:")
        self.assertEqual(first["case"], ["1. Invoice 1042 is 100 EUR.", "2. A refund of 130 EUR comes in.", "3. The invoice shows 0, and a credit note holds the other 30 EUR."])
        self.assertEqual(first["chart"], 'flowchart TD\n  A["A refund comes in"] --> B{"Larger than the total?"}\n    B -->|"yes"| C["The total shows 0"]')
        self.assertNotIn("mermaid", first["text"])
        self.assertEqual([test["command"] for test in first["tests"]], ["sh tests/refund.sh"])
        self.assertEqual((second["case"], second["chart"]), ([], None))

    def test_how_it_works_is_read_and_is_no_criterion(self) -> None:
        read = criteria.parse(PLAN, "plan.md")
        self.assertEqual(len(read["criteria"]), 2)
        self.assertTrue(read["how"].startswith("The refund, from its arrival to the invoice:\n\n```mermaid\nflowchart LR"))

    def test_a_second_chart_under_one_criterion_is_refused(self) -> None:
        twice = PLAN.replace("   - test:", "   ```mermaid\n   flowchart TD\n     A[\"x\"]\n   ```\n   - test:")
        with self.assertRaisesRegex(criteria.CriteriaError, "plan.md:15: criterion 1 has a chart already"):
            criteria.parse(twice, "plan.md")


class Digests(unittest.TestCase):
    """The case is a part of what the owner approved, and the chart is not: a change of a step changes
    the criterion and both digests, a change of the chart changes neither."""

    @staticmethod
    def marks(plan: str) -> tuple[str, str, list[str]]:
        read = criteria.parse(plan, "plan.md")
        wholes = [criteria.whole(criterion) for criterion in read["criteria"]]
        return read["digest"], criteria.text_digest(read["size"], wholes), wholes

    def test_a_step_changes_the_criterion(self) -> None:
        digest, text, wholes = self.marks(PLAN)
        moved, moved_text, moved_wholes = self.marks(PLAN.replace("130 EUR", "150 EUR"))
        self.assertNotEqual(digest, moved)
        self.assertNotEqual(text, moved_text)
        self.assertNotEqual(wholes[0].split(), moved_wholes[0].split())

    def test_a_chart_changes_nothing_that_is_marked(self) -> None:
        drawn = PLAN.replace('C["The total shows 0"]', 'C["The total reads 0"]').replace('B["The invoice"]', 'B["An invoice"]')
        self.assertEqual(self.marks(PLAN), self.marks(drawn))

    def test_steps_read_as_the_text_they_were(self) -> None:
        """A case written before the steps were lines of their own read as one text: the same digest."""
        _, text, _ = self.marks(PLAN)
        read = criteria.parse(PLAN, "plan.md")
        joined = [" ".join(criteria.whole(criterion).split()) for criterion in read["criteria"]]
        self.assertEqual(text, criteria.text_digest("full", joined))


if __name__ == "__main__":
    unittest.main()


class ResumedPlan(unittest.TestCase):
    """A task resumed from a dropped one finds the old task's plan on its branch, and its own once its lead writes one."""

    def test_the_plan_of_the_task_it_came_from(self) -> None:
        import tempfile
        lem_plans = importlib.import_module("lem_plans")
        with tempfile.TemporaryDirectory() as folder:
            tasks, plans = Path(folder) / "tasks", Path(folder) / "plans"
            for slug, came in (("gift-note", None), ("gift-note-2", "gift-note"), ("gift-note-3", "gift-note-2")):
                (tasks / slug).mkdir(parents=True)
                if came:
                    (tasks / slug / "resumed-from.txt").write_text(came + "\n")
            plans.mkdir()
            (plans / "2026-11-20-gift-note.md").write_text("# plan\n")
            self.assertEqual(lem_plans.resumed_from(tasks, "gift-note-3"), ["gift-note-2", "gift-note"])
            self.assertEqual(lem_plans.found(plans, lem_plans.PLAN_FILE, "gift-note-3"), None)
            self.assertEqual(lem_plans.found(plans, lem_plans.PLAN_FILE, "gift-note-3", lem_plans.resumed_from(tasks, "gift-note-3")).name, "2026-11-20-gift-note.md")
            (plans / "2026-11-21-gift-note-3.md").write_text("# its own\n")
            self.assertEqual(lem_plans.found(plans, lem_plans.PLAN_FILE, "gift-note-3", ["gift-note-2", "gift-note"]).name, "2026-11-21-gift-note-3.md")
            self.assertEqual(lem_plans.resumed_from(tasks, "gift-note"), [])


class FastTrackNotHis(unittest.TestCase):
    """The fast track's one criterion is approved in the owner's name only when the request is his own
    sentence; a night's task, or a request someone else wrote, is approved without him (`--alone`), in any mode."""

    SMALL = "## Acceptance criteria\n\nSize: small, because the request is one sentence.\n\n1. The footer says 2026.\n"

    def task(self, folder: Path, night: str | None = None, brief: str = "", mode: str = "with-owner"):
        task = criteria.Task.__new__(criteria.Task)
        task.slug, task.night, task.mode = "footer-year", night, mode
        task.directory = folder / "tasks" / "footer-year"
        task.directory.mkdir(parents=True)
        task.approved_file, task.small_file = task.directory / "criteria.json", task.directory / "criteria.md"
        task.small_file.write_text(self.SMALL)
        if brief:
            (task.directory / "brief.md").write_text(brief)
        task.read_mode = lambda: task.mode
        task.log = lambda *args, **kwargs: None
        return task

    def test_a_nights_task_is_approved_without_him_and_never_in_his_name(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            task = self.task(Path(folder), night="2026-11-21", mode="alone")
            with self.assertRaises(criteria.CriteriaError) as refused:
                criteria.cmd_approve(task, str(task.small_file), "lem")
            self.assertIn("--alone", str(refused.exception))
            self.assertEqual(criteria.cmd_approve(task, str(task.small_file), "alone", plan=True)["by"], "alone")

    def test_a_request_someone_else_wrote_is_approved_without_him_while_he_is_there(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            task = self.task(Path(folder), brief="task: footer-year\nrequest by: someone else\n")
            self.assertEqual(criteria.cmd_approve(task, str(task.small_file), "alone", plan=True)["by"], "alone")

    def test_his_own_request_is_approved_in_his_name_even_while_he_is_away(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            task = self.task(Path(folder), mode="alone")
            with self.assertRaises(criteria.CriteriaError) as refused:
                criteria.cmd_approve(task, str(task.small_file), "alone", plan=True)
            self.assertIn("--alone is for a night's task or a request someone else wrote", str(refused.exception))
            self.assertEqual(criteria.cmd_approve(task, str(task.small_file), "lem")["by"], "lem")


class ApprovalOfWhatWasShown(unittest.TestCase):
    """`cmd_approve` with the digest of the bytes the owner's page showed (`--shown`): it approves those
    bytes or nothing, so a file that changed after the page's check is never approved in his name."""

    FULL = "## Acceptance criteria\n\nSize: full, because the export gets a column.\n\n1. The export holds the gift note.\n"

    def task(self, folder: Path):
        task = FastTrackNotHis.task(FastTrackNotHis(), folder)
        task.small_file.write_text(self.FULL)
        return task

    def test_the_bytes_the_page_showed_are_approved(self) -> None:
        import hashlib
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            task = self.task(Path(folder))
            shown = hashlib.sha256(task.small_file.read_bytes()).hexdigest()[:16]
            self.assertEqual(criteria.cmd_approve(task, str(task.small_file), "owner", shown=shown)["text"], self.FULL)

    def test_a_file_that_changed_after_the_page_is_not_approved(self) -> None:
        import hashlib
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            task = self.task(Path(folder))
            shown = hashlib.sha256(task.small_file.read_bytes()).hexdigest()[:16]
            task.small_file.write_text(self.FULL.replace("gift note", "gift note and its date"))
            with self.assertRaises(criteria.CriteriaError) as refused:
                criteria.cmd_approve(task, str(task.small_file), "owner", shown=shown)
            self.assertIn("changed since the page showed them", str(refused.exception))
            self.assertFalse(task.approved_file.exists())


class Unstarted(unittest.TestCase):
    """`criteria.unstarted`: a test command that starts a shell or Python on a script file the base
    commit lacks does not start there, whatever its exit; a module, a text and a file that is there do."""

    def test_python_on_a_file_the_base_lacks(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            where = Path(folder)
            (where / "tests").mkdir()
            (where / "tests" / "there.py").write_text("")
            for command in ("python3 tests/helper.py", "python tests/helper.py -v", "python3.12 -I -B tests/helper.py",
                            "/usr/bin/python3 -u tests/helper.py", "python3 -W ignore tests/helper.py", "python3 -X dev -- tests/helper.py"):
                self.assertEqual(criteria.unstarted(command, where), "tests/helper.py", command)
            for command in ("python3 -m unittest tests.test_helper", "python3 -c 'import helper'", "python3 tests/there.py",
                            "python3 -", "python3", "pythonista tests/helper.py", "python3 -mpytest tests/helper.py"):
                self.assertIsNone(criteria.unstarted(command, where), command)

    def test_a_shell_on_a_file_the_base_lacks_is_named(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(criteria.unstarted("sh tests/helper.sh", Path(folder)), "tests/helper.sh")
            self.assertIsNone(criteria.unstarted("sh -c 'exit 1'", Path(folder)))


class NightTrackChange(unittest.TestCase):
    """A night's task on the fast track that turns out to be a full change: its `small` approval by
    `alone` is replaced by a `full` one by `alone` while it still runs without the owner, and both stay
    in the history; with the owner there, or after a `full` approval, the second `--alone` is refused."""

    FULL = "## Acceptance criteria\n\nSize: full, because the footer has two places.\n\n1. The footer says 2026.\n2. The page title says 2026.\n"

    def night(self, folder: Path, mode: str = "alone"):
        task = FastTrackNotHis.task(FastTrackNotHis(), folder, night="2026-11-21", mode="alone")
        criteria.cmd_approve(task, str(task.small_file), "alone", plan=True)
        task.mode = mode
        full = folder / "criteria-full.md"
        full.write_text(self.FULL)
        return task, full

    def test_the_full_approval_replaces_the_small_one_while_it_runs_alone(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            task, full = self.night(Path(folder))
            record = criteria.cmd_approve(task, str(full), "alone", plan=True)
            self.assertEqual((record["by"], record["size"], record["number"], record["replaces"]), ("alone", "full", 2, 1))
            self.assertEqual([(old["by"], old["size"]) for old in record["history"]], [("alone", "small")])

    def test_with_the_owner_back_it_waits_for_his_yes(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            task, full = self.night(Path(folder), mode="with-owner")
            with self.assertRaises(criteria.CriteriaError) as refused:
                criteria.cmd_approve(task, str(full), "alone", plan=True)
            self.assertIn("runs with the owner", str(refused.exception))

    def test_a_second_full_approval_alone_is_refused(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            task, full = self.night(Path(folder))
            criteria.cmd_approve(task, str(full), "alone", plan=True)
            with self.assertRaises(criteria.CriteriaError) as refused:
                criteria.cmd_approve(task, str(full), "alone", plan=True)
            self.assertIn("has approval 2 of its criteria already (by alone)", str(refused.exception))


class ReadsOf(unittest.TestCase):
    """A read of the criteria whose words hold the characters str.splitlines breaks at, read back whole."""

    def test_a_read_whose_words_hold_a_line_separator(self) -> None:
        import json
        import tempfile
        import types
        words = "a\N{LINE SEPARATOR}b\N{PARAGRAPH SEPARATOR}c\x85d"
        with tempfile.TemporaryDirectory() as folder:
            task = types.SimpleNamespace(slug="demo", directory=Path(folder) / "tasks" / "demo")
            record = {"ts": "2026-11-21T10:00:00Z", "event": "criteria.read", "task": "demo", "silent": [words]}
            (Path(folder) / "events.jsonl").write_text(json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8")
            self.assertEqual([read["silent"] for read in criteria.reads_of(task)], [[words]])
