"""`lem criteria change`: a change of the criteria from the owner's note, on the standard track while they
wait for his yes (the task criteria-change-asks-again, task 1). The change keeps the text he answered,
writes the new `criteria.md`, logs it and writes a new wait, and approves nothing; its pairs show each
changed criterion's text before beside its text after; his typed No is recorded as the answer of the
criteria's row before the new text is written; a stop in the middle is ended by a second run; and the
change and his yes take one lock. Each is called in this process over a task folder, with `lem project
state` and `lem project log` stood in for by writes of the same events into the log; the command's
journey with the real `lem project state` runs once in tests/lem-settings.sh.

    python3 -B -m unittest tests.unit.test_criteria_change
"""

import importlib
import json
import sys
import tempfile
import threading
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "lem" / "scripts"))
criteria = importlib.import_module("criteria")
project = importlib.import_module("project")
bm = importlib.import_module("lem_board_model")
lem_answers = importlib.import_module("lem_answers")

SLUG = "invoice-export-empty-cells"
START = datetime(2026, 11, 23, 15, 0, tzinfo=timezone.utc)
HEAD = "## Acceptance criteria\n\nSize: full, because the export changes in three places.\n\n"
ONE = "1. An export keeps the order's number: order 1042 exports as 1042.\n"
TWO = "2. An export keeps an empty cell: order 1042 with no note exports an empty note cell.\n"
THREE = "3. An export ends with a line break.\n"
NEW_TWO = "2. An export keeps an empty cell and an empty row: order 1042 with no note and a blank line exports both.\n"
CRITERIA = HEAD + ONE + TWO + THREE
CHANGED = HEAD + ONE + NEW_TWO + THREE
NOTE = "criterion 2 must also cover empty rows"


class Folder(unittest.TestCase):
    """A task's folder in a state folder, its log, and a task of criteria.py over them. `state` and `log`
    of project.py are stood in for: each appends the event project.py appends, a minute after the last."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state = Path(self.tmp.name) / "state"
        self.events = self.state / "events.jsonl"
        self.minute = 0
        self.task = criteria.Task.__new__(criteria.Task)
        self.task.slug, self.task.night, self.task.mode, self.task.repo = SLUG, None, "with-owner", Path(self.tmp.name)
        self.task.directory = self.state / "tasks" / SLUG
        self.task.directory.mkdir(parents=True)
        self.task.approved_file, self.task.small_file = self.task.directory / "criteria.json", self.task.directory / "criteria.md"
        self.task.read_mode = lambda: self.task.mode
        self.task.log = lambda event, **fields: self.append(event, **fields)
        self.stop_state = False
        self.calls: list[tuple[str, ...]] = []
        patcher = mock.patch.object(criteria, "script", side_effect=self.script)
        patcher.start()
        self.addCleanup(patcher.stop)

    def append(self, event: str, **fields: object) -> dict:
        self.minute += 1
        # the log's own time, as project.py writes it, for a case of two blocks in one second
        moment = datetime.now(timezone.utc) if getattr(self, "real_clock", False) else START + timedelta(minutes=self.minute)
        record = {"ts": moment.strftime("%Y-%m-%dT%H:%M:%SZ"), "event": event, "task": SLUG, **fields}
        with self.events.open("a", encoding="utf-8") as log:
            log.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record

    def held(self, text: str, *lines: str) -> dict:
        return self.append("task.state", status="held", text=text, lines=list(lines))

    def script(self, name: str, repo: Path, *args: str) -> str:
        self.calls.append((name, *args))
        if name == "project.py" and args[0] == "state":
            if self.stop_state:
                raise KeyboardInterrupt("the change stopped before its held block")
            record = self.append("task.state", status=args[2], text=args[3], lines=list(args[4:]))
            return json.dumps({"slug": SLUG, "status": args[2], "since": record["ts"]})
        raise AssertionError(f"no stand-in for {name} {args}")

    def file(self, text: str, name: str = "changed.md") -> str:
        path = Path(self.tmp.name) / name
        path.write_text(text, encoding="utf-8")
        return str(path)

    def named(self, event: str) -> list[dict]:
        return [json.loads(line) for line in self.events.read_text(encoding="utf-8").splitlines() if json.loads(line)["event"] == event]

    def waiting(self, text: str = CRITERIA, block: str = criteria.INTERVIEW_WAIT) -> dict:
        """The interview's criteria that wait for his yes: its held block, and criteria.md."""
        self.task.small_file.write_text(text, encoding="utf-8")
        return self.held(block, "type: feat, because the export loses empty cells")

    def refused(self, call, *args) -> str:
        with self.assertRaises(criteria.CriteriaError) as caught:
            call(*args)
        return str(caught.exception)


