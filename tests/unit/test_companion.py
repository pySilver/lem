"""The rules of `lem companion`, as calls of their functions over facts written here: which need
waits, when it is answered, what `due` gives, why `open` refuses, and the copy of the talk from a
transcript. What agterm and the files show is checked in tests/lem-companion.sh.

    python3 -B -m unittest discover -s tests/unit
"""

import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "lem" / "scripts"))
companion = importlib.import_module("companion")

HELD = "2026-11-19T10:00:00Z"
# the personas' read of an interview's criteria, on record after the wait began
READ = "2026-11-19T10:25:00Z"
THERE = {"away": False, "since": None, "words": None}


def task(slug: str = "gift-note", status: str = "held", line: str | None = "the interview waits for the owner", **more) -> dict:
    """One task's facts, as `gather` reads them: an interview that waits, unless MORE says otherwise."""
    return {"slug": slug, "status": status, "track": "standard", "mode": "with-owner", "line": line, "held_at": HELD,
            "approvals": [], "reads": [], "choices": {}, "talk": True, **more}


def choice(state: str = "waits", irreversible: str | None = None, at: str = HELD) -> dict:
    return {"state": state, "irreversible": irreversible, "at": at}


def facts(*tasks: dict, events: list[dict] = (), live: set[str] = frozenset(), owner: dict = THERE, back_at: str | None = None) -> dict:
    return {"tasks": list(tasks), "owner": owner, "back_at": back_at, "companions": companion.companions_of(list(events), set(live))}


def opened(slug: str, need: str, session: str, ts: str = "2026-11-19T10:05:00Z", number: int | None = None) -> dict:
    return {"ts": ts, "event": "companion.open", "task": slug, "need": need, **({"choice": number} if number else {}), "session": session,
            "name": companion.sidebar_name(slug, need, number)}


def closed(slug: str, need: str, session: str, why: str, ts: str = "2026-11-19T10:20:00Z", number: int | None = None) -> dict:
    return {"ts": ts, "event": "companion.close", "task": slug, "need": need, **({"choice": number} if number else {}), "session": session, "why": why}


def names(found: list[dict]) -> list[str]:
    return [item["name"] for item in found]


class WhichNeedWaits(unittest.TestCase):
    """One rule for every reader: the newest block's line names the need."""

    def test_the_lines_of_a_held_block(self):
        self.assertEqual(companion.held_need("the interview waits for the owner"), ("interview", None))
        # the fast track's builder found a full change: its interview, not his yes to criteria nobody wrote
        self.assertEqual(companion.held_need("the criteria wait for the owner: the small change is a full change"), ("interview", None))
        self.assertEqual(companion.held_need("the criteria wait for the owner: somebody else wrote the request"), ("criteria", None))
        self.assertEqual(companion.held_need("choice 2 waits for the owner"), ("choice", 2))
        self.assertIsNone(companion.held_need("the reviewer's pane waits for the owner's trust of the folder"))

    def test_the_sidebar_names(self):
        self.assertEqual(companion.sidebar_name("gift-note", "interview", None), "gift-note · interview")
        self.assertEqual(companion.sidebar_name("gift-note", "choice", 2), "gift-note · choice 2")


