"""lem_board_model.py's rules, each called over a few events: the status and the column of a task, who
acts, what a card says, what waits for the owner and where he answers, green and its reasons, the end
of a run of the checks, the phases, and the read of the log on from where the last read stopped.

    python3 -B -m unittest discover -s tests/unit
"""

import importlib
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "lem" / "scripts"))
bm = importlib.import_module("lem_board_model")

START = datetime(2026, 11, 20, 9, 0, tzinfo=timezone.utc)
NOW = int((START + timedelta(hours=2)).timestamp() * 1000)


def ev(minute: float, event: str, task: str = "gift-note", **fields) -> dict:
    return {"ts": (START + timedelta(minutes=minute)).strftime("%Y-%m-%dT%H:%M:%SZ"), "event": event, "task": task, **fields}


def state(minute: float, status: str, text: str, *lines: str, task: str = "gift-note") -> dict:
    return ev(minute, "task.state", task, status=status, text=text, lines=list(lines))


def model(*events: dict, owner=(), seen=None):
    m = bm.derive(list(events), list(owner), NOW)
    m.seen = seen
    return m


def one(*events: dict, **kw) -> "bm.Task":
    return model(*events, **kw).tasks[0]


class Status(unittest.TestCase):
    def test_criteria_that_wait_put_the_task_in_the_owners_column_in_his_words(self):
        m = model(state(0, "held", "the interview waits for the owner"), state(5, "held", "the criteria wait for the owner"))
        t = m.tasks[0]
        self.assertEqual((t.lane, t.info["actor"]), ("you", "you"))
        self.assertEqual(bm.card_line(t, bm.LANE["you"]), "The criteria wait for you")
        rows = bm.waits_of(m)
        self.assertEqual([(w["kind"], bm.wait_say(w)["verb"]) for w in rows], [("criteria", "Approve the criteria")])
        self.assertIn("in the task’s session", bm.answer_of(t))

    def test_criteria_he_approved_with_no_lead_yet_are_lems_to_start(self):
        t = one(state(0, "held", "the criteria wait for the owner"), ev(3, "criteria.approved", by="owner", number=1))
        self.assertFalse(t.for_owner)
        self.assertEqual((t.lane, t.info["label"], t.info["actor"]), ("build", "Approved", "lem"))
        self.assertEqual(t.shown, "your yes to the criteria is on record: Lem starts its lead")
        self.assertEqual(bm.waits_of(model(state(0, "held", "the criteria wait for the owner"), ev(3, "criteria.approved", by="owner", number=1))), [])

    def test_since_is_when_the_task_entered_its_status_not_its_newest_block(self):
        t = one(state(0, "queued", "it waits"), state(10, "building", "lead: builder"), state(30, "building", "task 2 of 3"))
        self.assertEqual(t.since, bm.at(ev(10, "x")["ts"]))
        self.assertEqual(t.progress, {"n": 2, "of": 3})
        self.assertEqual(bm.card_line(t, bm.LANE["build"]), "Task 2 of 3")