class AChangeWaitsForHisYes(Folder):
    """Criteria 1 and 4: his No with a note becomes a change Lem writes, which waits for his yes again,
    with each changed criterion's text before beside its text after; nothing is approved."""

    def test_the_change_keeps_the_text_he_answered_and_writes_a_new_wait(self) -> None:
        block = self.waiting()
        said = criteria.cmd_change(self.task, self.file(CHANGED), NOTE)
        self.assertEqual(self.task.small_file.read_text(encoding="utf-8"), CHANGED)
        kept = json.loads((self.task.directory / "criteria-before.json").read_text(encoding="utf-8"))
        self.assertEqual((kept["ts"], kept["text"], kept["words"]), (block["ts"], CRITERIA, NOTE))
        newest = criteria.newest_block(self.task)
        self.assertEqual((newest["status"], newest["text"]), ("held", "the criteria wait for the owner: changed from the owner's note"))
        [event] = self.named("criteria.changed")
        self.assertEqual((event["words"], event["block"], len(event["pairs"])), (NOTE, block["ts"], 1))
        self.assertNotEqual(event["before"], event["after"])
        # nothing is approved: no criteria.json, no approval event, and the build has no yes to start from
        self.assertFalse(self.task.approved_file.exists())
        self.assertEqual(self.named("criteria.approved"), [])
        [pair] = said["pairs"]
        self.assertEqual(pair["change"], "changed")
        self.assertEqual((pair["before"]["n"], pair["before"]["text"]), (2, TWO[3:].strip()))
        self.assertEqual((pair["after"]["n"], pair["after"]["text"]), (2, NEW_TWO[3:].strip()))
        self.assertEqual(said["shown"], criteria.shown_digest(CHANGED.encode("utf-8")))
        self.assertFalse(said["resumed"])

    def test_a_second_no_changes_the_changed_text_again(self) -> None:
        self.waiting()
        criteria.cmd_change(self.task, self.file(CHANGED), NOTE)
        again = CHANGED.replace("exports both.", "exports both, each as its own row.")
        said = criteria.cmd_change(self.task, self.file(again, "again.md"), "each its own row")
        self.assertEqual([(p["before"]["text"], p["after"]["text"]) for p in said["pairs"]], [(NEW_TWO[3:].strip(), again.splitlines()[5][3:])])
        self.assertEqual(len(self.named("task.state")), 3)

    def test_the_pairs_again_while_the_wait_stands(self) -> None:
        self.waiting()
        made = criteria.cmd_change(self.task, self.file(CHANGED), NOTE)
        again = criteria.cmd_pairs(self.task)
        self.assertEqual((again["pairs"], again["words"], again["shown"]), (made["pairs"], NOTE, made["shown"]))
        self.held("lead: builder")
        self.assertIn("no change of invoice-export-empty-cells's criteria waits for the owner's yes", self.refused(criteria.cmd_pairs, self.task))


    def test_the_new_wait_is_a_new_row_also_in_the_same_second(self) -> None:
        """A change in the second of the block he answered waits for the next second, so that its wait
        has a key of its own and his No on record answers the old wait only."""
        self.real_clock = True
        block = self.waiting()
        criteria.cmd_typed(self.task, NOTE)
        changed = criteria.cmd_change(self.task, self.file(CHANGED), NOTE)
        newest = criteria.newest_block(self.task)
        self.assertNotEqual(criteria.row_key(self.task, newest), criteria.row_key(self.task, block))
        self.assertIsNone(criteria.owners_no(self.task, newest))
        self.assertEqual(criteria.cmd_approve(self.task, str(self.task.small_file), "owner", shown=changed["shown"])["by"], "owner")