class Due(unittest.TestCase):
    def test_an_approval_with_the_held_block_still_newest_gives_start_and_no_open(self):
        approved = task(approvals=[{"at": "2026-11-19T10:30:00Z", "by": "owner"}], reads=[READ])
        found = companion.due(facts(approved))
        self.assertEqual(names(found["start"]), ["gift-note · interview"])
        self.assertEqual(found["open"], [])

    def test_a_yes_before_the_read_is_in_starts_no_lead_and_keeps_the_companion(self):
        # he typed yes while the personas still read: the read may flag a criterion he has not seen
        early = task(approvals=[{"at": "2026-11-19T10:20:00Z", "by": "owner"}])
        events = [opened("gift-note", "interview", "S-1")]
        found = companion.due(facts(early, events=events, live={"S-1"}))
        self.assertEqual((found["start"], found["close"]), ([], []))
        self.assertIsNone(companion.refusal(early, "interview", None, facts(early, events=events, live={"S-1"}), asked=False))
        # the read came in after his yes: it still waits for a yes after the read
        self.assertEqual(companion.due(facts(task(approvals=early["approvals"], reads=[READ]), events=events, live={"S-1"}))["start"], [])
        # a read from before the wait began is no read of these criteria
        self.assertEqual(companion.due(facts(task(approvals=[{"at": "2026-11-19T10:30:00Z", "by": "owner"}], reads=["2026-11-19T09:00:00Z"])))["start"], [])

    def test_a_yes_after_the_read_or_after_his_word_to_skip_it_starts_the_lead(self):
        after_read = task(approvals=[{"at": "2026-11-19T10:20:00Z", "by": "owner"}, {"at": "2026-11-19T10:30:00Z", "by": "owner"}], reads=[READ])
        self.assertEqual(names(companion.due(facts(after_read))["start"]), ["gift-note · interview"])
        skip = {"ts": "2026-11-19T10:10:00Z", "event": "decision.taken", "task": "gift-note", "by": "owner", **companion.land.READ_SKIP}
        other = {"ts": "2026-11-19T10:11:00Z", "event": "decision.taken", "task": "gift-note", "by": "lead", **companion.land.READ_SKIP}
        self.assertEqual(companion.reads_of([skip, other, {"ts": READ, "event": "criteria.read", "task": "gift-note"}]), ["2026-11-19T10:10:00Z", READ])
        skipped = task(approvals=[{"at": "2026-11-19T10:12:00Z", "by": "owner"}], reads=companion.reads_of([skip]))
        self.assertEqual(names(companion.due(facts(skipped))["start"]), ["gift-note · interview"])

    def test_criteria_that_wait_for_his_yes_were_read_before_the_wait(self):
        # the lead ran the read and then stopped: his yes after the block answers it
        criteria = task(line="the criteria wait for the owner: somebody else wrote the request", approvals=[{"at": "2026-11-19T10:30:00Z", "by": "owner"}])
        self.assertEqual(names(companion.due(facts(criteria))["start"]), ["gift-note · criteria"])

    def test_an_approval_before_the_wait_answers_nothing(self):
        # the fast track's own approval, by Lem in his name, came before the builder found a full change
        grew = task(line="the criteria wait for the owner: the small change is a full change", approvals=[{"at": "2026-11-19T09:00:00Z", "by": "lem"}])
        found = companion.due(facts(grew))
        self.assertEqual((names(found["open"]), found["start"]), (["gift-note · interview"], []))

    def test_an_answered_choice_a_lead_stopped_for_gives_start(self):
        stopped = task(line="choice 2 waits for the owner", choices={2: choice("answered", "data")})
        found = companion.due(facts(stopped))
        self.assertEqual(names(found["start"]), ["gift-note · choice 2"])
        self.assertEqual(found["open"], [])

    def test_a_dismissed_card_gives_no_open_and_asked_opens_it(self):
        building = task(status="building", line="task 2 of 3", choices={1: choice()})
        events = [opened("gift-note", "choice", "S-1", number=1), closed("gift-note", "choice", "S-1", "dismissed", number=1)]
        state = facts(building, events=events)
        self.assertEqual(companion.due(state)["open"], [])
        self.assertEqual(companion.refusal(building, "choice", 1, state, asked=False)[0], "asked")
        self.assertIsNone(companion.refusal(building, "choice", 1, state, asked=True))

    def test_a_companion_gone_from_the_tree_is_logged_and_opens_on_his_word(self):
        events = [opened("gift-note", "interview", "S-1")]
        found = companion.due(facts(task(), events=events, live=set()))
        self.assertEqual((names(found["gone"]), found["open"]), (["gift-note · interview"], []))

    def test_a_night_task_with_him_there_opens_only_its_irreversible_choice(self):
        night = task(status="building", line="task 1 of 2", mode="alone", choices={3: choice(irreversible="money"), 4: choice()})
        night_criteria = task(slug="night-criteria", line="the criteria wait for the owner: a persona doubted criterion 2", mode="alone")
        found = companion.due(facts(night, night_criteria))
        self.assertEqual(names(found["open"]), ["gift-note · choice 3"])

    def test_nothing_opens_while_he_is_away_and_each_companion_is_told_once(self):
        away = {"away": True, "since": "2026-11-19T11:00:00Z", "words": "/lem im-away"}
        events = [opened("gift-note", "interview", "S-1"), opened("report-dates", "interview", "S-2")]
        others = task(slug="report-dates")
        waiting = task(slug="third-ask")
        found = companion.due(facts(task(), others, waiting, events=events, live={"S-1", "S-2"}, owner=away))
        self.assertEqual((found["open"], sorted(names(found["away"]))), ([], ["gift-note · interview", "report-dates · interview"]))
        told = [*events, {"ts": "2026-11-19T11:01:00Z", "event": "companion.away", "task": "gift-note", "need": "interview", "session": "S-1"}]
        self.assertEqual(names(companion.due(facts(task(), others, events=told, live={"S-1", "S-2"}, owner=away))["away"]), ["report-dates · interview"])

    def test_after_he_is_back_an_irreversible_choice_he_closed_opens_again(self):
        stopped = task(line="choice 2 waits for the owner", choices={2: choice(irreversible="data")})
        events = [opened("gift-note", "choice", "S-1", number=2), closed("gift-note", "choice", "S-1", "dismissed", number=2)]
        self.assertEqual(companion.due(facts(stopped, events=events, back_at="2026-11-19T10:10:00Z"))["open"], [])
        self.assertEqual(names(companion.due(facts(stopped, events=events, back_at="2026-11-19T12:00:00Z"))["open"]), ["gift-note · choice 2"])

    def test_a_companion_whose_need_is_answered_or_dropped_is_closed(self):
        approved = task(approvals=[{"at": "2026-11-19T10:30:00Z", "by": "alone"}], reads=[READ])
        dropped = task(slug="dropped-one", status="dropped", line="the owner dropped it")
        events = [opened("gift-note", "interview", "S-1"), opened("dropped-one", "interview", "S-2")]
        found = companion.due(facts(approved, dropped, events=events, live={"S-1", "S-2"}))
        self.assertEqual([(item["name"], item["why"]) for item in found["close"]], [("gift-note · interview", "answered"), ("dropped-one · interview", "dropped")])

    def test_a_close_on_record_whose_session_still_runs_is_due_its_close_again(self):
        # `lem companion close` logged the close, and agterm's `session close` then failed
        events = [opened("gift-note", "choice", "S-1", number=1), closed("gift-note", "choice", "S-1", "dismissed", number=1)]
        building = task(status="building", line="task 2 of 3", choices={1: choice()})
        found = companion.due(facts(building, events=events, live={"S-1"}))
        self.assertEqual([(item["name"], item["why"], item["session"]) for item in found["close"]], [("gift-note · choice 1", "dismissed", "S-1")])
        self.assertEqual((found["open"], found["gone"]), ([], []))
        self.assertEqual(companion.due(facts(building, events=events, live=set()))["close"], [])

    def test_an_interview_with_no_talk_is_due_its_talk_first(self):
        found = companion.due(facts(task(talk=False)))
        self.assertEqual((found["open"], names(found["talk"])), ([], ["gift-note · interview"]))