class Breakers(unittest.TestCase):
    STOP = ev(20, "decision.breaker", id=1, at="2026-11-20T09:20:00Z", kind="breaker", cause="criteria", what="The gift note has no place that keeps criterion 1",
              document="breaker.md", handoff="handoff.md")
    HELD = state(20, "held", "breaker 1 waits for the owner", "The gift note has no place that keeps criterion 1: no option keeps the criteria")

    def test_a_breaker_is_one_row_until_his_help_and_its_held_block_is_not_a_second(self):
        m = model(state(0, "building", "task 2 of 3"), self.STOP, self.HELD)
        rows = bm.waits_of(m)
        self.assertEqual([(w["key"], bm.wait_say(w)["verb"]) for w in rows], [("breaker:gift-note:1", "Read the breaker of gift-note")])
        self.assertEqual((m.tasks[0].lane, bm.card_line(m.tasks[0], bm.LANE["you"])), ("you", "The build stopped, and its breaker waits for you"))
        self.assertIn("/lem park gift-note", bm.answer_of(m.tasks[0]))
        helped = model(state(0, "building", "task 2 of 3"), self.STOP, self.HELD,
                       ev(30, "decision.taken", id=2, what="Where the gift note goes", chose="A", why="his word", by="owner", breaker=1))
        t = helped.tasks[0]
        self.assertEqual((bm.waits_of(helped), t.info["label"], t.decisions[1].state, t.decisions[1].help), ([], "Helped", "helped", 2))
        self.assertEqual(bm.importance(t, t.decisions[2]), "it is your help on breaker 1")

    def test_a_parked_or_ended_task_waits_for_nobody_and_a_parked_one_stands_apart(self):
        m = model(state(0, "building", "task 2 of 3"), self.STOP, self.HELD, state(40, "parked", "the owner parked it: wait for the merchants"))
        t = m.tasks[0]
        self.assertEqual((bm.waits_of(m), t.for_owner, t.lane, [x.slug for x in m.parked]), ([], False, "parked", ["gift-note"]))
        self.assertFalse(any(t in tasks for tasks in m.lane.values()))
        self.assertEqual(bm.parked_of(t), {"since": bm.at(ev(40, "x")["ts"]), "why": "the owner parked it: wait for the merchants", "resume": "/lem resume gift-note"})
        self.assertIs(t.stopped, t.decisions[1])
        dropped = model(state(0, "building", "task 2 of 3"), self.STOP, self.HELD, state(40, "dropped", "the owner dropped it"))
        self.assertEqual((bm.waits_of(dropped), dropped.tasks[0].stopped), ([], None))


class Landing(unittest.TestCase):
    def test_a_stopped_run_of_the_checks_is_lems_wait_for_his_word_and_no_row_of_his(self):
        m = model(state(0, "landing", "the checks start"), ev(1, "gate.start", commands=2),
                  ev(4, "gate.end", result="stopped", seconds=180, say="gift-note: the checks were stopped; the landing waits for your word"))
        t = m.tasks[0]
        self.assertEqual((t.lane, t.info["actor"], t.info["label"]), ("checks", "lem", "Checks stopped"))
        self.assertEqual(bm.waits_of(m), [])
        line = bm.card_line(t, bm.LANE["checks"])
        self.assertTrue(line.startswith("The checks were stopped; the landing waits for your word."))
        self.assertIn("/lem land starts them again and /lem drop gift-note drops the task", line)

    def test_a_refused_run_says_that_a_builder_repairs_it_and_a_passed_one_says_nothing(self):
        refused = one(state(0, "landing", "the checks start"), ev(1, "gate.start", commands=2),
                      ev(2, "gate.end", result="refused", say="gift-note: the checks refused the change: a.py changed; a builder repairs it, nothing for you"))
        self.assertEqual(refused.info["label"], "Checks refused")
        self.assertEqual(bm.refused_of(refused.checks_end), "a.py changed")
        passed = one(state(0, "landing", "the checks start"), ev(1, "gate.start", commands=2), ev(2, "gate.end", result="passed"))
        self.assertIsNone(passed.checks_stop)
        self.assertEqual(passed.info["label"], "Checks and review")

    def test_a_landing_that_waits_says_what_for_until_its_next_event(self):
        waiting = one(state(0, "landing", "the checks start"), ev(1, "gate.wait", load=9.5, start=6))
        self.assertEqual(bm.card_line(waiting, bm.LANE["checks"]), "Waits for the load: 9.5, starts below 6")
        going = one(state(0, "landing", "the checks start"), ev(1, "gate.wait", load=9.5, start=6), ev(2, "gate.start", commands=2))
        self.assertEqual(bm.card_line(going, bm.LANE["checks"]), "The checks start")

    def test_a_result_on_another_tip_starts_a_new_run_of_the_checks(self):
        t = one(state(0, "landing", "the checks start"), ev(1, "gate", command="make test", exit=1, tip="aaa"),
                ev(5, "gate", command="make test", exit=0, tip="bbb"), ev(6, "gate", command="make lint", exit=0, tip="bbb"))
        self.assertEqual(([g["tip"] for g in t.gates], t.gate_bad), (["bbb", "bbb"], 0))