class Pairs(unittest.TestCase):
    """Criterion 4: the criteria before and after are paired by their text, never by their number."""

    @staticmethod
    def pairs(before: str, after: str) -> list[tuple]:
        found = criteria.change_of(before, after)["pairs"]
        return [(p["change"], p.get("before", {}).get("n"), p.get("after", {}).get("n")) for p in found]

    def test_one_changed(self) -> None:
        self.assertEqual(self.pairs(CRITERIA, CHANGED), [("changed", 2, 2)])

    def test_a_removal_keeps_the_next_criterion_as_it_was(self) -> None:
        self.assertEqual(self.pairs(CRITERIA, HEAD + ONE + THREE.replace("3.", "2.")), [("removed", 2, None)])

    def test_two_changed_in_one_note_are_two_pairs(self) -> None:
        both = HEAD + ONE.replace("1042 exports", "1042 still exports") + NEW_TWO + THREE
        self.assertEqual(self.pairs(CRITERIA, both), [("changed", 1, 1), ("changed", 2, 2)])

    def test_one_replaced_by_two_is_a_removal_and_two_additions(self) -> None:
        split = HEAD + ONE + "2. An export keeps an empty cell: order 1042.\n3. An export keeps an empty row: order 1043.\n" + THREE.replace("3.", "4.")
        self.assertEqual(self.pairs(CRITERIA, split), [("removed", 2, None), ("added", None, 2), ("added", None, 3)])

    def test_an_added_criterion_and_a_new_line_break_that_is_no_change(self) -> None:
        wrapped = HEAD + ONE + TWO.replace(": order", ":\n   order") + THREE + "4. An export names its day.\n"
        self.assertEqual(self.pairs(CRITERIA, wrapped), [("added", None, 4)])