class Approvals(unittest.TestCase):
    def test_criteria_json_holds_an_approval_whose_event_was_never_logged(self):
        # `lem criteria approve` writes criteria.json before it logs the event, and a log can fail alone
        with tempfile.TemporaryDirectory() as folder:
            record = {"by": "owner", "at": "2026-11-19T10:30:00Z", "history": [{"by": "lem", "at": "2026-11-19T09:00:00Z"}]}
            (Path(folder) / "criteria.json").write_text(json.dumps(record), encoding="utf-8")
            found = companion.approvals_of(Path(folder), [])
        self.assertEqual(sorted((item["at"], item["by"]) for item in found), [("2026-11-19T09:00:00Z", "lem"), ("2026-11-19T10:30:00Z", "owner")])
        self.assertEqual(names(companion.due(facts(task(approvals=found, reads=[READ])))["start"]), ["gift-note · interview"])


class Refusals(unittest.TestCase):
    def test_the_fast_track_an_ended_task_and_a_need_that_does_not_wait(self):
        state = facts()
        self.assertEqual(companion.refusal(task(track="fast"), "interview", None, state, False)[0], "fast")
        self.assertEqual(companion.refusal(task(status="landed", line="main 1..2"), "interview", None, state, False)[0], "ended")
        self.assertEqual(companion.refusal(task(), "criteria", None, state, False)[0], "none")
        approved = task(approvals=[{"at": "2026-11-19T10:30:00Z", "by": "owner"}], reads=[READ])
        self.assertEqual(companion.refusal(approved, "interview", None, state, False)[0], "answered")


def transcript(folder: Path, *records: dict) -> Path:
    path = folder / "session.jsonl"
    path.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")
    return path


def typed(text: str, at: str) -> dict:
    return {"type": "user", "origin": {"kind": "human"}, "promptSource": "typed", "timestamp": at, "message": {"role": "user", "content": text}}


def said(text: str, at: str) -> dict:
    return {"type": "assistant", "timestamp": at, "message": {"role": "assistant", "content": [{"type": "text", "text": text}]}}