class Merge(unittest.TestCase):
    PR = "pull request https://github.com/acme/shop/pull/41"

    def test_a_proposal_waits_for_his_merge_with_its_number_and_green(self):
        m = model(state(0, "open", self.PR, "green"))
        t = m.tasks[0]
        self.assertEqual(bm.card_line(t, bm.LANE["you"]), "Waits for the merge: pull request #41")
        self.assertEqual(bm.wait_say(bm.waits_of(m)[0])["verb"], "Merge the pull request #41")
        self.assertEqual(bm.verdict_of(t), {"green": True, "reasons": []})
        self.assertEqual(bm.pr_of(t)["repo"], "acme/shop")

    def test_not_green_has_the_proposals_reasons(self):
        t = one(ev(0, "proposed", green=False, not_green=["a test was deleted"], tip="abc123456"), state(1, "open", self.PR))
        self.assertEqual(bm.verdict_of(t), {"green": False, "reasons": ["a test was deleted"]})

    def test_a_pull_request_the_forge_calls_conflicting_is_a_row_with_nothing_to_do(self):
        events = (ev(0, "proposed", green=True, not_green=[], tip="abc123456"), state(1, "open", self.PR),
                  ev(2, "merge.review", verdict="call", calls=True, why="Verdict: call. It is careful.", by="claude", tip="abc123456"))
        seen = {"gift-note": {"mergeable": "CONFLICTING", "head": "abc123456789"}}
        say = bm.wait_say(bm.waits_of(model(*events, seen=seen))[-1])
        self.assertEqual((say["verb"], say["actor"]), ("It conflicts with the base", "bad"))
        older = {"gift-note": {"mergeable": "CONFLICTING", "head": "fff000"}}
        self.assertEqual(bm.wait_say(bm.waits_of(model(*events, seen=older))[-1])["verb"], "Merge the pull request #41")

    def test_a_merge_review_that_calls_him_comes_before_the_merge_and_a_new_proposal_forgets_it(self):
        events = (ev(0, "proposed", green=True, not_green=[], tip="abc123456"), state(1, "open", self.PR),
                  ev(2, "merge.review", verdict="call", calls=True, why="Verdict: call. A test proves less than its criterion.", by="claude", tip="abc123456"))
        rows = bm.waits_of(model(*events))
        self.assertEqual([(w["kind"], bm.wait_say(w)["verb"]) for w in rows], [("review", "Read the merge review"), ("merge", "Merge the pull request #41")])
        self.assertEqual(bm.wait_say(rows[0])["where"], "The merge review is the first card of the task’s Overview. A test proves less than its criterion.")
        merges = model(*events[:2], ev(2, "merge.review", verdict="merge", calls=False, by="claude", tip="abc123456"))
        self.assertEqual(bm.waits_of(merges), [])
        # a new proposal forgets the review: the merge agent reads the new tip, and nothing waits for him
        again = model(*events, ev(3, "proposed", green=True, not_green=[], tip="def456789"))
        self.assertEqual(bm.waits_of(again), [])

    def test_an_open_pull_request_waits_for_him_only_when_its_merge_does(self):
        proposed = (ev(0, "proposed", green=True, not_green=[], tip="abc123456"), state(1, "open", self.PR))
        reads = model(*proposed)
        t = reads.tasks[0]
        self.assertEqual((t.merge_wait, t.for_owner, t.lane, t.info["label"], bm.waits_of(reads)), ("reads", False, "checks", "The merge agent reads it", []))
        merges = model(*proposed, ev(2, "merge.review", verdict="merge", calls=False, by="claude", tip="abc123456"))
        t = merges.tasks[0]
        self.assertEqual((t.merge_wait, t.for_owner, t.lane, t.info["label"], bm.waits_of(merges)), ("merges", False, "checks", "Lem merges it", []))
        calls = model(*proposed, ev(2, "merge.review", verdict="merge", calls=True, why="Verdict: merge. The settings say the owner merges.", by="claude", tip="abc123456"))
        self.assertEqual(([w["kind"] for w in bm.waits_of(calls)], calls.tasks[0].lane), (["review", "merge"], "you"))
        refused = model(*proposed, ev(2, "merge.review", verdict="merge", calls=False, by="claude", tip="abc123456"),
                        ev(3, "merge.refused", by="merger", via="server", said="Required status check is expected", tip="abc123456"))
        self.assertEqual(([w["kind"] for w in bm.waits_of(refused)], refused.tasks[0].for_owner), (["merge"], True))
        # a review of an older tip than the proposal is none
        older = model(*proposed, ev(2, "merge.review", verdict="merge", calls=False, by="claude", tip="fff000111"))
        self.assertEqual((older.tasks[0].merge_wait, bm.waits_of(older)), ("reads", []))
        # his own merge stays on the task's page in each case
        for m in (reads, merges, calls, refused, older):
            self.assertEqual(bm.acts_of(m.tasks[0], None), ["merge"])

    def test_an_open_task_needs_its_session_only_while_the_merge_agent_reads_it(self):
        proposed = (ev(0, "proposed", green=True, not_green=[], tip="abc123456"), state(1, "open", self.PR))
        reads = model(*proposed)
        reads.sessions = {}
        reads.now += 10 * 60_000
        self.assertEqual(bm.session_need(reads.tasks[0], reads), "gone")
        calls = model(*proposed, ev(2, "merge.review", verdict="call", calls=True, why="Verdict: call. It is careful.", by="claude", tip="abc123456"))
        calls.sessions = {}
        calls.now += 10 * 60_000
        self.assertIsNone(bm.session_need(calls.tasks[0], calls))

    def test_a_merge_github_refused_says_its_line(self):
        say = bm.wait_say(bm.waits_of(model(state(0, "open", self.PR), ev(1, "merge.refused", by="merger", said="Required status check is expected", tip="abc123456")))[0])
        self.assertEqual((say["verb"], say["actor"]), ("GitHub refused the merge", "bad"))
        self.assertIn("GitHub said: Required status check is expected.", say["where"])