class Refusals(Folder):
    """Each refusal exits with a message that names the fix, and writes nothing."""

    def untouched(self) -> None:
        self.assertFalse((self.task.directory / "criteria-before.json").exists())
        self.assertEqual(self.named("criteria.changed"), [])

    def test_no_words_no_file_the_same_criteria_and_a_test_line(self) -> None:
        self.waiting()
        self.assertIn("change needs --words", self.refused(criteria.cmd_change, self.task, self.file(CHANGED), "  "))
        self.assertIn("is not a file", self.refused(criteria.cmd_change, self.task, str(Path(self.tmp.name) / "none.md"), NOTE))
        self.assertIn("has the same criteria as the ones the owner answered: nothing changed",
                      self.refused(criteria.cmd_change, self.task, self.file(CRITERIA.replace(": order", ":\n   order")), NOTE))
        tested = CHANGED.replace(THREE, THREE + "   - test: `sh tests/end.sh` in `tests/end.sh`\n")
        self.assertIn("criterion 3 of changed.md has a test line", self.refused(criteria.cmd_change, self.task, self.file(tested), NOTE))
        self.assertIn("the section starts with `Size: full", self.refused(criteria.cmd_change, self.task, self.file("## Acceptance criteria\n\n1. One.\n"), NOTE))
        self.untouched()

    def test_an_answer_on_record_that_does_not_read(self) -> None:
        """Review 1, finding 3: a record of the row that is no JSON is a refusal that names its file, not a traceback."""
        block = self.waiting()
        broken = lem_answers.answer_file(self.task.directory, criteria.row_key(self.task, block))
        broken.parent.mkdir(parents=True, exist_ok=True)
        broken.write_text("{not json", encoding="utf-8")
        self.assertIn(f"{broken} cannot be read as an answer", self.refused(criteria.cmd_change, self.task, self.file(CHANGED), NOTE))
        self.untouched()

    def test_no_criteria_md(self) -> None:
        self.waiting()
        self.task.small_file.unlink()
        self.assertIn("criteria.md is not there", self.refused(criteria.cmd_change, self.task, self.file(CHANGED), NOTE))
        self.untouched()

    def test_the_fast_track(self) -> None:
        self.waiting("## Acceptance criteria\n\nSize: small, because one cell.\n\n1. An empty note writes an empty cell.\n", criteria.FAST_WAIT)
        self.assertIn("is on the fast track", self.refused(criteria.cmd_change, self.task, self.file(CHANGED), NOTE))
        self.untouched()

    def test_criteria_that_do_not_wait_for_his_yes(self) -> None:
        self.waiting()
        self.held("lead: builder")
        self.assertIn("do not wait for the owner's yes: its newest state block is `held: lead: builder`",
                      self.refused(criteria.cmd_change, self.task, self.file(CHANGED), NOTE))
        self.untouched()

    def test_an_approval_of_the_standard_track(self) -> None:
        self.waiting()
        criteria.cmd_approve(self.task, str(self.task.small_file), "owner")
        self.held(criteria.CRITERIA_WAIT + ": the lead doubts criterion 2")
        said = self.refused(criteria.cmd_change, self.task, self.file(CHANGED), NOTE)
        self.assertIn("has approval 1 of its criteria on the standard track (by owner)", said)
        self.assertIn("`lem decisions criterion invoice-export-empty-cells --changed N --was TEXT --now TEXT`", said)
        self.untouched()

    def test_a_grown_task_keeps_its_small_approval_and_takes_the_change(self) -> None:
        """Logged decision 4: a task that grew from the fast track is on the standard track, and its `--small` approval refuses nothing."""
        self.task.small_file.write_text("## Acceptance criteria\n\nSize: small, because one cell.\n\n1. An empty note writes an empty cell.\n", encoding="utf-8")
        self.held("small change: one builder")
        criteria.cmd_approve(self.task, str(self.task.small_file), "lem")
        self.held("the criteria wait for the owner: the small change is a full change")
        self.waiting()
        self.assertEqual(len(criteria.cmd_change(self.task, self.file(CHANGED), NOTE)["pairs"]), 1)


class OneLock(Folder):
    """Talk question 1: the change and his yes take the task's criteria.lock, so of the two that come at one
    time one ends before the other starts."""

    def test_his_yes_first_refuses_the_change(self) -> None:
        self.waiting()
        criteria.cmd_approve(self.task, str(self.task.small_file), "owner", shown=criteria.shown_digest(CRITERIA.encode()))
        said = self.refused(criteria.cmd_change, self.task, self.file(CHANGED), NOTE)
        self.assertIn("approval 1 of invoice-export-empty-cells's criteria (by owner", said)
        self.assertIn("came after the wait the owner answered", said)
        self.assertEqual(self.task.small_file.read_text(encoding="utf-8"), CRITERIA)

    def test_the_change_first_refuses_a_yes_to_the_text_before_it(self) -> None:
        self.waiting()
        before = criteria.shown_digest(CRITERIA.encode())
        criteria.cmd_change(self.task, self.file(CHANGED), NOTE)
        said = self.refused(criteria.cmd_approve, self.task, str(self.task.small_file), "owner", False, before)
        self.assertIn("changed since the page showed them", said)
        self.assertFalse(self.task.approved_file.exists())

    def test_the_yes_reads_its_file_under_the_lock(self) -> None:
        """A yes that waits for the lock while a change holds it reads the file after the change, and
        refuses the bytes its page showed before."""
        self.waiting()
        before = criteria.shown_digest(CRITERIA.encode())
        lock = (self.task.directory / "criteria.lock").open("w")
        criteria.fcntl.flock(lock, criteria.fcntl.LOCK_EX)
        result: dict = {}

        def yes() -> None:
            try:
                result["ok"] = criteria.cmd_approve(self.task, str(self.task.small_file), "owner", shown=before)
            except criteria.CriteriaError as error:
                result["refused"] = str(error)

        thread = threading.Thread(target=yes)
        thread.start()
        # time for the yes to reach the lock; on a loaded machine it may come later, and then it reads the
        # changed file whatever the code does, so the wait can only make the case pass without the lock, never fail with it
        time.sleep(0.2)
        self.task.small_file.write_text(CHANGED, encoding="utf-8")
        lock.close()
        thread.join(5)
        self.assertIn("changed since the page showed them", result.get("refused", ""), result)
        self.assertFalse(self.task.approved_file.exists())


