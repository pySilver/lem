"""The task picker (picker.py), as calls of the functions that hold its rules: the state of a task in
the board's words, and the ended tasks that keep a row. What agterm does with the picker is in tests/lem-picker.sh, with a stand-in for
agtermctl.

    python3 -B -m unittest discover -s tests/unit
"""

import importlib
import sys
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parents[2] / "skills" / "lem" / "scripts"
sys.path.insert(0, str(SCRIPTS))
picker = importlib.import_module("picker")


class StateWords(unittest.TestCase):
    def test_an_investigation_line_counts_on_any_line_of_the_newest_block(self) -> None:
        second = {
            "status": "building",
            "state": "2026-11-21T10:00Z building: an investigator reproduces the bug\ninvestigation: bug",
        }
        first = {
            "status": "building",
            "state": "2026-11-21T10:00Z building: investigation: question\ntype: question, because a report",
        }
        self.assertEqual(picker.state_words(second, None), picker.INVESTIGATING)
        self.assertEqual(picker.state_words(first, None), picker.INVESTIGATING)

    def test_a_lead_that_builds_is_no_investigation(self) -> None:
        task = {
            "status": "building",
            "state": "2026-11-21T10:00Z building: lead: builder\ntask 1 of 3",
        }
        self.assertEqual(picker.state_words(task, None), picker.WORDS["building"])
        self.assertEqual(
            picker.state_words({"status": "building", "state": None}, None),
            picker.WORDS["building"],
        )


NOW = datetime(2026, 11, 22, 12, 0, tzinfo=UTC)


def task(slug: str, status: str, since: datetime) -> dict:
    """A task as `project.read_tasks` gives it, with only what a row reads."""
    return {
        "slug": slug,
        "ask": slug,
        "status": status,
        "since": since.strftime("%Y-%m-%dT%H:%MZ"),
        "state": None,
        "track": "fast",
        "proposal": None,
    }


def ended(count: int, newest: datetime) -> list[dict]:
    """COUNT tasks that ended a day apart, `ended-01` the newest, and each ended one in turn landed, dropped or answered."""
    return [
        task(
            f"ended-{n:02d}",
            ("landed", "dropped", "answered")[n % 3],
            newest - timedelta(days=n - 1),
        )
        for n in range(1, count + 1)
    ]


def picked(tasks: list[dict], held: tuple[str, ...] = ()) -> list[str]:
    """The ids of the picker's rows over TASKS, with HELD the tasks that wait for the owner."""
    waiting = {
        key: []
        for key in (
            "breakers",
            "criteria",
            "after_dropped",
            "blocked",
            "plans",
            "pull_requests",
            "no_session",
            "stopped",
        )
    }
    waiting["held"] = [{"task": slug} for slug in held]
    with (
        mock.patch.object(picker.project, "read_tasks", return_value=tasks),
        mock.patch.object(picker.project, "cmd_waiting", return_value=waiting),
    ):
        return [r["id"] for r in picker.rows(Path("/nowhere"), NOW)]


class Ended(unittest.TestCase):
    """Criterion 5: the picker lists the tasks that ended last, as many as Done draws, whenever they ended."""

    def test_three_tasks_that_all_ended_a_month_ago_each_have_a_row(self) -> None:
        self.assertEqual(
            picked(ended(3, NOW - timedelta(days=30))),
            ["ended-01", "ended-02", "ended-03", picker.ALL],
        )

    def test_with_25_ended_tasks_the_20_that_ended_last_have_a_row_the_newest_first(
        self,
    ) -> None:
        self.assertEqual(picker.lem_board_model.DONE_SHOWN, 20)
        rows = picked(list(reversed(ended(25, NOW))))
        self.assertEqual(rows, [f"ended-{n:02d}" for n in range(1, 21)] + [picker.ALL])

    def test_what_waits_for_the_owner_and_what_builds_stay_above_the_ended_tasks(
        self,
    ) -> None:
        # the two above are older than every ended task: the order is by place, not by time
        tasks = [
            *ended(3, NOW),
            task("his-step", "held", NOW - timedelta(days=40)),
            task("builds", "building", NOW - timedelta(days=50)),
        ]
        self.assertEqual(
            picked(tasks, held=("his-step",)),
            ["his-step", "builds", "ended-01", "ended-02", "ended-03", picker.ALL],
        )


if __name__ == "__main__":
    unittest.main()