class Acts(unittest.TestCase):
    """What the board offers the owner to do on a task (serve.py's acts)."""

    READ = dict(by="lem", asked=3, answered=3, families=["opus"], silent=[], criteria=2, flagged=0, split=False, digest="d")

    def test_his_yes_is_offered_for_criteria_and_for_an_interview_only_once_its_read_is_in(self):
        self.assertEqual(bm.acts_of(one(state(0, "held", "the criteria wait for the owner")), None), ["approve"])
        interview = (state(0, "held", "the interview waits for the owner"),)
        self.assertEqual(bm.acts_of(one(*interview), None), [])
        self.assertEqual(bm.acts_of(one(*interview, ev(5, "criteria.read", **self.READ)), None), ["approve"])
        approved = one(state(0, "held", "the criteria wait for the owner"), ev(3, "criteria.approved", by="owner", number=1))
        self.assertEqual(bm.acts_of(approved, None), [])

    def test_a_merge_is_offered_while_open_and_not_while_the_forge_calls_it_conflicting(self):
        events = (ev(0, "proposed", green=False, not_green=["a test was deleted"], tip="abc123456"), state(1, "open", Merge.PR))
        self.assertEqual(bm.acts_of(one(*events), None), ["merge"])
        seen = {"gift-note": {"mergeable": "CONFLICTING", "head": "abc123456789"}}
        self.assertEqual(bm.acts_of(one(*events), seen), [])
        self.assertEqual(bm.merge_says(one(*events)), {"green": False, "proposed": True, "reasons": ["a test was deleted"], "careful": False, "careful_why": ""})

    def test_a_park_is_offered_while_a_breaker_waits_and_not_once_the_task_is_parked(self):
        stop, held = Breakers.STOP, Breakers.HELD
        self.assertEqual(bm.acts_of(one(state(0, "building", "task 2 of 3"), stop, held), None), ["park"])
        self.assertEqual(bm.acts_of(one(state(0, "building", "task 2 of 3"), stop, held, state(30, "parked", "the owner parked it")), None), [])

    def test_the_activity_says_where_he_asked_from_and_no_login(self):
        said = bm.describe(ev(0, "board.act", act="merge", via=bm.VIA["door"]), model(state(0, "open", Merge.PR)))
        self.assertEqual((said["head"], said["text"]), ("You merged it from the board", "the board, through the tailnet door"))