class AStopInTheMiddle(Folder):
    """Talk question 4: a change that stopped after `criteria.md` moved is ended by a run with the same file,
    against the text he answered, and its wait is written once."""

    def test_a_second_run_ends_it(self) -> None:
        block = self.waiting()
        self.stop_state = True
        with self.assertRaises(KeyboardInterrupt):
            criteria.cmd_change(self.task, self.file(CHANGED), NOTE)
        self.assertEqual(self.task.small_file.read_text(encoding="utf-8"), CHANGED)
        self.assertEqual(criteria.newest_block(self.task)["ts"], block["ts"])
        self.assertIn("stopped in the middle", self.refused(criteria.cmd_pairs, self.task))
        self.stop_state = False
        said = criteria.cmd_change(self.task, self.file(CHANGED), NOTE)
        self.assertTrue(said["resumed"])
        self.assertEqual([(p["change"], p["before"]["text"]) for p in said["pairs"]], [("changed", TWO[3:].strip())])
        self.assertEqual(json.loads((self.task.directory / "criteria-before.json").read_text(encoding="utf-8"))["text"], CRITERIA)
        self.assertEqual([e["text"] for e in self.named("task.state")], [criteria.INTERVIEW_WAIT, criteria.CHANGED_WAIT])
        self.assertEqual(criteria.cmd_pairs(self.task)["pairs"], said["pairs"])


class HisTypedNo(Folder):
    """Logged decision 9: his typed No is recorded as the answer of the criteria's row of the newest block
    before the session writes the new text, and the first answer counts."""

    def test_his_typed_no_then_a_yes_from_the_board_is_refused(self) -> None:
        block = self.waiting()
        said = criteria.cmd_typed(self.task, NOTE)
        key = lem_answers.key_of("criterion", SLUG, int(datetime.fromisoformat(block["ts"]).timestamp() * 1000))
        self.assertEqual((said["key"], said["recorded"]), (key, True))
        made = lem_answers.on_record(self.task.directory, key)
        self.assertEqual((made["option"], made["note"], made["from"], made["question"]), ("no", NOTE, "session", "Approve the criteria?"))
        # the board's Yes links its record first, and the link fails on his No (serve.py act_approve)
        won, found = lem_answers.record(self.task.directory, key, "Approve the criteria?", "yes", "", digest="d", via="door", device="phone", agent="x")
        self.assertEqual((won, found["option"]), (False, "no"))
        # and the approval the board's yes runs is refused too, with the bytes the page showed
        refused = self.refused(criteria.cmd_approve, self.task, str(self.task.small_file), "owner", False, criteria.shown_digest(CRITERIA.encode()))
        self.assertIn("the owner said No to the criteria of this wait (typed in the session", refused)
        self.assertFalse(self.task.approved_file.exists())
        # his No on record, the change goes on, and his yes to the new text counts
        changed = criteria.cmd_change(self.task, self.file(CHANGED), NOTE)
        self.assertEqual(len(changed["pairs"]), 1)
        self.assertEqual(criteria.cmd_approve(self.task, str(self.task.small_file), "owner", shown=changed["shown"])["by"], "owner")

    def test_a_board_answer_that_came_first_refuses_his_typed_no(self) -> None:
        block = self.waiting()
        key = lem_answers.key_of("criterion", SLUG, int(datetime.fromisoformat(block["ts"]).timestamp() * 1000))
        lem_answers.record(self.task.directory, key, "Approve the criteria?", "yes", "", digest="d", via="door", device="phone", agent="x")
        said = self.refused(criteria.cmd_typed, self.task, NOTE)
        self.assertIn("the owner's answer 'Yes' to this wait came first, on the board", said)
        self.assertIn("the owner's answer 'Yes' to this wait came first", self.refused(criteria.cmd_change, self.task, self.file(CHANGED), NOTE))
        self.assertEqual(self.task.small_file.read_text(encoding="utf-8"), CRITERIA)

    def test_his_typed_no_twice_is_one_record(self) -> None:
        self.waiting()
        criteria.cmd_typed(self.task, NOTE)
        again = criteria.cmd_typed(self.task, NOTE)
        self.assertEqual((again["recorded"], again["answer"]["from"]), (False, "session"))
        self.assertIn("--typed needs --words", self.refused(criteria.cmd_typed, self.task, ""))

    def test_an_approval_after_the_wait_refuses_his_typed_no(self) -> None:
        self.waiting()
        criteria.cmd_approve(self.task, str(self.task.small_file), "owner")
        self.assertIn("came after the wait the owner answered", self.refused(criteria.cmd_typed, self.task, NOTE))


