"""A `lem-ask` card of a task's session in the task's folder, and the one end of each
card (cards.py): the first end recorded counts, from the session or from the board,
and the other writer reads it; the threads of one process each write under a name of
their own (decision 7 of docs/plans/2026-11-23-board-answers-a-card.md); the module that
the board's server calls holds no call of agterm, so an end from the board never answers
or closes the session's page.

    python3 -B -m unittest discover -s tests/unit
"""

import json
import re
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from typing import cast

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from lem import cards as lem_cards

SLUG = "export-notes"
SPEC = {
    "prompt": "Keep the empty cell?",
    "options": [{"id": "a", "label": "yes"}, {"id": "b", "label": "no, write a dash"}],
}


def answer(option: str, label: str, note: str | None = None) -> dict:
    one = {"selected": [option], "labels": [label], **({"text": note} if note else {})}
    return {"status": "answered", "answers": {"answer": one}}


A = answer("a", "yes")
B = answer("b", "no, write a dash", "a dash, as in the invoice export")


class Repository(unittest.TestCase):
    """A throwaway repository with the task's folder in its state folder."""

    def setUp(self) -> None:
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.repo = Path(self.dir.name).resolve() / "shop"
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        self.task = self.repo / ".lem" / "state" / "tasks" / SLUG
        self.task.mkdir(parents=True)

    def events(self) -> list[dict]:
        log = self.repo / ".lem" / "state" / "events.jsonl"
        return (
            [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
            if log.is_file()
            else []
        )


class TaskFolder(Repository):
    def test_the_task_of_the_session_in_its_repository(self) -> None:
        self.assertEqual(lem_cards.task_folder(self.repo, SLUG), self.task)

    def test_no_card_outside_a_task(self) -> None:
        self.assertIsNone(lem_cards.task_folder(self.repo, None))
        self.assertIsNone(
            lem_cards.task_folder(self.repo, "import-notes")
        )  # no folder of that task
        self.assertIsNone(lem_cards.task_folder(self.repo, "../shop"))  # no slug
        self.assertIsNone(
            lem_cards.task_folder(Path(self.dir.name), SLUG)
        )  # no repository
        self.assertFalse(
            (Path(self.dir.name) / ".lem").exists(),
            "a look for the task made a state folder",
        )

    def test_a_page_id_is_never_a_path(self) -> None:
        for page in ("../P1", "P1/x", ".P1", ""):
            with self.subTest(page=page), self.assertRaises(lem_cards.CardError):
                lem_cards.end_file(self.task, page)


class Keep(Repository):
    def test_the_card_holds_its_page_and_what_it_asks_and_logs_card_asked(self) -> None:
        html = b"<!doctype html><p>Keep the empty cell?</p>"
        lem_cards.keep(self.task, "P1", html, SPEC, "S1")
        self.assertEqual((self.task / "cards" / "P1.html").read_bytes(), html)
        card = cast("dict", lem_cards.card(self.task, "P1"))
        self.assertEqual(
            (card["page"], card["session"], card["chat"]), ("P1", "S1", True)
        )
        self.assertRegex(card["at"], r"\A\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ\Z")
        self.assertEqual(
            card["questions"],
            [
                {
                    "id": "answer",
                    "prompt": "Keep the empty cell?",
                    "mode": "single",
                    "optional": False,
                    "options": [
                        {"id": "a", "label": "yes"},
                        {"id": "b", "label": "no, write a dash"},
                    ],
                }
            ],
        )
        self.assertEqual(
            [(e["event"], e["task"], e["page"], e["prompt"]) for e in self.events()],
            [("card.asked", SLUG, "P1", "Keep the empty cell?")],
        )
        self.assertIsNone(lem_cards.ended(self.task, "P1"))

    def test_questions_take_the_ids_the_page_gives_them(self) -> None:
        spec = {
            "title": "Two things",
            "chat": False,
            "questions": [
                {"prompt": "Which cache?", "options": ["Redis", {"label": "Postgres"}]},
                {"id": "why", "mode": "text", "optional": True},
                {"prompt": "Radius?", "controls": [{"id": "r", "label": "Radius"}]},
            ],
        }
        found = lem_cards.questions_of(spec)
        self.assertEqual(
            [(q["id"], q["mode"], q["optional"]) for q in found],
            [("q1", "single", False), ("why", "text", True), ("q3", "tune", False)],
        )
        self.assertEqual(
            found[0]["options"],
            [{"id": "Redis", "label": "Redis"}, {"id": "o2", "label": "Postgres"}],
        )
        self.assertEqual(found[1]["prompt"], "Two things")


class FirstEndCounts(Repository):
    def setUp(self) -> None:
        super().setUp()
        lem_cards.keep(self.task, "P1", b"<p>card</p>", SPEC, "S1")

    def test_the_board_first_then_the_session_reads_the_board(self) -> None:
        won, record = lem_cards.end(
            self.task,
            "P1",
            "answered",
            "board",
            B,
            via="door",
            device="phone",
            agent="Mozilla/5.0 (iPhone)",
        )
        self.assertTrue(won)
        self.assertEqual(
            (record["from"], record["via"], record["device"], record["agent"]),
            ("board", "door", "phone", "Mozilla/5.0 (iPhone)"),
        )
        won, on_record = lem_cards.end(self.task, "P1", "answered", "session", A)
        self.assertFalse(won)
        self.assertEqual(on_record["answer"], B)
        self.assertEqual(
            cast("dict", lem_cards.ended(self.task, "P1"))["from"], "board"
        )
        self.assertRegex(
            lem_cards.took_effect(on_record),
            r"\Ano, write a dash was taken on the board at \d\d:\d\d, from the phone\Z",
        )
        self.assertEqual(
            [
                (e["event"], e.get("from"), e.get("via"), e.get("device"))
                for e in self.events()
            ][1:],
            [("card.answered", "board", "door", "phone")],
        )

    def test_the_session_first_then_the_board_is_told_what_took_effect(self) -> None:
        self.assertTrue(lem_cards.end(self.task, "P1", "answered", "session", A)[0])
        won, on_record = lem_cards.end(
            self.task, "P1", "answered", "board", B, via="local", device="computer"
        )
        self.assertFalse(won)
        self.assertRegex(
            lem_cards.took_effect(on_record),
            r"\Ayes was taken in the session at \d\d:\d\d\Z",
        )
        self.assertEqual(
            [e["event"] for e in self.events()], ["card.asked", "card.answered"]
        )

    def test_a_close_or_a_dismissal_is_an_end_too(self) -> None:
        self.assertTrue(lem_cards.end(self.task, "P1", "closed", "session")[0])
        won, on_record = lem_cards.end(
            self.task, "P1", "answered", "board", B, via="door", device="phone"
        )
        self.assertFalse(won)
        self.assertRegex(
            lem_cards.took_effect(on_record),
            r"\Athe card was closed in the session at \d\d:\d\d\Z",
        )
        self.assertEqual(
            [(e["event"], e.get("status")) for e in self.events()][1:],
            [("card.closed", "closed")],
        )

    def test_an_end_takes_its_form(self) -> None:
        for status, source, given in (
            ("taken", "session", None),
            ("answered", "phone", A),
            ("answered", "board", None),
            ("closed", "session", A),
        ):
            with (
                self.subTest(status=status, source=source),
                self.assertRaises(lem_cards.CardError),
            ):
                lem_cards.end(self.task, "P1", status, source, given)
        self.assertIsNone(lem_cards.ended(self.task, "P1"))

    def test_threads_of_one_process_each_write_their_own_record_and_one_counts(
        self,
    ) -> None:
        start = threading.Barrier(8)
        results: list[tuple[bool, dict] | None] = [None] * 8

        def one(number: int) -> None:
            start.wait()
            results[number] = lem_cards.end(
                self.task,
                "P1",
                "answered",
                "board",
                answer(f"o{number}", f"option {number}"),
                via="door",
                device="phone",
            )

        threads = [threading.Thread(target=one, args=(number,)) for number in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        # each thread set its own place
        ends = cast("list[tuple[bool, dict]]", results)
        winners = [record for won, record in ends if won]
        self.assertEqual(len(winners), 1)
        on_record = lem_cards.ended(self.task, "P1")
        self.assertEqual(
            on_record,
            winners[0],
            "the file on record is not the record of the one writer that owns the end",
        )
        self.assertTrue(
            all(record == on_record for _, record in ends),
            "a writer that lost was told another end than the one on record",
        )
        self.assertEqual(
            sorted(path.name for path in (self.task / "cards").iterdir()),
            ["P1.end.json", "P1.html", "P1.json"],
        )
        self.assertEqual([e["event"] for e in self.events()].count("card.answered"), 1)


class NoAgterm(unittest.TestCase):
    def test_the_module_the_board_calls_answers_and_closes_no_page(self) -> None:
        text = Path(lem_cards.__file__).read_text(encoding="utf-8")
        self.assertIsNone(
            re.search(r"agtermctl|subprocess|overlay\W+(submit|close)", text)
        )


if __name__ == "__main__":
    unittest.main()