class Sessions(unittest.TestCase):
    """When a task is stuck for want of its session (a row of "Waits for you", which the push sends), and
    when the board offers "Open a session" (plan-task-4.md section 7, item 2)."""

    @staticmethod
    def rows(m) -> list:
        return [(w["kind"], bm.wait_say(w)["verb"]) for w in bm.waits_of(m) if w["kind"] == "session"]

    def test_a_task_whose_phase_needs_an_agent_and_has_no_live_session_is_a_row_and_gets_the_button(self):
        events = (state(0, "building", "lead: builder"), ev(1, "session.open", session="S1", name="gift-note", phase="build", why="handoff"))
        m = model(*events)
        m.sessions = {"gift-note": {"live": True, "agent": False}}
        self.assertEqual(self.rows(m), [("session", "No session runs this task")])
        self.assertTrue(bm.opens_session(m.tasks[0], m))
        m.sessions = {"gift-note": {"live": True, "agent": True}}
        self.assertEqual((self.rows(m), bm.opens_session(m.tasks[0], m)), ([], False))

    def test_nothing_is_said_while_the_server_has_not_asked_or_the_session_is_young(self):
        self.assertEqual(self.rows(model(state(0, "building", "lead: builder"))), [])
        young = model(state(119, "held", "the interview waits for the owner"))
        young.sessions = {}
        self.assertEqual(self.rows(young), [])

    def test_a_task_that_waits_only_for_his_merge_has_the_button_and_no_row(self):
        m = model(state(0, "open", Merge.PR, "green"))
        m.sessions = {}
        self.assertEqual((self.rows(m), bm.opens_session(m.tasks[0], m)), ([], True))

    def test_a_merged_task_has_a_row_only_while_its_worktree_stays(self):
        m = model(state(0, "open", Merge.PR), state(10, "landed", "main: pull request https://github.com/acme/shop/pull/41 is merged"))
        m.sessions = {"gift-note": {"worktree": True}}
        self.assertEqual(self.rows(m), [("session", "No session cleans the merged task")])
        m.sessions = {}
        self.assertEqual((self.rows(m), bm.opens_session(m.tasks[0], m)), ([], False))

    def test_a_wake_nobody_took_is_a_row_of_its_own(self):
        m = model(state(0, "open", Merge.PR))
        m.sessions = {"gift-note": {"live": True, "agent": True, "unanswered": True}}
        rows = bm.waits_of(m)
        self.assertEqual([(w["key"], bm.wait_say(w)["verb"]) for w in rows if w["kind"] == "session"], [("deaf:gift-note", "Its session does not answer")])

    def test_a_parked_task_and_one_queued_behind_an_open_task_have_none(self):
        parked = model(state(0, "parked", "the owner parked it"))
        parked.sessions = {}
        queued = model(state(0, "open", Merge.PR, task="coupon"), state(1, "queued", "it starts after coupon", "after: coupon"))
        queued.sessions = {}
        self.assertEqual((self.rows(parked), self.rows(queued)), ([], []))
        self.assertFalse(bm.opens_session(queued.by_slug["gift-note"], queued))

    def test_a_demo_reads_a_session_from_the_log_alone(self):
        demo = bm.derive([state(0, "building", "lead: builder"), ev(1, "session.open", session="S1", name="gift-note")], [], NOW, meta={"demo": True})
        self.assertEqual(self.rows(demo), [])
        closed = bm.derive([state(0, "building", "lead: builder"), ev(1, "session.open", session="S1"), ev(2, "session.close", session="S1", why="owner")], [], NOW, meta={"demo": True})
        self.assertEqual(self.rows(closed), [("session", "No session runs this task")])