class HisYesToTheChange(Folder):
    """Criterion 6: his yes to the changed text is his approval (`by: owner`) of that text."""

    def test_his_yes_after_the_change(self) -> None:
        self.waiting()
        changed = criteria.cmd_change(self.task, self.file(CHANGED), NOTE)
        self.assertIsNone(self.task.approved())
        record = criteria.cmd_approve(self.task, str(self.task.small_file), "owner", shown=changed["shown"])
        self.assertEqual((record["by"], record["text"], record["number"]), ("owner", CHANGED, 1))
        self.assertEqual(self.task.approved()["criteria"][1]["text"], NEW_TWO[3:].strip())


class TheWaitAsTheOthersReadIt(unittest.TestCase):
    """Criterion 5: the change's held line is a wait of the standard track's criteria that takes no read before
    his yes, as project.py and the board read it, and `lem project state` takes it as it is."""

    def test_the_lines_are_project_pys(self) -> None:
        self.assertEqual((criteria.INTERVIEW_WAIT, criteria.CRITERIA_WAIT, criteria.FAST_WAIT), (project.INTERVIEW_WAIT, project.CRITERIA_WAIT, project.FAST_WAIT))
        self.assertEqual(criteria.FAST_GREW.pattern, project.FAST_GREW.pattern)
        self.assertTrue(criteria.CHANGED_WAIT.startswith(project.CRITERIA_WAIT))

    def test_the_standard_track_and_the_criteria_need(self) -> None:
        self.assertEqual(project.track_of(f"2026-11-23T15:10Z held: {criteria.CHANGED_WAIT}\n\n2026-11-23T15:00Z held: small change: one builder\n"), "standard")
        self.assertEqual(bm.held_need(criteria.CHANGED_WAIT), {"need": "criteria", "number": None})
        project.fixed_form(criteria.CHANGED_WAIT)
        self.assertIsNone(project.type_line(criteria.CHANGED_WAIT))

    def test_the_board_asks_his_yes_at_once(self) -> None:
        def at(minute: int) -> str:
            return (START + timedelta(minutes=minute)).strftime("%Y-%m-%dT%H:%M:%SZ")
        events = [
            {"ts": at(0), "event": "task.state", "task": SLUG, "status": "held", "text": criteria.INTERVIEW_WAIT, "lines": []},
            {"ts": at(1), "event": "criteria.read", "task": SLUG, "by": "lem", "asked": 2, "answered": 2, "families": ["opus"], "silent": [], "criteria": 3, "flagged": 0, "split": False, "digest": "0" * 12},
            {"ts": at(5), "event": "criteria.changed", "task": SLUG, "words": NOTE, "block": at(0), "pairs": []},
            {"ts": at(5), "event": "task.state", "task": SLUG, "status": "held", "text": criteria.CHANGED_WAIT, "lines": []},
        ]
        [t] = bm.derive(events, [], int((START + timedelta(hours=1)).timestamp() * 1000)).tasks
        self.assertEqual((t.need["need"], t.approvable, t.turn, t.reading, t.for_owner), ("criteria", True, "asks", None, True))


if __name__ == "__main__":
    unittest.main()
