"""The owner's status, the machine's one mark: where `lem_state` puts it, how
`project.py` reads it, and the spans without him that it gives a task, as calls of the
functions with records. The write of the mark and its read from two repositories are
facts of real checkouts, in tests/lem-state.sh.

    .venv/bin/python -B -m unittest discover -s tests/unit
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from lem import project
from lem import state as lem_state

SLUG = "report-dates"


def mark(ts: str, *, away: bool, words: str) -> dict:
    return {
        "ts": ts,
        "event": "owner",
        "task": None,
        "away": away,
        "by": "owner",
        "words": words,
        "repo": "/lem-unit/first",
    }


def night(ts: str) -> dict:
    return {
        "ts": ts,
        "event": "task.mode",
        "task": SLUG,
        "mode": "alone",
        "by": "lem",
        "words": "the night of 2026-11-19",
    }


class Mark(unittest.TestCase):
    """Each case runs with a folder of its own as XDG_CONFIG_HOME, and puts the variable
    back after: the unit level runs without tests/all.sh, and the home directory's mark
    is never read here."""

    def setUp(self) -> None:
        self.kept = os.environ.get("XDG_CONFIG_HOME")
        self.folder = tempfile.TemporaryDirectory()
        os.environ["XDG_CONFIG_HOME"] = self.folder.name

    def tearDown(self) -> None:
        if self.kept is None:
            os.environ.pop("XDG_CONFIG_HOME", None)
        else:
            os.environ["XDG_CONFIG_HOME"] = self.kept
        self.folder.cleanup()

    def test_the_place_follows_the_variable(self) -> None:
        self.assertEqual(
            lem_state.owner_mark(), Path(self.folder.name) / "lem" / "owner.jsonl"
        )

    def test_an_empty_variable_is_the_home_directory(self) -> None:
        os.environ["XDG_CONFIG_HOME"] = ""
        self.assertEqual(lem_state.config(), Path.home() / ".config" / "lem")

    def test_a_relative_variable_is_refused(self) -> None:
        os.environ["XDG_CONFIG_HOME"] = "config"
        with self.assertRaises(project.SettingsError) as caught:
            project.owner_records()
        self.assertIn(
            "XDG_CONFIG_HOME is 'config', a relative path", str(caught.exception)
        )

    def test_no_mark_is_the_owner_there_and_makes_nothing(self) -> None:
        records = project.owner_records()
        self.assertEqual(
            (records, project.owner_now(records)),
            ([], {"away": False, "since": None, "words": None}),
        )
        self.assertFalse((Path(self.folder.name) / "lem").exists())

    def test_the_newest_record_holds(self) -> None:
        folder = Path(self.folder.name) / "lem"
        folder.mkdir()
        (folder / "owner.jsonl").write_text(
            "".join(
                project.json.dumps(record) + "\n"
                for record in (
                    mark("2026-11-19T14:05:00Z", away=True, words="/lem im-away"),
                    mark("2026-11-19T16:30:00Z", away=False, words="/lem im-back"),
                )
            ),
            encoding="utf-8",
        )
        records = project.owner_records()
        self.assertEqual(
            project.owner_now(records),
            {"away": False, "since": "2026-11-19T16:30:00Z", "words": "/lem im-back"},
        )
        self.assertEqual(
            project.owner_now(records[:1]),
            {"away": True, "since": "2026-11-19T14:05:00Z", "words": "/lem im-away"},
        )

    def test_his_words_may_hold_a_line_separator(self) -> None:
        # the record as append_owner writes it: json.dumps with ensure_ascii=False keeps
        # U+2028, U+2029 and U+0085 as they are
        folder = Path(self.folder.name) / "lem"
        folder.mkdir()
        words = "away\u2028now\u2029and\x85later"
        (folder / "owner.jsonl").write_text(
            project.json.dumps(
                mark("2026-11-19T14:05:00Z", away=True, words=words), ensure_ascii=False
            )
            + "\n",
            encoding="utf-8",
        )
        records = project.owner_records()
        self.assertEqual(
            project.owner_now(records),
            {"away": True, "since": "2026-11-19T14:05:00Z", "words": words},
        )

    def test_a_line_that_does_not_read_is_refused_with_its_place(self) -> None:
        folder = Path(self.folder.name) / "lem"
        folder.mkdir()
        (folder / "owner.jsonl").write_text(
            project.json.dumps(mark("2026-11-19T14:05:00Z", away=True, words="x"))
            + "\nnot json\n",
            encoding="utf-8",
        )
        with self.assertRaises(project.SettingsError) as caught:
            project.owner_records()
        self.assertIn(
            f"{folder / 'owner.jsonl'}:2 does not read as JSON", str(caught.exception)
        )


class Spans(unittest.TestCase):
    """The spans in which a task ran without the owner, from its marks and the
    machine's records."""

    def test_a_back_ends_his_away_and_never_a_night(self) -> None:
        records = project.merged(
            [night("2026-11-19T02:00:00Z")],
            [
                mark("2026-11-19T01:00:00Z", away=True, words="I'm away"),
                mark("2026-11-19T02:10:00Z", away=False, words="/lem im-back"),
            ],
        )
        spans = project.runs_without_owner(SLUG, records, "2026-11-19T02:00:00Z")
        self.assertEqual(
            [(span["from"], span["to"]) for span in spans],
            [("2026-11-19T02:00:00Z", None)],
        )

    def test_a_day_task_runs_from_his_away_to_his_back(self) -> None:
        records = project.merged(
            [],
            [
                mark("2026-11-19T14:05:00Z", away=True, words="/lem im-away"),
                mark("2026-11-19T16:30:00Z", away=False, words="/lem im-back"),
            ],
        )
        spans = project.runs_without_owner(SLUG, records, "2026-11-19T14:00:00Z")
        self.assertEqual(
            [
                (
                    span["from"],
                    span["to"],
                    span["started"]["words"],
                    span["ended"]["words"],
                )
                for span in spans
            ],
            [
                (
                    "2026-11-19T14:05:00Z",
                    "2026-11-19T16:30:00Z",
                    "/lem im-away",
                    "/lem im-back",
                )
            ],
        )

    def test_on_one_second_the_repository_comes_first_and_each_list_keeps_its_order(
        self,
    ) -> None:
        events = [night("2026-11-19T14:05:00Z")]
        marks = [
            mark("2026-11-19T14:05:00Z", away=True, words="away"),
            mark("2026-11-19T14:05:00Z", away=False, words="back"),
        ]
        self.assertEqual(
            [
                (record["event"], record.get("away"))
                for record in project.merged(events, marks)
            ],
            [("task.mode", None), ("owner", True), ("owner", False)],
        )

    def test_an_away_and_a_back_before_the_task_opened_are_no_span_of_it(self) -> None:
        records = project.merged(
            [],
            [
                mark("2026-11-19T10:00:00Z", away=True, words="away"),
                mark("2026-11-19T11:00:00Z", away=False, words="back"),
            ],
        )
        self.assertEqual(
            project.runs_without_owner(SLUG, records, "2026-11-19T12:00:00Z"), []
        )


if __name__ == "__main__":
    unittest.main()