class Workspace(unittest.TestCase):
    def test_the_owners_newest_record_says_whether_he_is_away(self):
        away = {"ts": "2026-11-20T10:00:00Z", "event": "owner", "away": True, "words": "out"}
        back = {"ts": "2026-11-20T10:30:00Z", "event": "owner", "away": False}
        self.assertEqual(model(state(0, "queued", "x"), owner=[away]).away["words"], "out")
        self.assertIsNone(model(state(0, "queued", "x"), owner=[away, back]).away)

    def test_done_shows_the_newest_first_and_a_task_with_no_block_has_no_card(self):
        m = model(state(0, "landed", "merged", task="old-one"), state(50, "landed", "merged", task="new-one"), ev(5, "criteria.read", task="early"))
        self.assertEqual([t.slug for t in m.lane["done"]], ["new-one", "old-one"])
        self.assertNotIn("early", [t.slug for t in m.tasks])

    def test_the_phases_of_the_fast_track_and_of_the_standard_track(self):
        fast = one(state(0, "building", "small change: one builder"), state(9, "landing", "the checks start"))
        self.assertEqual((bm.phases_of(fast)["names"][0], bm.phases_of(fast)["at"]), ("Change", 1))
        standard = one(state(0, "building", "plan committed, 3 tasks"))
        self.assertEqual((bm.phases_of(standard)["names"][0], bm.phases_of(standard)["at"]), ("Criteria", 2))


class Reader(unittest.TestCase):
    def test_the_log_is_read_on_from_where_it_stopped_and_a_bad_line_is_said(self):
        with tempfile.TemporaryDirectory() as tmp:
            reader = bm.Reader(Path(tmp), Path(tmp))
            log = Path(tmp) / "events.jsonl"
            log.write_text(json.dumps(state(0, "queued", "x")) + "\n")
            reader.read_log()
            self.assertEqual((len(reader.events), reader.problems), (1, {}))
            with log.open("a") as out:
                out.write("not json\n" + json.dumps(state(1, "building", "y")) + "\n" + '{"ts": "half')
            reader.read_log()
            self.assertEqual([e["status"] for e in reader.events], ["queued", "building"])
            self.assertIn("line 2", reader.problems["events"])
            with log.open("a") as out:
                out.write(' a line"}\n')
            reader.read_log()
            self.assertIn("line 4", reader.problems["events"])


if __name__ == "__main__":
    unittest.main()


class MovedBase(unittest.TestCase):
    """An open task whose merge met a moved base is Lem's to land again, and one whose owner's merge stood
    through that landing is the server's to merge; a dropped task does not start the task queued behind it."""

    PR = "pull request https://github.com/acme/shop/pull/41"

    def test_a_base_refusal_is_no_row_and_githubs_is_his(self):
        proposed = (ev(0, "proposed", green=True, not_green=[], tip="abc123456"), state(1, "open", self.PR))
        base = model(*proposed, ev(2, "merge.refused", by="owner", via="server", **{"from": "lem"}, kind="base", said="origin/main moved after the checks ran", tip="abc123456"))
        t = base.tasks[0]
        self.assertEqual((t.merge_wait, t.for_owner, t.info["label"], bm.waits_of(base)), ("relands", False, "Lem lands it again", []))
        github = model(*proposed, ev(2, "merge.refused", by="owner", via="server", **{"from": "github"}, said="Required status check is expected", tip="abc123456"))
        self.assertEqual([w["kind"] for w in bm.waits_of(github)], ["merge"])

    def test_a_merge_of_his_that_stands_is_the_servers(self):
        again = (ev(0, "proposed", green=True, not_green=[], tip="def456789"), state(1, "open", self.PR),
                 ev(2, "merge.review", verdict="merge", calls=True, why="branch.land is owner", by="claude", tip="def456789", carried="abc123456"),
                 ev(3, "merge.stands", by="owner", tip="def456789", **{"from": "abc123456"}))
        t = one(*again)
        self.assertEqual((t.merge_wait, t.for_owner), ("merges", False))
        # a stand of an older tip is none
        older = one(*again[:3], ev(3, "merge.stands", by="owner", tip="fff000111"))
        self.assertEqual(older.merge_wait, "owner")

    def test_a_dropped_task_leaves_the_task_behind_it_queued(self):
        queued = state(1, "queued", "it starts after coupon", "after: coupon")
        for status, ended, dropped in (("landed", True, False), ("answered", True, False), ("dropped", False, True), ("open", False, False)):
            m = model(state(0, status, "it ended" if status != "open" else self.PR, task="coupon"), queued)
            t = m.by_slug["gift-note"]
            self.assertEqual((bm.after_ended(t, m), bm.after_dropped(t, m)), (ended, dropped), status)