class Talk(unittest.TestCase):
    """A transcript written by hand, in the shapes Claude Code writes: what the owner typed, a `/lem`
    line, the skill's text it loads, a tool's call and result, a task's notification with agterm's
    mail in it, a peer's message, a compaction, and Lem's words."""

    RECORDS = (
        typed("Lets talk about the export first.", "2026-11-19T09:00:00Z"),
        said("The export writes one cell for the note.", "2026-11-19T09:00:05Z"),
        {"type": "system", "subtype": "compact_boundary", "timestamp": "2026-11-19T09:10:00Z"},
        {"type": "user", "isCompactSummary": True, "timestamp": "2026-11-19T09:10:01Z", "message": {"content": "This session is being continued from an earlier one."}},
        typed("Lets talk about the gift note in the export.", "2026-11-19T09:20:00Z"),
        said("Each order has one note today.", "2026-11-19T09:20:04Z"),
        {"type": "assistant", "timestamp": "2026-11-19T09:20:05Z", "message": {"content": [{"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": "ls"}}]}},
        {"type": "user", "timestamp": "2026-11-19T09:20:06Z", "message": {"content": [{"type": "tool_result", "tool_use_id": "t1", "content": "a b"}]}},
        said("Two notes would need two cells.", "2026-11-19T09:20:07Z"),
        {"type": "user", "origin": {"kind": "task-notification"}, "promptSource": "system", "timestamp": "2026-11-19T09:25:00Z",
         "message": {"content": "<task-notification>chat received</task-notification>\n[agterm mailbox, not a peer chat message] lem: other-task is ready"}},
        said("other-task is ready for its landing.", "2026-11-19T09:25:02Z"),
        {"type": "user", "origin": {"kind": "peer"}, "promptSource": "system", "isMeta": True, "timestamp": "2026-11-19T09:26:00Z", "message": {"content": "[peer chat] hello"}},
        typed("And the report dates stay whole.", "2026-11-19T09:30:00Z"),
        said("I will open a second task for the dates.", "2026-11-19T09:30:03Z"),
        {"type": "user", "origin": {"kind": "human"}, "timestamp": "2026-11-19T09:40:00Z",
         "message": {"content": "<command-message>lem:lem</command-message>\n<command-name>/lem:lem</command-name>\n<command-args>the export holds the gift note</command-args>"}},
        {"type": "user", "isMeta": True, "timestamp": "2026-11-19T09:40:00Z", "message": {"content": [{"type": "text", "text": "Base directory for this skill: /x\n\n# Lem"}]}},
        said("feat: the export holds the gift note.", "2026-11-19T09:40:09Z"),
    )

    def turns(self) -> list[dict]:
        with tempfile.TemporaryDirectory() as folder:
            return companion.transcript_turns(transcript(Path(folder), *self.RECORDS))

    def test_only_what_the_owner_typed_and_what_lem_wrote_from_before_a_compaction(self):
        found = [(turn["who"], turn["text"]) for turn in self.turns()]
        self.assertEqual(found, [
            ("owner", "Lets talk about the export first."),
            ("lem", "The export writes one cell for the note."),
            ("owner", "Lets talk about the gift note in the export."),
            ("lem", "Each order has one note today.\n\nTwo notes would need two cells."),
            ("lem", "other-task is ready for its landing."),
            ("owner", "And the report dates stay whole."),
            ("lem", "I will open a second task for the dates."),
            ("owner", "/lem the export holds the gift note"),
            ("lem", "feat: the export holds the gift note."),
        ])

    def test_the_newer_of_two_matches_and_a_turn_left_out_with_its_answers(self):
        kept, left = companion.talk_range(self.turns(), "Lets talk about", ["And the report"])
        self.assertEqual([turn["text"][:22] for turn in kept], [
            "Lets talk about the gi", "Each order has one not", "other-task is ready fo", "/lem the export holds ", "feat: the export holds"])
        self.assertEqual(left, [{"at": "2026-11-19T09:30:00Z", "words": "And the report dates stay whole.", "lem_turns": 1}])
        page = companion.talk_text("gift-note", kept, left, Path("/x/session.jsonl"))
        self.assertIn("- the owner's turn of 2026-11-19 09:30 UTC that starts \"And the report dates stay whole.\", with 1 turn of Lem after it", page)
        self.assertIn("## The owner, 2026-11-19 09:40 UTC\n\n/lem the export holds the gift note\n", page)

    def test_a_slash_command_matches_by_its_words_too(self):
        kept, _ = companion.talk_range(self.turns(), "the export holds", [])
        self.assertEqual([turn["who"] for turn in kept], ["owner", "lem"])

    def test_no_turn_that_starts_with_the_text_is_refused(self):
        with self.assertRaises(companion.CompanionError) as caught:
            companion.talk_range(self.turns(), "Nothing like this", [])
        self.assertIn("no turn of the owner starts with 'Nothing like this'", str(caught.exception))
        with self.assertRaises(companion.CompanionError):
            companion.talk_range(self.turns(), "Lets talk about", ["Nothing like this"])

    def test_a_transcript_with_no_origin_is_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            old = transcript(Path(folder), {"type": "user", "message": {"content": "hello"}}, said("hi", "2026-11-19T09:00:00Z"))
            with self.assertRaises(companion.CompanionError) as caught:
                companion.transcript_turns(old)
        self.assertIn("names no prompt's origin", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
