"""The records of the night's and the retro's proposals, the reviewer's verdicts and items, and the
owner's drop of an item (`lem project proposals`), as calls of their functions over a state folder in
a temporary directory. That `waiting` no longer lists or counts the retros is tests/lem-decisions.sh's,
and that `prune` keeps the records and the items is tests/lem-state.sh's.

    python3 -B -m unittest discover -s tests/unit
"""

import contextlib
import io
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "lem" / "scripts"))
import project  # noqa: E402

MORNING = datetime(2026, 11, 23, 6, 55, tzinfo=timezone.utc)
TEN = datetime(2026, 11, 23, 10, 0, tzinfo=timezone.utc)


def proposal(area: str, move: str, where: str = "skills/lem/stages/learn.md", source: str = "the task gift-note's records") -> dict:
    return {"area": area, "move": move, "body": f"Why: {move.lower()}", "source": source, "where": where}


class Records(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.main = Path(self.temp.name) / "shop"
        self.state = self.main / ".lem" / "state"
        self.state.mkdir(parents=True)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def add(self, kind: str, day: str, proposals: list, now: datetime = MORNING, read: str = "the tasks since the last retro") -> dict:
        return project.cmd_proposals_add(self.state, kind, day, {"read": read, "proposals": proposals}, now)

    def record(self, kind: str, day: str) -> dict:
        return json.loads(project.record_file(self.state, kind, day).read_text(encoding="utf-8"))

    def refused(self, call, *args) -> str:
        with self.assertRaises(project.SettingsError) as caught:
            call(*args)
        return str(caught.exception)

    def eleven(self) -> None:
        # criterion 5: of 11 proposals, 9 pass, 5 about lessons, 3 about the board, 1 about the tests
        self.add("night", "2026-11-24", [proposal("tests", "Wait for the port before the PX check", where="tests/lem-serve.sh", source="the free hour's run of tests/lem-serve.sh")])
        self.add("retro", "2026-11-24", [proposal("lessons", f"Lesson {n}") for n in range(1, 7)] + [proposal("board", f"Board {n}", where="skills/lem/assets/board.css") for n in range(1, 5)])

    def task(self, slug: str, ask: str, status: str | None) -> None:
        directory = self.state / "tasks" / slug
        directory.mkdir(parents=True)
        (directory / "ask.txt").write_text(ask + "\n", encoding="utf-8")
        if status:
            (directory / "state.md").write_text(f"2026-11-24T08:00Z {status}: a line\n", encoding="utf-8")


class Add(Records):
    def test_a_retro_with_no_proposal_writes_its_days_file_with_what_it_read(self):
        # criterion 3: the retro of 2026-11-25 proposes nothing, and its file says what it read
        added = self.add("retro", "2026-11-25", [], read="the tasks gift-note and refund-total since 2026-11-24T06:55:00Z")
        self.assertEqual((added["numbers"], added["at"]), ([], "2026-11-23T06:55:00Z"))
        record = self.record("retro", "2026-11-25")
        self.assertEqual((record["date"], record["kind"], record["proposals"], record["refuted"], record["passed"], record["dropped"]),
                         ("2026-11-25", "retro", [], [], [], []))
        self.assertEqual(record["runs"], [{"at": "2026-11-23T06:55:00Z", "read": "the tasks gift-note and refund-total since 2026-11-24T06:55:00Z", "proposals": []}])
        self.assertEqual(project.cmd_proposals_read(self.state)["newest"]["retro"]["date"], "2026-11-25")

    def test_a_second_retro_of_the_day_adds_after_the_first_and_keeps_its_verdicts(self):
        self.add("retro", "2026-11-23", [proposal("lessons", "Move the rule"), proposal("board", "Color the key")])
        project.cmd_proposals_verdict(self.state, {"verdicts": [{"proposal": "retro of 2026-11-23 #1", "refuted": "a first-time lesson, with no question in it"}]}, "2026-11-23")
        second = self.add("retro", "2026-11-23", [proposal("tests", "Wait for the port")], now=TEN, read="the naps since 06:55")
        self.assertEqual((second["numbers"], second["names"]), ([3], ["retro of 2026-11-23 #3"]))
        record = self.record("retro", "2026-11-23")
        self.assertEqual([p["number"] for p in record["proposals"]], [1, 2, 3])
        self.assertEqual([(run["at"], run["proposals"]) for run in record["runs"]], [("2026-11-23T06:55:00Z", [1, 2]), ("2026-11-23T10:00:00Z", [3])])
        self.assertEqual(record["refuted"], [{"number": 1, "reason": "a first-time lesson, with no question in it", "day": "2026-11-23"}])
        self.assertEqual(project.cmd_proposals_read(self.state)["newest"]["retro"], {"date": "2026-11-23", "at": "2026-11-23T10:00:00Z", "read": "the naps since 06:55"})

    def test_a_run_that_is_not_in_the_form_is_refused_and_writes_nothing(self):
        self.assertIn("is not an object with area, move, body, source, where",
                      self.refused(project.cmd_proposals_add, self.state, "night", "2026-11-24", {"read": "x", "proposals": [{"area": "tests"}]}, MORNING))
        self.assertIn("is lower-case words", self.refused(self.add, "night", "2026-11-24", [proposal("The Tests", "Wait")]))
        self.assertIn("is one line", self.refused(self.add, "night", "2026-11-24", [proposal("tests", "Wait\nfor the port")]))
        self.assertIn("--date is the run's day", self.refused(self.add, "night", "24 Nov", []))
        self.assertFalse((self.state / "night").exists())


class OldForm(Records):
    def test_a_retro_file_in_the_form_of_the_question_page_is_refused_with_the_fix(self):
        (self.state / "retros").mkdir()
        (self.state / "retros" / "2026-11-23.json").write_text(json.dumps({"title": "The retro", "questions": [{"id": "p1", "prompt": "Move the rule?"}]}), encoding="utf-8")
        said = self.refused(project.cmd_proposals_read, self.state)
        self.assertIn("2026-11-23.json: it holds questions in the form of the question page", said)
        self.assertIn("The maintaining session converts it by hand into a record of proposals", said)
        self.assertIn("each question a proposal with no verdict", said)
        # and add refuses to write into it
        self.assertIn("question page", self.refused(self.add, "retro", "2026-11-23", []))

    def test_a_record_that_does_not_read_is_refused_with_the_form(self):
        (self.state / "night").mkdir()
        (self.state / "night" / "2026-11-24.json").write_text("not json", encoding="utf-8")
        (self.state / "night" / "2026-11-24.md").write_text("# The night\n", encoding="utf-8")
        said = self.refused(project.cmd_proposals_read, self.state)
        self.assertIn("2026-11-24.json: it does not read as JSON", said)
        self.assertIn("only `lem project proposals` writes one", said)


class Verdict(Records):
    def test_the_passed_ones_become_one_item_for_each_area_and_the_refuted_ones_stay_with_their_reason(self):
        self.eleven()
        verdicts = [{"proposal": "night of 2026-11-24 #1", "passed": "tests"}]
        verdicts += [{"proposal": f"retro of 2026-11-24 #{n}", "passed": "lessons"} for n in range(1, 6)]
        verdicts += [{"proposal": "retro of 2026-11-24 #6", "refuted": "a first-time lesson, with no question in it"}]
        verdicts += [{"proposal": f"retro of 2026-11-24 #{n}", "passed": "board"} for n in range(7, 10)]
        verdicts += [{"proposal": "retro of 2026-11-24 #10", "refuted": "the rule is in lem.css already"}]
        titles = {"tests": "The PX check of the board server fails by chance", "lessons": "Five lessons of the retro", "board": "The board's colors"}
        done = project.cmd_proposals_verdict(self.state, {"verdicts": verdicts, "titles": titles}, "2026-11-24")
        self.assertEqual(done["refuted"], ["retro of 2026-11-24 #6", "retro of 2026-11-24 #10"])
        self.assertEqual([(item["area"], item["path"], len(item["proposals"])) for item in done["items"]],
                         [("tests", ".lem/state/backlog/the-px-check-of-the-board-server-fails-by-chance.md", 1),
                          ("lessons", ".lem/state/backlog/five-lessons-of-the-retro.md", 5), ("board", ".lem/state/backlog/the-board-s-colors.md", 3)])
        self.assertEqual(sorted(file.name for file in (self.state / "backlog").iterdir()),
                         ["five-lessons-of-the-retro.md", "the-board-s-colors.md", "the-px-check-of-the-board-server-fails-by-chance.md"])
        tests = (self.main / done["items"][0]["path"]).read_text(encoding="utf-8")
        self.assertTrue(tests.startswith("---\nworth: later\nwhere: tests/lem-serve.sh\nadded: 2026-11-24\nproposals: night of 2026-11-24 #1\n---\n"
                                         "# The PX check of the board server fails by chance\n"), tests)
        self.assertIn("From the night of 2026-11-24, proposal 1. Its source: the free hour's run of tests/lem-serve.sh.", tests)
        board = (self.main / done["items"][2]["path"]).read_text(encoding="utf-8")
        self.assertIn("proposals: retro of 2026-11-24 #7, retro of 2026-11-24 #8, retro of 2026-11-24 #9\n", board)
        # criterion 4: the refuted one stays in the retro's file with its reason
        record = self.record("retro", "2026-11-24")
        self.assertIn({"number": 6, "reason": "a first-time lesson, with no question in it", "day": "2026-11-24"}, record["refuted"])
        self.assertIn({"number": 7, "area": "board", "item": ".lem/state/backlog/the-board-s-colors.md", "day": "2026-11-24"}, record["passed"])
        self.assertEqual(self.record("night", "2026-11-24")["passed"],
                         [{"number": 1, "area": "tests", "item": ".lem/state/backlog/the-px-check-of-the-board-server-fails-by-chance.md", "day": "2026-11-24"}])
        read = project.cmd_proposals_read(self.state)
        self.assertEqual((read["undecided"], len(read["refuted"]), len(read["passed"])), ([], 2, 9))

    def test_no_item_on_a_morning_where_nothing_passed(self):
        self.add("retro", "2026-11-23", [proposal("lessons", "Move the rule")])
        done = project.cmd_proposals_verdict(self.state, {"verdicts": [{"proposal": "retro of 2026-11-23 #1", "refuted": "a first-time lesson, with no question in it"}]}, "2026-11-23")
        self.assertEqual(done["items"], [])
        self.assertFalse((self.state / "backlog").exists())

    def test_an_item_name_that_is_taken_gets_the_next_number(self):
        self.add("retro", "2026-11-23", [proposal("board", "Color the key"), proposal("board", "Color the chip")])
        project.cmd_proposals_verdict(self.state, {"verdicts": [{"proposal": "retro of 2026-11-23 #1", "passed": "board"}], "titles": {"board": "The board's colors"}}, "2026-11-23")
        again = project.cmd_proposals_verdict(self.state, {"verdicts": [{"proposal": "retro of 2026-11-23 #2", "passed": "board"}], "titles": {"board": "The board's colors"}}, "2026-11-23")
        self.assertEqual(again["items"][0]["path"], ".lem/state/backlog/the-board-s-colors-2.md")

    def test_a_proposal_judged_once_is_not_judged_again_and_a_wrong_verdict_writes_nothing(self):
        self.add("retro", "2026-11-23", [proposal("board", "Color the key"), proposal("lessons", "Move the rule")])
        project.cmd_proposals_verdict(self.state, {"verdicts": [{"proposal": "retro of 2026-11-23 #1", "refuted": "the rule is there"}]}, "2026-11-23")
        before = self.record("retro", "2026-11-23")
        self.assertIn("has a verdict already", self.refused(project.cmd_proposals_verdict, self.state, {"verdicts": [
            {"proposal": "retro of 2026-11-23 #2", "passed": "lessons"}, {"proposal": "retro of 2026-11-23 #1", "passed": "board"}], "titles": {"lessons": "L", "board": "B"}}, "2026-11-24"))
        self.assertIn("gives no title for the area lessons", self.refused(project.cmd_proposals_verdict, self.state, {"verdicts": [
            {"proposal": "retro of 2026-11-23 #2", "passed": "lessons"}]}, "2026-11-24"))
        self.assertIn("has 2 proposals", self.refused(project.cmd_proposals_verdict, self.state, {"verdicts": [{"proposal": "retro of 2026-11-23 #3", "refuted": "x"}]}, "2026-11-24"))
        self.assertIn("there is no record of the night of 2026-11-23", self.refused(project.cmd_proposals_verdict, self.state, {"verdicts": [{"proposal": "night of 2026-11-23 #1", "refuted": "x"}]}, "2026-11-24"))
        self.assertEqual(self.record("retro", "2026-11-23"), before)
        self.assertFalse((self.state / "backlog").exists())


class Drop(Records):
    def items(self) -> dict:
        self.eleven()
        verdicts = [{"proposal": "night of 2026-11-24 #1", "passed": "tests"}] + [{"proposal": f"retro of 2026-11-24 #{n}", "passed": "board"} for n in (7, 8)]
        return {item["area"]: item["path"] for item in project.cmd_proposals_verdict(
            self.state, {"verdicts": verdicts, "titles": {"tests": "Tests flaky check", "board": "The board's colors"}}, "2026-11-24")["items"]}

    def test_a_drop_removes_the_file_at_once_and_keeps_the_drop_in_the_retros_file(self):
        # criterion 7: the owner drops the item about the board's colors
        board = self.items()["board"]
        done = project.cmd_proposals_drop(self.state, board, "2026-11-25")
        self.assertEqual(done, {"dropped": True, "item": board, "proposals": ["retro of 2026-11-24 #7", "retro of 2026-11-24 #8"], "day": "2026-11-25"})
        self.assertFalse((self.main / board).exists())
        self.assertEqual(self.record("retro", "2026-11-24")["dropped"], [
            {"number": 7, "text": "Board 1", "said": "the owner dropped it", "day": "2026-11-25", "item": board},
            {"number": 8, "text": "Board 2", "said": "the owner dropped it", "day": "2026-11-25", "item": board}])
        # criterion 8: a later reviewer reads the drop with its day
        read = project.cmd_proposals_read(self.state)
        self.assertEqual([(one["name"], one["move"], one["said"], one["day"]) for one in read["dropped"]],
                         [("retro of 2026-11-24 #7", "Board 1", "the owner dropped it", "2026-11-25"),
                          ("retro of 2026-11-24 #8", "Board 2", "the owner dropped it", "2026-11-25")])
        self.assertIn("is not there: it was dropped", self.refused(project.cmd_proposals_drop, self.state, board, "2026-11-25"))

    def test_a_drop_is_refused_while_a_task_that_has_not_ended_holds_the_item(self):
        tests = self.items()["tests"]
        self.task("tests-flaky-check", tests, "building")
        with self.assertRaises(project.ItemRefused) as caught:
            project.cmd_proposals_drop(self.state, tests, "2026-11-25")
        self.assertIn("the task tests-flaky-check (building) builds the item", str(caught.exception))
        self.assertEqual(caught.exception.answer, {"dropped": False, "item": tests, "held_by": "tests-flaky-check", "status": "building"})
        self.assertTrue((self.main / tests).is_file())
        self.assertEqual(self.record("night", "2026-11-24")["dropped"], [])

    def test_a_task_with_no_state_yet_holds_the_item_and_one_that_ended_does_not(self):
        tests = self.items()["tests"]
        self.task("tests-flaky-check", str(self.main / tests), None)
        self.assertEqual(project.item_holder(self.state, tests), {"task": "tests-flaky-check", "status": None})
        (self.state / "tasks" / "tests-flaky-check" / "state.md").write_text("2026-11-24T09:00Z dropped: the owner dropped it\n", encoding="utf-8")
        self.task("another-ask", f"{tests} and more", "building")
        self.assertIsNone(project.item_holder(self.state, tests))
        self.assertTrue(project.cmd_proposals_drop(self.state, tests, "2026-11-25")["dropped"])

    def test_a_path_outside_the_state_folders_backlog_is_refused(self):
        self.items()
        self.assertIn("is not the path of an item of .lem/state/backlog/", self.refused(project.cmd_proposals_drop, self.state, "docs/backlog/refund-total-zero.md", "2026-11-25"))
        self.assertIsNone(project.backlog_item_of(self.state, "/elsewhere/.lem/state/backlog/x.md"))
        self.assertEqual(project.backlog_item_of(self.state, f" {self.state}/backlog/x.md\n"), ".lem/state/backlog/x.md")

    def test_task_dir_refuses_the_path_of_an_item_the_owner_dropped(self):
        board = self.items()["board"]
        self.assertIsNone(project.dropped_item_refusal(self.state, board))
        self.assertIsNone(project.dropped_item_refusal(self.state, "Fix the board's colors"))
        project.cmd_proposals_drop(self.state, board, "2026-11-25")
        root = Path("/lem-unit/shop")
        project.STATE_ROOTS[root] = self.state
        self.addCleanup(project.STATE_ROOTS.pop, root, None)
        with contextlib.redirect_stdout(io.StringIO()):
            said = self.refused(project.cmd_task_dir, root, "the-board-s-colors", board, None)
        self.assertEqual(said, "the item was dropped: read the backlog again (.lem/state/backlog/the-board-s-colors.md is no longer in the state folder's backlog)")
        self.assertFalse((self.state / "tasks" / "the-board-s-colors").exists())


class Refuted(Records):
    def test_the_read_gives_every_refuted_one_of_every_day_with_its_day(self):
        # criterion 8: the reviewer of 2026-11-25 meets a proposal a reviewer refuted on 2026-11-23
        self.add("retro", "2026-11-23", [proposal("lessons", "Move the rule")])
        project.cmd_proposals_verdict(self.state, {"verdicts": [{"proposal": "retro of 2026-11-23 #1", "refuted": "a first-time lesson, with no question in it"}]}, "2026-11-23")
        self.add("retro", "2026-11-25", [proposal("lessons", "Move the rule")])
        read = project.cmd_proposals_read(self.state)
        self.assertEqual([(one["name"], one["move"], one["reason"], one["day"]) for one in read["refuted"]],
                         [("retro of 2026-11-23 #1", "Move the rule", "a first-time lesson, with no question in it", "2026-11-23")])
        self.assertEqual([one["name"] for one in read["undecided"]], ["retro of 2026-11-25 #1"])

    def test_a_morning_whose_reviewer_did_not_finish_is_read_on_the_next(self):
        self.add("night", "2026-11-24", [proposal("tests", "Wait for the port")])
        self.add("retro", "2026-11-24", [proposal("board", "Color the key")])
        self.add("retro", "2026-11-25", [])
        self.assertEqual([one["name"] for one in project.cmd_proposals_read(self.state)["undecided"]], ["night of 2026-11-24 #1", "retro of 2026-11-24 #1"])


if __name__ == "__main__":
    unittest.main()
