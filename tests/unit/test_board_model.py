"""board_model.py's rules, each called over a few events: the status and the column
of a task, who acts, what a card says, what waits for the owner and where he answers,
green and its reasons, the end of a run of the checks, the phases, the read of the log
on from where the last read stopped, and a task whose events became one summary: its
card, its followers, its board and the read of the new log.

    python3 -B -m unittest discover -s tests/unit
"""

import json
import os
import re
import sys
import tempfile
import threading
import unittest
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import IO, Any, Never, cast
from unittest import mock

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from lem import board_model as bm
from lem import board_pages as pages
from lem import board_task as task_pages
from lem import land
from lem.markup import join

START = datetime(2026, 11, 20, 9, 0, tzinfo=UTC)
NOW = int((START + timedelta(hours=2)).timestamp() * 1000)


def ev(minute: float, event: str, task: str = "gift-note", **fields: object) -> dict:
    return {
        "ts": (START + timedelta(minutes=minute)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event": event,
        "task": task,
        **fields,
    }


def bkey(number: int = 1, minute: float = 20, task: str = "gift-note") -> str:
    """The key of the row of breaker NUMBER, whose held block came MINUTE minutes after
    START (`answer_row`)."""
    return f"breaker:{task}:{number}:" + (START + timedelta(minutes=minute)).strftime(
        "%Y%m%dT%H%M%SZ"
    )


def state(
    minute: float, status: str, text: str, *lines: str, task: str = "gift-note"
) -> dict:
    return ev(minute, "task.state", task, status=status, text=text, lines=list(lines))


def model(
    *events: dict, owner: Iterable[dict] = (), seen: dict | None = None
) -> "bm.Model":
    m = bm.derive(list(events), list(owner), NOW)
    m.seen = seen
    return m


def one(
    *events: dict, owner: Iterable[dict] = (), seen: dict | None = None
) -> "bm.Task":
    return model(*events, owner=owner, seen=seen).tasks[0]


class Status(unittest.TestCase):
    def test_criteria_that_wait_put_the_task_in_the_owners_column_in_his_words(
        self,
    ) -> None:
        m = model(
            state(0, "held", "the interview waits for the owner"),
            state(5, "held", "the criteria wait for the owner"),
        )
        t = m.tasks[0]
        self.assertEqual((t.lane, t.info["actor"]), ("you", "you"))
        self.assertEqual(bm.card_line(t, bm.LANE["you"]), "The criteria wait for you")
        rows = bm.waits_of(m)
        self.assertEqual(
            [(w["kind"], bm.wait_say(w)["verb"]) for w in rows],
            [("criteria", "Approve the criteria")],
        )
        self.assertIn("in the task’s session", bm.answer_of(t))

    def test_criteria_he_approved_with_no_lead_yet_are_lems_to_start(self) -> None:
        t = one(
            state(0, "held", "the criteria wait for the owner"),
            ev(3, "criteria.approved", by="owner", number=1),
        )
        self.assertFalse(t.for_owner)
        self.assertEqual(
            (t.lane, t.info["label"], t.info["actor"]), ("build", "Approved", "lem")
        )
        self.assertEqual(
            t.shown,
            (
                "your yes to the criteria is on record: "
                "the task's session starts its build"
            ),
        )
        self.assertEqual(
            bm.waits_of(
                model(
                    state(0, "held", "the criteria wait for the owner"),
                    ev(3, "criteria.approved", by="owner", number=1),
                )
            ),
            [],
        )

    def test_since_is_when_the_task_entered_its_status_not_its_newest_block(
        self,
    ) -> None:
        t = one(
            state(0, "queued", "it waits"),
            state(10, "building", "lead: builder"),
            state(30, "building", "task 2 of 3"),
        )
        self.assertEqual(t.since, bm.at(ev(10, "x")["ts"]))
        self.assertEqual(t.progress, {"n": 2, "of": 3})
        self.assertEqual(bm.card_line(t, bm.LANE["build"]), "Task 2 of 3")


class Breakers(unittest.TestCase):
    STOP = ev(
        20,
        "decision.breaker",
        id=1,
        at="2026-11-20T09:20:00Z",
        kind="breaker",
        cause="criteria",
        what="The gift note has no place that keeps criterion 1",
        document="breaker.md",
        handoff="handoff.md",
    )
    HELD = state(
        20,
        "held",
        "breaker 1 waits for the owner",
        (
            "The gift note has no place that keeps criterion 1: "
            "no option keeps the criteria"
        ),
    )

    def test_a_breaker_is_one_row_until_his_help_and_its_held_block_is_not_a_second(
        self,
    ) -> None:
        m = model(state(0, "building", "task 2 of 3"), self.STOP, self.HELD)
        rows = bm.waits_of(m)
        self.assertEqual(
            [(w["key"], bm.wait_say(w)["verb"]) for w in rows],
            [(bkey(), "Read the breaker of gift-note")],
        )
        self.assertEqual(
            (m.tasks[0].lane, bm.card_line(m.tasks[0], bm.LANE["you"])),
            ("you", "The build stopped, and its breaker waits for you"),
        )
        self.assertIn("/lem park gift-note", bm.answer_of(m.tasks[0]))
        helped = model(
            state(0, "building", "task 2 of 3"),
            self.STOP,
            self.HELD,
            ev(
                30,
                "decision.taken",
                id=2,
                what="Where the gift note goes",
                chose="A",
                why="his word",
                by="owner",
                breaker=1,
            ),
        )
        t = helped.tasks[0]
        self.assertEqual(
            (
                bm.waits_of(helped),
                t.info["label"],
                t.decisions[1].state,
                t.decisions[1].help,
            ),
            ([], "Helped", "helped", 2),
        )
        self.assertEqual(
            bm.importance(t, t.decisions[2]), "it is your help on breaker 1"
        )

    def test_a_parked_or_ended_task_waits_for_nobody_and_a_parked_one_stands_apart(
        self,
    ) -> None:
        m = model(
            state(0, "building", "task 2 of 3"),
            self.STOP,
            self.HELD,
            state(40, "parked", "the owner parked it: wait for the merchants"),
        )
        t = m.tasks[0]
        self.assertEqual(
            (bm.waits_of(m), t.for_owner, t.lane, [x.slug for x in m.parked]),
            ([], False, "parked", ["gift-note"]),
        )
        self.assertFalse(any(t in tasks for tasks in m.lane.values()))
        self.assertEqual(
            bm.parked_of(t),
            {
                "since": bm.at(ev(40, "x")["ts"]),
                "why": "the owner parked it: wait for the merchants",
                "resume": "/lem resume gift-note",
            },
        )
        self.assertIs(t.stopped, t.decisions[1])
        dropped = model(
            state(0, "building", "task 2 of 3"),
            self.STOP,
            self.HELD,
            state(40, "dropped", "the owner dropped it"),
        )
        self.assertEqual((bm.waits_of(dropped), dropped.tasks[0].stopped), ([], None))


class Landing(unittest.TestCase):
    def test_a_stopped_run_of_the_checks_is_lems_wait_for_his_word_and_no_row_of_his(
        self,
    ) -> None:
        m = model(
            state(0, "landing", "the checks start"),
            ev(1, "gate.start", commands=2),
            ev(
                4,
                "gate.end",
                result="stopped",
                seconds=180,
                say=(
                    "gift-note: the checks were stopped; "
                    "the landing waits for your word"
                ),
            ),
        )
        t = m.tasks[0]
        self.assertEqual(
            (t.lane, t.info["actor"], t.info["label"]),
            ("checks", "lem", "Checks stopped"),
        )
        self.assertEqual(bm.waits_of(m), [])
        line = bm.card_line(t, bm.LANE["checks"])
        self.assertTrue(
            line.startswith("The checks were stopped; the landing waits for your word.")
        )
        self.assertIn(
            "/lem land starts them again and /lem drop gift-note drops the task", line
        )

    def test_a_refused_run_says_that_a_builder_repairs_it_and_a_passed_one_says_nothing(
        self,
    ) -> None:
        refused = one(
            state(0, "landing", "the checks start"),
            ev(1, "gate.start", commands=2),
            ev(
                2,
                "gate.end",
                result="refused",
                say=(
                    "gift-note: the checks refused the change: a.py changed; "
                    "a builder repairs it, nothing for you"
                ),
            ),
        )
        self.assertEqual(refused.info["label"], "Checks refused")
        self.assertEqual(
            bm.refused_of(cast("dict", refused.checks_end)),
            "a.py changed",
        )
        passed = one(
            state(0, "landing", "the checks start"),
            ev(1, "gate.start", commands=2),
            ev(2, "gate.end", result="passed"),
        )
        self.assertIsNone(passed.checks_stop)
        self.assertEqual(passed.info["label"], "Checks and review")

    def test_a_landing_that_waits_says_what_for_until_its_next_event(self) -> None:
        waiting = one(
            state(0, "landing", "the checks start"),
            ev(1, "gate.wait", load=9.5, start=6),
        )
        self.assertEqual(
            bm.card_line(waiting, bm.LANE["checks"]),
            "Waits for the load: 9.5, starts below 6",
        )
        going = one(
            state(0, "landing", "the checks start"),
            ev(1, "gate.wait", load=9.5, start=6),
            ev(2, "gate.start", commands=2),
        )
        self.assertEqual(
            (bm.card_line(going, bm.LANE["checks"]), bm.now_head(going)),
            ("The checks run", "The checks run"),
        )

    def test_criterion_1_a_landing_card_says_the_step_that_runs_as_its_page_does(
        self,
    ) -> None:
        t = one(
            state(0, "landing", "the checks start"),
            ev(1, "builder.start", job="the repair of a conflict with the base"),
            ev(12, "builder.end"),
            ev(13, "polish.start", before="1a2b3c4d5"),
        )
        self.assertEqual(bm.now_head(t), "The polish pass runs")
        self.assertEqual(bm.card_line(t, bm.LANE["checks"]), "The polish pass runs")
        builder = one(
            state(0, "landing", "the checks start"),
            ev(1, "builder.start", job="the repair of a conflict with the base"),
        )
        self.assertEqual(bm.card_line(builder, bm.LANE["checks"]), bm.now_head(builder))
        # a step that ended leaves the state's own words, and so does a status other
        # than landing
        ended = one(
            state(0, "landing", "the checks start"),
            ev(1, "polish.start", before="1a2b3c4d5"),
            ev(9, "polish", before="1a2b3c4d5", after="2b3c4d5e6"),
        )
        self.assertEqual(bm.card_line(ended, bm.LANE["checks"]), "The checks start")
        building = one(
            state(0, "building", "task 2 of 3"), ev(1, "builder.start", job="task 2")
        )
        self.assertEqual(bm.card_line(building, bm.LANE["build"]), "Task 2 of 3")

    def test_a_landing_that_waits_with_no_task_ahead_keeps_its_load_and_after_words(
        self,
    ) -> None:
        after = one(
            state(0, "landing", "the checks start"),
            ev(1, "gate.wait", load=3.0, start=6, after="keys-help"),
        )
        self.assertEqual(
            bm.card_line(after, bm.LANE["checks"]),
            "Its checks wait a minute after the checks of keys-help started",
        )
        self.assertEqual(
            bm.SAYS["gate.wait"](after.events[-1])["text"],
            "a minute after the checks of keys-help started",
        )
        load = one(
            state(0, "landing", "the checks start"),
            ev(1, "gate.wait", load=9.5, start=6),
        )
        self.assertEqual(
            bm.SAYS["gate.wait"](load.events[-1])["text"],
            "for the load: 9.5, they start below 6",
        )

    def test_a_result_on_another_tip_starts_a_new_run_of_the_checks(self) -> None:
        t = one(
            state(0, "landing", "the checks start"),
            ev(1, "gate", command="make test", exit=1, tip="aaa"),
            ev(5, "gate", command="make test", exit=0, tip="bbb"),
            ev(6, "gate", command="make lint", exit=0, tip="bbb"),
        )
        self.assertEqual(([g["tip"] for g in t.gates], t.gate_bad), (["bbb", "bbb"], 0))


class WaitsBehind(unittest.TestCase):
    """The machine's one line of the landings that wait (land.py, `wait_for_load`): a
    run that is not first logs `gate.wait` with `behind`, `why` and, for a first of
    another repository, `behind_repo`; the card, the large card's head, what the task
    waits for and the feed say which landing it waits behind and why."""

    SLUG = "plugin-dir-for-the-plan-talk"
    FIRST = "fast-track-checks-documents"

    def waiting(self, **fields: object) -> "bm.Task":
        return one(
            state(0, "landing", "the checks start", task=self.SLUG),
            ev(1, "gate.wait", self.SLUG, load=50.0, start=40, **fields),
        )

    def test_criterion_7_a_landing_behind_one_that_waits_longer_says_so_on_the_card_and_in_the_feed(
        self,
    ) -> None:
        t = self.waiting(behind=self.FIRST, why="longer")
        said = "Its checks wait behind fast-track-checks-documents, which waits longer"
        self.assertEqual(bm.card_line(t, bm.LANE["checks"]), said)
        self.assertEqual(bm.now_head(t), said)
        self.assertEqual(cast("dict", bm.waits_for(t, []))["text"], said)
        self.assertEqual(
            bm.SAYS["gate.wait"](t.events[-1]),
            {
                "info": {"actor": "quiet", "icon": "clock"},
                "head": "The checks wait",
                "text": "behind fast-track-checks-documents, which waits longer",
            },
        )
        # the first itself waits for the load, in today's words
        first = one(
            state(0, "landing", "the checks start", task=self.FIRST),
            ev(1, "gate.wait", self.FIRST, load=50.0, start=40),
        )
        self.assertEqual(
            bm.card_line(first, bm.LANE["checks"]),
            "Waits for the load: 50.0, starts below 40",
        )

    def test_each_why_has_its_words(self) -> None:
        for why, said in (
            ("wanted", "which another task waits for"),
            ("longer", "which waits longer"),
            ("first", "which is first in the line"),
        ):
            with self.subTest(why=why):
                t = self.waiting(behind="fix-red-base", why=why)
                self.assertEqual(
                    bm.card_line(t, bm.LANE["checks"]),
                    f"Its checks wait behind fix-red-base, {said}",
                )
                self.assertEqual(
                    bm.SAYS["gate.wait"](t.events[-1])["text"],
                    f"behind fix-red-base, {said}",
                )

    def test_a_first_of_another_repository_is_named_with_its_folder(self) -> None:
        t = self.waiting(
            behind="new-sessions-open-at-tail",
            behind_repo="/Users/someone/Projects/mybaze",
            why="wanted",
        )
        self.assertEqual(
            bm.card_line(t, bm.LANE["checks"]),
            (
                "Its checks wait behind new-sessions-open-at-tail of mybaze, which "
                "another task waits for"
            ),
        )
        self.assertEqual(
            bm.SAYS["gate.wait"](t.events[-1])["text"],
            "behind new-sessions-open-at-tail of mybaze, which another task waits for",
        )

    def test_behind_goes_before_a_minute_after_the_last_start(self) -> None:
        t = self.waiting(behind=self.FIRST, why="longer", after="keys-help")
        self.assertEqual(
            bm.card_line(t, bm.LANE["checks"]),
            "Its checks wait behind fast-track-checks-documents, which waits longer",
        )

    def test_a_stop_while_it_waited_ends_the_wait_and_reads_as_the_stopped_checks_with_no_count(
        self,
    ) -> None:
        t = one(
            state(0, "landing", "the checks start", task=self.SLUG),
            ev(
                1,
                "gate.wait",
                self.SLUG,
                load=50.0,
                start=40,
                behind=self.FIRST,
                why="longer",
            ),
            ev(
                5,
                "gate.end",
                self.SLUG,
                result="stopped",
                seconds=0,
                tip="abc123456",
                say=(
                    f"{self.SLUG}: the checks were stopped; "
                    "the landing waits for your word"
                ),
            ),
        )
        self.assertIsNone(bm.waits_now(t))
        self.assertEqual(t.info["label"], "Checks stopped")
        self.assertTrue(
            bm.card_line(t, bm.LANE["checks"]).startswith(
                "The checks were stopped; the landing waits for your word."
            )
        )
        self.assertEqual(
            bm.SAYS["gate.end"](t.events[-1])["head"], "The checks were stopped"
        )
        tm = bm.time_of(t, bm.time_end(t, NOW), {"gates": 2, "serial": 0})
        ends = [(s["head"], s["sub"]) for s in tm["spans"] if s["row"] == "checks"]
        self.assertEqual(
            ends,
            [
                (
                    "The checks were stopped",
                    "stopped while they waited, before their first command",
                )
            ],
        )

    def test_a_run_stopped_after_its_start_keeps_its_count_of_commands(self) -> None:
        t = one(
            state(0, "landing", "the checks start"),
            ev(1, "gate.start", commands=2, tip="abc123456"),
            ev(2, "gate", command="make test", exit=0, last="ok", tip="abc123456"),
            ev(
                4,
                "gate.end",
                result="stopped",
                seconds=180,
                tip="abc123456",
                say=(
                    "gift-note: the checks were stopped; "
                    "the landing waits for your word"
                ),
            ),
        )
        tm = bm.time_of(t, bm.time_end(t, NOW), {"gates": 2, "serial": 0})
        self.assertIn(
            ("The checks were stopped", "1 of 2 commands done · 3m 00s"),
            [(s["head"], s["sub"]) for s in tm["spans"] if s["row"] == "checks"],
        )


class TakenFromPolish(unittest.TestCase):
    """A run of the checks that took the polish pass's result of the criteria's tests
    logs no `task.red`: its `gate.end` names the pass's commit (`taken`), and the board
    says so where it would draw the tests."""

    TIP = "a1b2c3d4e"

    def landing(self, *after: dict, commits: int = 1) -> "bm.Task":
        return one(
            state(0, "landing", "the polish pass"),
            ev(1, "polish.start", before="0f0f0f0f0"),
            ev(
                10,
                "polish",
                before="0f0f0f0f0",
                after=self.TIP,
                commits=commits,
                filed=[],
            ),
            ev(11, "gate.start", tip=self.TIP, commands=2),
            ev(13, "gate", command="make test", exit=0, last="ok", tip=self.TIP),
            ev(15, "gate", command="make lint", exit=0, last="ok", tip=self.TIP),
            *after,
        )

    @staticmethod
    def checks(t: "bm.Task", end: int | None = None) -> list[tuple]:
        tm = bm.time_of(
            t,
            end if end is not None else bm.time_end(t, NOW),
            {"gates": 2, "serial": 0},
        )
        return [
            (g["head"], g["sub"], g["live"])
            for g in tm["spans"]
            if g["row"] == "checks"
        ]

    def test_a_taken_result_is_the_span_of_the_criterias_tests_with_the_pass_and_its_commit(
        self,
    ) -> None:
        t = self.landing(
            ev(
                16,
                "gate.end",
                result="passed",
                seconds=300,
                tip=self.TIP,
                taken=self.TIP,
                say="gift-note: the checks passed; the review runs, nothing for you",
            )
        )
        heads = [x[0] for x in self.checks(t)]
        self.assertIn(
            f"The tests of the criteria, taken from the polish pass at {self.TIP}",
            heads,
        )
        self.assertNotIn(
            "The tests of the criteria, on the branch and on the base commit", heads
        )
        # the feed says it too, under the run's end
        self.assertIn(
            (
                f"the tests of the criteria taken from the polish pass at {self.TIP}, "
                "not run again"
            ),
            cast("str", bm.SAYS["gate.end"](t.events[-1])["sub"]),
        )

    def test_a_run_of_the_tests_says_nothing_of_the_polish_pass(self) -> None:
        t = self.landing(
            ev(
                18,
                "task.red",
                ok=True,
                digest="d",
                base="b0b0b0b0b",
                tip=self.TIP,
                tests=[],
                without_a_test=[],
            ),
            ev(
                19,
                "gate.end",
                result="passed",
                seconds=480,
                tip=self.TIP,
                say="gift-note: the checks passed; the review runs, nothing for you",
            ),
        )
        heads = [x[0] for x in self.checks(t)]
        self.assertIn(
            "The tests of the criteria, on the branch and on the base commit", heads
        )
        self.assertFalse(any("polish pass" in x for x in heads))
        self.assertNotIn(
            "polish pass", cast("str", bm.SAYS["gate.end"](t.events[-1])["sub"])
        )

    def test_after_the_last_command_on_the_passs_commit_the_live_line_does_not_say_that_the_tests_run(
        self,
    ) -> None:
        live = [x for x in self.checks(self.landing()) if x[2]]
        self.assertEqual(len(live), 1)
        self.assertNotEqual(live[0][0], "The tests of the criteria run")
        self.assertIn(f"the polish pass's result at {self.TIP} is taken", live[0][0])

    def test_after_a_pass_with_no_commits_the_tests_run(self) -> None:
        live = [x for x in self.checks(self.landing(commits=0)) if x[2]]
        self.assertEqual([x[0] for x in live], ["The tests of the criteria run"])


class Merge(unittest.TestCase):
    PR = "pull request https://github.com/acme/shop/pull/41"

    def test_a_proposal_waits_for_his_merge_with_its_number_and_green(self) -> None:
        m = model(state(0, "open", self.PR, "green"))
        t = m.tasks[0]
        self.assertEqual(
            bm.card_line(t, bm.LANE["you"]), "Waits for the merge: pull request #41"
        )
        self.assertEqual(
            bm.wait_say(bm.waits_of(m)[0])["verb"], "Merge the pull request #41"
        )
        self.assertEqual(bm.verdict_of(t), {"green": True, "reasons": []})
        self.assertEqual(cast("dict", bm.pr_of(t))["repo"], "acme/shop")

    def test_not_green_has_the_proposals_reasons(self) -> None:
        t = one(
            ev(
                0,
                "proposed",
                green=False,
                not_green=["a test was deleted"],
                tip="abc123456",
            ),
            state(1, "open", self.PR),
        )
        self.assertEqual(
            bm.verdict_of(t), {"green": False, "reasons": ["a test was deleted"]}
        )

    def test_a_pull_request_the_forge_calls_conflicting_is_a_row_with_nothing_to_do(
        self,
    ) -> None:
        events = (
            ev(0, "proposed", green=True, not_green=[], tip="abc123456"),
            state(1, "open", self.PR),
            ev(
                2,
                "merge.review",
                verdict="call",
                calls=True,
                why="Verdict: call. It is careful.",
                by="claude",
                tip="abc123456",
            ),
        )
        seen = {"gift-note": {"mergeable": "CONFLICTING", "head": "abc123456789"}}
        say = bm.wait_say(bm.waits_of(model(*events, seen=seen))[-1])
        self.assertEqual(
            (say["verb"], say["actor"]), ("It conflicts with the base", "bad")
        )
        older = {"gift-note": {"mergeable": "CONFLICTING", "head": "fff000"}}
        self.assertEqual(
            bm.wait_say(bm.waits_of(model(*events, seen=older))[-1])["verb"],
            "Merge the pull request #41",
        )

    def test_a_merge_review_that_calls_him_comes_before_the_merge_and_a_new_proposal_forgets_it(
        self,
    ) -> None:
        events = (
            ev(0, "proposed", green=True, not_green=[], tip="abc123456"),
            state(1, "open", self.PR),
            ev(
                2,
                "merge.review",
                verdict="call",
                calls=True,
                why="Verdict: call. A test proves less than its criterion.",
                by="claude",
                tip="abc123456",
            ),
        )
        rows = bm.waits_of(model(*events))
        self.assertEqual(
            [(w["kind"], bm.wait_say(w)["verb"]) for w in rows],
            [
                ("review", "Read the merge review"),
                ("merge", "Merge the pull request #41"),
            ],
        )
        self.assertEqual(
            bm.wait_say(rows[0])["where"],
            (
                "The merge review is the first card of the task’s Overview. "
                "A test proves less than its criterion."
            ),
        )
        merges = model(
            *events[:2],
            ev(
                2,
                "merge.review",
                verdict="merge",
                calls=False,
                by="claude",
                tip="abc123456",
            ),
        )
        self.assertEqual(bm.waits_of(merges), [])
        # a new proposal forgets the review: the merge agent reads the new tip, and
        # nothing waits for him
        again = model(
            *events, ev(3, "proposed", green=True, not_green=[], tip="def456789")
        )
        self.assertEqual(bm.waits_of(again), [])

    def test_an_open_pull_request_waits_for_him_only_when_its_merge_does(self) -> None:
        proposed = (
            ev(0, "proposed", green=True, not_green=[], tip="abc123456"),
            state(1, "open", self.PR),
        )
        reads = model(*proposed)
        t = reads.tasks[0]
        self.assertEqual(
            (t.merge_wait, t.for_owner, t.lane, t.info["label"], bm.waits_of(reads)),
            ("reads", False, "checks", "The merge agent reads it", []),
        )
        merges = model(
            *proposed,
            ev(
                2,
                "merge.review",
                verdict="merge",
                calls=False,
                by="claude",
                tip="abc123456",
            ),
        )
        t = merges.tasks[0]
        self.assertEqual(
            (t.merge_wait, t.for_owner, t.lane, t.info["label"], bm.waits_of(merges)),
            ("merges", False, "checks", "Lem merges it", []),
        )
        calls = model(
            *proposed,
            ev(
                2,
                "merge.review",
                verdict="merge",
                calls=True,
                why="Verdict: merge. The settings say the owner merges.",
                by="claude",
                tip="abc123456",
            ),
        )
        self.assertEqual(
            ([w["kind"] for w in bm.waits_of(calls)], calls.tasks[0].lane),
            (["review", "merge"], "you"),
        )
        refused = model(
            *proposed,
            ev(
                2,
                "merge.review",
                verdict="merge",
                calls=False,
                by="claude",
                tip="abc123456",
            ),
            ev(
                3,
                "merge.refused",
                by="merger",
                via="server",
                said="Required status check is expected",
                tip="abc123456",
            ),
        )
        self.assertEqual(
            ([w["kind"] for w in bm.waits_of(refused)], refused.tasks[0].for_owner),
            (["merge"], True),
        )
        # a review of an older tip than the proposal is none
        older = model(
            *proposed,
            ev(
                2,
                "merge.review",
                verdict="merge",
                calls=False,
                by="claude",
                tip="fff000111",
            ),
        )
        self.assertEqual((older.tasks[0].merge_wait, bm.waits_of(older)), ("reads", []))
        # his own merge stays on the task's page in each case
        for m in (reads, merges, calls, refused, older):
            self.assertEqual(bm.acts_of(m.tasks[0], None), ["merge"])

    def test_an_open_task_needs_its_session_only_while_the_merge_agent_reads_it(
        self,
    ) -> None:
        proposed = (
            ev(0, "proposed", green=True, not_green=[], tip="abc123456"),
            state(1, "open", self.PR),
        )
        reads = model(*proposed)
        reads.sessions = {}
        reads.now += 10 * 60_000
        self.assertEqual(bm.session_need(reads.tasks[0], reads), "gone")
        calls = model(
            *proposed,
            ev(
                2,
                "merge.review",
                verdict="call",
                calls=True,
                why="Verdict: call. It is careful.",
                by="claude",
                tip="abc123456",
            ),
        )
        calls.sessions = {}
        calls.now += 10 * 60_000
        self.assertIsNone(bm.session_need(calls.tasks[0], calls))

    def test_a_merge_github_refused_says_its_line(self) -> None:
        say = bm.wait_say(
            bm.waits_of(
                model(
                    state(0, "open", self.PR),
                    ev(
                        1,
                        "merge.refused",
                        by="merger",
                        said="Required status check is expected",
                        tip="abc123456",
                    ),
                )
            )[0]
        )
        self.assertEqual(
            (say["verb"], say["actor"]), ("GitHub refused the merge", "bad")
        )
        self.assertIn("GitHub said: Required status check is expected.", say["where"])

    def test_the_timeline_says_whose_merge_lem_refused(self) -> None:
        # merge-button-after-failed-merge, 2026-11-22: right after his own press, the
        # owner read that the merge agent's merge was refused
        def head(**fields: object) -> str:
            refused = ev(
                2,
                "merge.refused",
                via="server",
                said="origin/main moved after the checks ran",
                tip="abc123456",
            )
            return cast("str", bm.SAYS["merge.refused"]({**refused, **fields})["head"])

        self.assertEqual(
            (
                head(by="owner", kind="base", **{"from": "lem"}),
                head(by="merger", kind="base", **{"from": "lem"}),
                head(by="owner", **{"from": "github"}),
            ),
            (
                "Lem refused your merge",
                "Lem refused the merge agent’s merge",
                "GitHub refused the merge",
            ),
        )


class WaitStacks(unittest.TestCase):
    """The rows of "Waits for you" grouped by task (`wait_stacks`), each group in the
    place of its first row: a task whose merge review calls the owner is one group of
    its two things (criteria 1 and 3 of
    docs/plans/2026-11-23-one-row-for-a-merge-call.md)."""

    @staticmethod
    def calls(task: str, minute: float, number: int) -> tuple:
        """TASK proposed, open at MINUTE with pull request NUMBER, and its merge review
        calling the owner a minute later"""
        return (
            ev(
                minute - 1,
                "proposed",
                task,
                green=True,
                not_green=[],
                tip=f"{task[:3]}123456",
            ),
            state(
                minute,
                "open",
                f"pull request https://github.com/acme/shop/pull/{number}",
                task=task,
            ),
            ev(
                minute + 1,
                "merge.review",
                task,
                verdict="call",
                calls=True,
                why="Verdict: call. It is careful.",
                by="claude",
                tip=f"{task[:3]}123456",
            ),
        )

    @staticmethod
    def groups(m: "bm.Model") -> list:
        return [
            (s["t"].slug, [w["key"] for w in s["rows"]])
            for s in bm.wait_stacks(bm.waits_of(m))
        ]

    def test_a_task_of_two_things_is_one_group_in_the_place_of_its_first_and_another_tasks_row_after_it(
        self,
    ) -> None:
        # the merge of board-card waits since minute 5, before the merge of the logo's
        # task (minute 10), and after the logo's merge review, so that the rows are the
        # logo's, board-card's, the logo's
        m = model(
            *self.calls("logo-eyes", 10, 73),
            state(
                5,
                "open",
                "pull request https://github.com/acme/shop/pull/42",
                "green",
                task="board-card",
            ),
        )
        self.assertEqual(
            [w["key"] for w in bm.waits_of(m)],
            ["review:logo-eyes", "merge:board-card", "merge:logo-eyes"],
        )
        self.assertEqual(
            self.groups(m),
            [
                ("logo-eyes", ["review:logo-eyes", "merge:logo-eyes"]),
                ("board-card", ["merge:board-card"]),
            ],
        )
        stack = bm.wait_stacks(bm.waits_of(m))[0]
        self.assertEqual(
            [bm.wait_say(w)["verb"] for w in stack["rows"]],
            ["Read the merge review", "Merge the pull request #73"],
        )
        self.assertIs(stack["t"], m.by_slug["logo-eyes"])

    def test_a_task_of_one_thing_is_a_group_of_its_one_row(self) -> None:
        m = model(
            state(
                0,
                "held",
                "the interview waits for the owner",
                task="board-answers-a-card",
            )
        )
        self.assertEqual(
            self.groups(m), [("board-answers-a-card", ["held:board-answers-a-card"])]
        )

    def test_two_tasks_of_two_things_are_two_groups_in_the_order_of_their_first_rows(
        self,
    ) -> None:
        m = model(*self.calls("receipt", 20, 44), *self.calls("logo-eyes", 10, 73))
        self.assertEqual(
            [w["key"] for w in bm.waits_of(m)],
            ["review:logo-eyes", "review:receipt", "merge:logo-eyes", "merge:receipt"],
        )
        self.assertEqual(
            self.groups(m),
            [
                ("logo-eyes", ["review:logo-eyes", "merge:logo-eyes"]),
                ("receipt", ["review:receipt", "merge:receipt"]),
            ],
        )

    def test_nothing_waits_no_group(self) -> None:
        self.assertEqual(bm.wait_stacks([]), [])


class TopLine(unittest.TestCase):
    """The words "waits for you" of the Tasks view's top line (`summary_of`) count what
    the sidebar, the rail, the phone's icon and the switcher count: the tasks with a row
    of "Waits for you" (`wait_count`), not the tasks of the "You" column. The owner's
    answer of 2026-11-24, "Count like the sidebar"."""

    def test_a_building_task_whose_session_is_gone_waits_for_you_on_the_top_line(
        self,
    ) -> None:
        # the probe of the question: the task builds, its session closed, and "Waits for
        # you" has its one row "No session runs this task"
        m = model(
            state(0, "building", "lead: builder"), state(30, "building", "task 2 of 3")
        )
        m.sessions = {}
        self.assertEqual([w["key"] for w in bm.waits_of(m)], ["session:gift-note"])
        self.assertEqual(pages.summary_of(m), "1 waits for you, 1 builds")
        self.assertEqual((bm.wait_count(m), len(m.lane["you"])), (1, 0))

    def test_a_task_whose_merge_review_calls_you_is_one_on_the_top_line_and_in_the_sidebar(
        self,
    ) -> None:
        # the two sets were the same before: two rows, one task, in the "You" column
        m = model(*WaitStacks.calls("logo-eyes", 10, 73))
        self.assertEqual(len(bm.waits_of(m)), 2)
        self.assertEqual(pages.summary_of(m), "1 waits for you")
        self.assertEqual((bm.wait_count(m), len(m.lane["you"])), (1, 1))


class WaitingByTask(unittest.TestCase):
    """`lem project waiting` groups the things of one task under that task (`tasks`), in
    the order of the board's stacks, and counts each task once (criterion 5
    of docs/plans/2026-11-23-one-row-for-a-merge-call.md)."""

    SLUGS = ("board-answers-a-card", "logo-eyes", "board-card")

    def waiting(self, m: "bm.Model") -> dict:
        from lem import project

        tasks = [
            {
                "slug": slug,
                "ask": f"the ask of {slug}",
                "since": "2026-11-23T09:00:00Z",
                "night": None,
                "state": f"## 2026-11-23 09:00 · open\n\n{slug}'s line",
                "status": "open",
                "proposal": None,
            }
            for slug in self.SLUGS
        ]
        pending = mock.Mock(
            returncode=0, stdout=json.dumps({"waiting": [], "ended": []})
        )
        with (
            tempfile.TemporaryDirectory() as folder,
            mock.patch.object(project, "load", return_value={}),
            mock.patch.object(project, "read_tasks", return_value=tasks),
            mock.patch.object(project, "waiting_model", return_value=(m, None)),
            mock.patch.object(project.subprocess, "run", return_value=pending),
            mock.patch.object(project, "owner_records", return_value=[]),
            mock.patch.object(project, "state_root", return_value=Path(folder)),
            mock.patch.object(
                project,
                "first_line_of",
                side_effect=lambda task: f"{task['slug']}'s line",
            ),
        ):
            return project.cmd_waiting(Path("/lem-unit/repo"))

    def test_a_task_whose_merge_review_calls_the_owner_is_one_entry_of_its_two_things_and_counts_once(
        self,
    ) -> None:
        # the interview of board-answers-a-card, then the logo's merge review,
        # board-card's merge and the logo's merge
        m = model(
            state(
                0,
                "held",
                "the interview waits for the owner",
                task="board-answers-a-card",
            ),
            *WaitStacks.calls("logo-eyes", 10, 73),
            state(
                5,
                "open",
                "pull request https://github.com/acme/shop/pull/42",
                "green",
                task="board-card",
            ),
        )
        found = self.waiting(m)
        self.assertEqual(
            [r["key"] for r in found["rows"]],
            [
                "held:board-answers-a-card",
                "review:logo-eyes",
                "merge:board-card",
                "merge:logo-eyes",
            ],
        )
        self.assertEqual(
            found["tasks"],
            [
                {
                    "task": "board-answers-a-card",
                    "ask": "the ask of board-answers-a-card",
                    "since": "2026-11-23T09:00:00Z",
                    "night": None,
                    "line": "board-answers-a-card's line",
                    "things": [
                        {
                            "key": "held:board-answers-a-card",
                            "kind": "held",
                            "verb": "The interview waits for you",
                        }
                    ],
                },
                {
                    "task": "logo-eyes",
                    "ask": "the ask of logo-eyes",
                    "since": "2026-11-23T09:00:00Z",
                    "night": None,
                    "line": "logo-eyes's line",
                    "things": [
                        {
                            "key": "review:logo-eyes",
                            "kind": "review",
                            "verb": "Read the merge review",
                        },
                        {
                            "key": "merge:logo-eyes",
                            "kind": "merge",
                            "verb": "Merge the pull request #73",
                        },
                    ],
                },
                {
                    "task": "board-card",
                    "ask": "the ask of board-card",
                    "since": "2026-11-23T09:00:00Z",
                    "night": None,
                    "line": "board-card's line",
                    "things": [
                        {
                            "key": "merge:board-card",
                            "kind": "merge",
                            "verb": "Merge the pull request #42",
                        }
                    ],
                },
            ],
        )
        # three tasks wait, though four things do; the groups of each kind keep one
        # entry for each thing
        self.assertEqual(found["count"], 3)
        self.assertEqual(
            (
                [e["task"] for e in found["reviews"]],
                [e["task"] for e in found["pull_requests"]],
            ),
            (["logo-eyes"], ["board-card", "logo-eyes"]),
        )

    def test_nothing_waits_no_task_and_a_count_of_0(self) -> None:
        found = self.waiting(
            model(state(0, "building", "lead: builder", task="logo-eyes"))
        )
        self.assertEqual((found["tasks"], found["rows"], found["count"]), ([], [], 0))


class Acts(unittest.TestCase):
    """What the board offers the owner to do on a task (serve.py's acts)."""

    READ: dict[str, Any] = {
        "by": "lem",
        "asked": 3,
        "answered": 3,
        "families": ["opus"],
        "silent": [],
        "criteria": 2,
        "flagged": 0,
        "split": False,
        "digest": "d",
    }

    def test_his_yes_is_offered_for_criteria_and_for_an_interview_only_once_its_read_is_in(
        self,
    ) -> None:
        self.assertEqual(
            bm.acts_of(one(state(0, "held", "the criteria wait for the owner")), None),
            ["approve"],
        )
        interview = (state(0, "held", "the interview waits for the owner"),)
        self.assertEqual(bm.acts_of(one(*interview), None), [])
        self.assertEqual(
            bm.acts_of(one(*interview, ev(5, "criteria.read", **self.READ)), None),
            ["approve"],
        )
        approved = one(
            state(0, "held", "the criteria wait for the owner"),
            ev(3, "criteria.approved", by="owner", number=1),
        )
        self.assertEqual(bm.acts_of(approved, None), [])

    def test_a_merge_is_offered_while_open_and_not_while_the_forge_calls_it_conflicting(
        self,
    ) -> None:
        events = (
            ev(
                0,
                "proposed",
                green=False,
                not_green=["a test was deleted"],
                tip="abc123456",
            ),
            state(1, "open", Merge.PR),
        )
        self.assertEqual(bm.acts_of(one(*events), None), ["merge"])
        seen = {"gift-note": {"mergeable": "CONFLICTING", "head": "abc123456789"}}
        self.assertEqual(bm.acts_of(one(*events), seen), [])
        self.assertEqual(
            bm.merge_says(one(*events)),
            {
                "green": False,
                "proposed": True,
                "reasons": ["a test was deleted"],
                "careful": False,
                "careful_why": "",
            },
        )

    def test_a_park_is_offered_while_a_breaker_waits_and_not_once_the_task_is_parked(
        self,
    ) -> None:
        stop, held = Breakers.STOP, Breakers.HELD
        self.assertEqual(
            bm.acts_of(one(state(0, "building", "task 2 of 3"), stop, held), None),
            ["park"],
        )
        self.assertEqual(
            bm.acts_of(
                one(
                    state(0, "building", "task 2 of 3"),
                    stop,
                    held,
                    state(30, "parked", "the owner parked it"),
                ),
                None,
            ),
            [],
        )

    def test_the_activity_says_where_he_asked_from_and_no_login(self) -> None:
        said = bm.describe(
            ev(0, "board.act", act="merge", via=bm.VIA["door"]),
            model(state(0, "open", Merge.PR)),
        )
        self.assertEqual(
            (said["head"], said["text"]),
            ("You merged it from the board", "the board, through the tailnet door"),
        )


class InterviewRead(unittest.TestCase):
    """An interview's held block says that it waits for the owner from its first
    question to his yes; while the personas read the criteria (`criteria.read.start`
    with no `criteria.read` after it) Lem waits for them, and nothing of the task waits
    for him (the case of 2026-11-19, in the plan of interview-end-tells-board)."""

    READ = Acts.READ
    INTERVIEW = (
        state(
            0,
            "held",
            "the interview waits for the owner",
            "type: feat, because the export gets a column",
        ),
        ev(0.5, "scout.start"),
        ev(1, "interview.start"),
        ev(3, "scout"),
    )

    @staticmethod
    def rows(m: "bm.Model") -> list:
        return [(w["key"], w["kind"]) for w in bm.waits_of(m)]

    def test_the_row_leaves_while_the_personas_read_and_comes_back_when_his_yes_is_what_is_missing(
        self,
    ) -> None:
        asking = model(*self.INTERVIEW)
        t = asking.tasks[0]
        self.assertEqual(
            (self.rows(asking), t.for_owner, t.lane, bm.now_head(t)),
            ([("held:gift-note", "held")], True, "you", "The interview waits for you"),
        )

        reading = model(*self.INTERVIEW, ev(10, "criteria.read.start", by="lem"))
        t = reading.tasks[0]
        self.assertEqual(self.rows(reading), [])
        self.assertEqual(
            (t.for_owner, t.lane, t.info["actor"], bm.who_acts(t), bm.now_head(t)),
            (False, "build", "quiet", "Lem acts", "The personas read the criteria"),
        )
        self.assertEqual(
            bm.card_line(t, bm.LANE["build"]),
            (
                "The personas read the criteria: nothing waits for you "
                "until their read is in"
            ),
        )
        self.assertEqual(bm.acts_of(t, None), [])
        self.assertEqual([x.slug for x in reading.for_owner], [])

        read = model(
            *self.INTERVIEW,
            ev(10, "criteria.read.start", by="lem"),
            ev(14, "criteria.read", **self.READ),
        )
        t = read.tasks[0]
        self.assertEqual(
            (self.rows(read), t.for_owner, t.lane, bm.now_head(t)),
            (
                [("criterion:gift-note:20261120T090000Z", "held")],
                True,
                "you",
                "The criteria wait for your yes",
            ),
        )
        self.assertEqual(bm.acts_of(t, None), ["approve"])

    def test_a_read_nobody_answered_and_started_once_more_hides_the_row_again(
        self,
    ) -> None:
        silent: dict[str, Any] = dict(
            self.READ,
            answered=0,
            families=[],
            silent=[{"name": "Ania, opus", "why": "no answer"}],
        )
        again = model(
            *self.INTERVIEW,
            ev(10, "criteria.read.start", by="lem"),
            ev(14, "criteria.read", **silent),
            ev(15, "criteria.read.start", by="lem"),
        )
        self.assertEqual((self.rows(again), again.tasks[0].for_owner), ([], False))

    def test_the_scouts_read_keeps_the_row_since_the_interview_may_still_ask_him(
        self,
    ) -> None:
        # the log has no end of the interview: while the scout reads, a question may
        # wait for him
        scouting = model(*self.INTERVIEW[:3])
        self.assertEqual(self.rows(scouting), [("held:gift-note", "held")])

    def test_a_read_that_started_before_the_newest_block_does_not_hide_it(self) -> None:
        # a start with no end before the held block (one a resumed task carried over) is
        # no read of these criteria
        stale = model(ev(0, "criteria.read.start", by="lem"), *self.INTERVIEW)
        self.assertEqual(self.rows(stale), [("held:gift-note", "held")])

    def test_a_session_gone_in_the_read_is_still_a_row(self) -> None:
        reading = model(*self.INTERVIEW, ev(10, "criteria.read.start", by="lem"))
        reading.sessions = {}
        self.assertEqual(self.rows(reading), [("session:gift-note", "session")])

    def test_lem_project_waiting_counts_only_the_interview_that_asks_him(self) -> None:
        # the case of 2026-11-19: two interviews, the personas read the criteria of the
        # first; `lem project waiting` lists the rows of waits_of and counts them, so it
        # counts one, as the board's Waits for you lists one
        first, second = "landing-in-the-background", "interview-in-a-companion"
        m = model(
            state(0, "held", "the interview waits for the owner", task=first),
            ev(1, "interview.start", task=first),
            state(2, "held", "the interview waits for the owner", task=second),
            ev(3, "interview.start", task=second),
            ev(10, "criteria.read.start", task=first, by="lem"),
        )
        self.assertEqual(self.rows(m), [(f"held:{second}", "held")])
        self.assertEqual([t.slug for t in m.for_owner], [second])


class InterviewTurns(unittest.TestCase):
    """Who acts on a held interview, from the events after its newest block: the owner
    answers the questions, Lem writes the criteria once they ended (`interview.end`),
    the owner says whether to skip the personas' read (`read.skip.asked`), the personas
    read, and his yes is what is missing (the plan of interview-end-tells-board, its
    acceptance criteria 1 to 4, on `report-dates-stay-whole`)."""

    SLUG = "report-dates-stay-whole"
    READ = Acts.READ
    SKIP: dict[str, Any] = {
        "id": 1,
        "by": "owner",
        "what": bm.READ_SKIP["what"],
        "chose": bm.READ_SKIP["chose"],
        "why": "y",
    }

    def interview(self, *events: dict) -> tuple:
        return (
            state(
                0,
                "held",
                "the interview waits for the owner",
                "type: fix, because a report cuts its dates",
                task=self.SLUG,
            ),
            ev(0.5, "scout.start", self.SLUG),
            ev(1, "interview.start", self.SLUG),
            *events,
        )

    def at(self, minute: float, event: str, **fields: object) -> dict:
        return ev(minute, event, self.SLUG, **fields)

    def rows(self, m: "bm.Model") -> list:
        return [
            (w["key"], w["kind"], bm.wait_say(w)["verb"], bm.wait_say(w)["to"])
            for w in bm.waits_of(m)
        ]

    def test_criterion_1_after_the_last_answer_lem_writes_the_criteria_and_nothing_waits_for_him(
        self,
    ) -> None:
        # the scout still reads (no `scout` yet), then its report is in, and Lem writes
        # the criteria
        for scout in ((), (self.at(6, "scout"),)):
            with self.subTest(scout_report=bool(scout)):
                m = model(*self.interview(self.at(5, "interview.end"), *scout))
                t = m.tasks[0]
                self.assertEqual(
                    (self.rows(m), [x.slug for x in m.for_owner], t.for_owner, t.lane),
                    ([], [], False, "build"),
                )
                self.assertEqual(
                    bm.card_line(t, bm.LANE["build"]),
                    "Lem writes the criteria; then they come to you.",
                )
                self.assertNotIn("scout", bm.card_line(t, bm.LANE["build"]).lower())
                self.assertEqual(
                    (bm.who_acts(t), bm.now_head(t), t.info["actor"]),
                    ("Lem acts", "Lem writes the criteria", "lem"),
                )
                self.assertIsNone(bm.waits_for(t, bm.waits_of(m)))
                self.assertEqual(bm.acts_of(t, None), [])

    def test_criterion_2_the_skip_question_is_his_row_and_his_no_starts_the_read(
        self,
    ) -> None:
        asking = model(*self.interview())
        interview_row = self.rows(asking)
        self.assertEqual(
            interview_row,
            [(f"held:{self.SLUG}", "held", "The interview waits for you", "overview")],
        )

        written = (self.at(5, "interview.end"), self.at(6, "scout"))
        skip = model(*self.interview(*written, self.at(12, "read.skip.asked")))
        t = skip.tasks[0]
        # a row of its own, named by the held block, with its words; the board answers
        # it with its Yes and No
        self.assertEqual(
            self.rows(skip),
            [
                (
                    f"skip:{self.SLUG}:20261120T090000Z",
                    "held",
                    "Lem asks whether to skip the personas' read of the criteria",
                    "overview",
                )
            ],
        )
        self.assertEqual(
            (t.for_owner, t.lane, t.need, bm.who_acts(t)),
            (True, "you", asking.tasks[0].need, "You act"),
        )
        self.assertIn("y or n", bm.answer_of(t))
        self.assertEqual(bm.acts_of(t, None), [])

        said_no = model(
            *self.interview(
                *written,
                self.at(12, "read.skip.asked"),
                self.at(13, "criteria.read.start", by="lem"),
            )
        )
        self.assertEqual((self.rows(said_no), said_no.tasks[0].for_owner), ([], False))
        read_in = model(
            *self.interview(
                *written,
                self.at(12, "read.skip.asked"),
                self.at(13, "criteria.read.start", by="lem"),
                self.at(18, "criteria.read", **self.READ),
            )
        )
        self.assertEqual(
            self.rows(read_in),
            [
                (
                    f"criterion:{self.SLUG}:20261120T090000Z",
                    "held",
                    "The criteria wait for your yes",
                    "overview",
                )
            ],
        )

        said_yes = model(
            *self.interview(
                *written,
                self.at(12, "read.skip.asked"),
                self.at(13, "decision.taken", **self.SKIP),
            )
        )
        t = said_yes.tasks[0]
        self.assertEqual(
            self.rows(said_yes),
            [
                (
                    f"criterion:{self.SLUG}:20261120T090000Z",
                    "held",
                    "The criteria wait for your yes",
                    "overview",
                )
            ],
        )
        self.assertEqual(
            (bm.now_head(t), bm.acts_of(t, None)),
            ("The criteria wait for your yes", ["approve"]),
        )

    def test_criterion_3_while_he_is_away_lem_goes_on_and_only_a_breaker_and_an_order_stay_his(
        self,
    ) -> None:
        away = {
            "ts": "2026-11-20T09:02:00Z",
            "event": "owner",
            "away": True,
            "words": "/lem im-away",
        }
        back = {
            "ts": "2026-11-20T09:20:00Z",
            "event": "owner",
            "away": False,
            "words": "/lem im-back",
        }
        order = "export-notes-in-order"
        others = (
            state(
                0,
                "held",
                'the order waits for the owner: "after the export task"',
                "type: feat, because notes get an order",
                task=order,
            ),
            state(0, "building", "task 1 of 2", task="gift-note"),
            ev(1, "decision.breaker", "gift-note", id=1, cause="criteria", what="w"),
            state(1, "held", "breaker 1 waits for the owner", task="gift-note"),
            state(
                0,
                "held",
                "the investigation waits for one more fact",
                task="zero-after-refund",
            ),
        )

        m = model(*self.interview(), *others, owner=[away])
        t = m.by_slug[self.SLUG]
        self.assertEqual(
            sorted(w["key"] for w in bm.waits_of(m)),
            [bkey(minute=1), f"held:{order}", "held:zero-after-refund"],
        )
        self.assertEqual(
            (t.for_owner, t.lane, t.goes_on, bm.now_head(t), bm.who_acts(t)),
            (False, "build", "interview", "Lem goes on without you", "Lem acts"),
        )
        self.assertTrue(
            bm.card_line(t, bm.LANE["build"]).startswith("Lem goes on without you: ")
        )
        self.assertIn("each in the task's decisions for the pull request", t.shown)
        self.assertNotIn(self.SLUG, [x.slug for x in m.for_owner])

        # back while Lem still has questions: the row comes back, and the next question
        # is his
        m = model(*self.interview(), *others, owner=[away, back])
        t = m.by_slug[self.SLUG]
        self.assertIn(f"held:{self.SLUG}", [w["key"] for w in bm.waits_of(m)])
        self.assertEqual(
            (t.for_owner, t.goes_on, bm.now_head(t)),
            (True, None, "The interview waits for you"),
        )

    def test_criterion_3_a_nights_task_and_the_requests_one_answer_go_on_without_him(
        self,
    ) -> None:
        night = self.at(
            0,
            "task.mode",
            mode="alone",
            by="lem",
            words="the night of 2026-11-19",
            all=False,
            was="with-owner",
        )
        m = model(night, *self.interview())
        self.assertEqual((self.rows(m), m.tasks[0].goes_on), ([], "interview"))
        criteria = model(
            self.at(
                0, "task.mode", mode="alone", by="lem", words="the night of 2026-11-19"
            ),
            state(
                1,
                "held",
                (
                    "the criteria wait for the owner: a small change that "
                    "someone else asked for"
                ),
                task=self.SLUG,
            ),
        )
        self.assertEqual(
            (self.rows(criteria), criteria.tasks[0].goes_on), ([], "criteria")
        )
        away = {
            "ts": "2026-11-20T08:00:00Z",
            "event": "owner",
            "away": True,
            "words": "out",
        }
        answer = (state(0, "held", "the request waits for one answer", task=self.SLUG),)
        self.assertEqual(model(*answer, owner=[away]).tasks[0].goes_on, "answer")
        self.assertEqual(len(bm.waits_of(model(*answer, owner=[away]))), 0)
        self.assertEqual(
            [w["key"] for w in bm.waits_of(model(*answer))], [f"held:{self.SLUG}"]
        )

    def test_criterion_4_the_interview_ends_with_its_questions_and_lems_writing_runs_to_the_read(
        self,
    ) -> None:
        # the questions ended at 10:05 and the read started at 10:12 (START is 9:00)
        t = one(
            state(59, "held", "the interview waits for the owner", task=self.SLUG),
            self.at(60, "interview.start"),
            self.at(65, "interview.end"),
            self.at(72, "criteria.read.start", by="lem"),
        )
        tm = bm.time_of(t, bm.time_end(t, NOW))
        got = [
            (g["row"], g["from"], g["to"], g["head"])
            for g in tm["spans"]
            if g["head"] in ("The interview", "Lem writes the criteria")
        ]

        def ms(minute: float) -> int:
            return int((START + timedelta(minutes=minute)).timestamp() * 1000)

        self.assertEqual(
            got,
            [
                ("you", ms(60), ms(65), "The interview"),
                ("lem", ms(65), ms(72), "Lem writes the criteria"),
            ],
        )
        # the skip question and his approval end Lem's writing too
        for end in (
            self.at(70, "read.skip.asked"),
            self.at(70, "criteria.approved", by="owner", number=1),
        ):
            with self.subTest(end=end["event"]):
                t = one(
                    state(
                        0, "held", "the interview waits for the owner", task=self.SLUG
                    ),
                    self.at(60, "interview.start"),
                    self.at(65, "interview.end"),
                    end,
                )
                writes = [
                    (g["from"], g["to"])
                    for g in bm.time_of(t, bm.time_end(t, NOW))["spans"]
                    if g["head"] == "Lem writes the criteria"
                ]
                self.assertEqual(writes, [(ms(65), ms(70))])

    def test_the_timeline_says_both_events(self) -> None:
        m = model(*self.interview())
        self.assertEqual(
            bm.describe(self.at(5, "interview.end"), m)["head"],
            "The interview’s questions ended",
        )
        self.assertEqual(
            bm.describe(self.at(12, "read.skip.asked"), m)["head"],
            "Lem asked whether to skip the personas’ read",
        )


class HomeFolder:
    """The events of one-home-folder-for-lem on 2026-11-23, as its log holds them up to
    its criteria's held block at 11:39:31 UTC, and what the board says of the
    task's wait."""

    SLUG = "one-home-folder-for-lem"
    NOW = "2026-11-23T11:44:04Z"
    CRITERIA = "2026-11-23T11:39:31Z"

    def at(self, ts: str, event: str, **fields: object) -> dict:
        return {"ts": ts, "event": event, "task": self.SLUG, **fields}

    def board(self, *more: dict, now: str = NOW) -> "bm.Model":
        return bm.derive([*self.events(), *more], [], cast("int", bm.at(now)))

    def events(self) -> list[dict]:
        return [
            self.at(
                "2026-11-23T09:53:42Z",
                "session.open",
                session="S1",
                name=self.SLUG,
                phase="shape",
                why="new",
            ),
            self.at(
                "2026-11-23T09:55:24Z",
                "task.state",
                status="held",
                text="the interview waits for the owner",
                lines=[
                    (
                        "type: feat, because the reviewer seat starts to "
                        "hold for the whole machine"
                    )
                ],
            ),
            self.at("2026-11-23T09:55:36Z", "scout.start"),
            self.at("2026-11-23T09:56:19Z", "interview.start"),
            self.at("2026-11-23T09:58:27Z", "scout"),
            self.at("2026-11-23T11:35:19Z", "interview.end"),
            self.at("2026-11-23T11:36:00Z", "criteria.read.start", by="lem"),
            self.at(
                "2026-11-23T11:37:48Z",
                "criteria.read",
                by="lem",
                asked=3,
                answered=3,
                families=["opus"],
                silent=[],
                criteria=10,
                flagged=6,
                split=False,
                digest="70aebe27373c",
            ),
            self.at(
                self.CRITERIA,
                "task.state",
                status="held",
                text="the criteria wait for the owner",
                lines=[
                    (
                        "the personas doubt 6 of 10 criteria; criterion 5, the "
                        "correction queue's switch, is wrong for two of them"
                    )
                ],
            ),
        ]

    def ctx(self, m: "bm.Model") -> "pages.Ctx":
        return pages.Ctx(
            host="h",
            workspace="w",
            model=m,
            asset=lambda name: name,
            task=self.SLUG,
            tab="overview",
        )

    def clocks(self, m: "bm.Model", slug: str | None = None) -> tuple:
        """The start of a task's wait as the row of Waits for you, the pill and In this
        state say it: the row's `since`, or None with no row, and each `data-since` of
        the pill and of the facts."""
        t = m.by_slug[slug or self.SLUG]
        row = next((w["since"] for w in bm.waits_of(m) if w["t"] is t), None)
        ctx = self.ctx(m)
        pill = re.findall(r'data-since="(\d+)"', str(task_pages.pill(ctx, t)))
        facts = re.findall(
            r'id="dd-time".*?data-since="(\d+)"',
            str(join(task_pages.facts(ctx, t, bm.waits_of(m)))),
            re.DOTALL,
        )
        return row, [int(x) for x in pill], [int(x) for x in facts]


class WaitStart(HomeFolder, unittest.TestCase):
    """A wait for the owner counts from its own held block, not from an earlier held
    block of another wait: the case of one-home-folder-for-lem on 2026-11-23, whose
    criteria waited from 11:39:31 UTC while the board said "Waits for you 1h 48m",
    "since 10:55" (local), the time of its interview's block. The events are the ones
    its log holds, read at 11:44:04 UTC, the time of the owner's screenshot."""

    def test_the_criteria_wait_counts_from_its_own_block_on_the_row_the_pill_and_in_this_state(
        self,
    ) -> None:
        m = self.board()
        t = m.by_slug[self.SLUG]
        began = bm.at(self.CRITERIA)
        # the task waits for the owner's yes, as it did: only the start of the wait
        # is wrong
        self.assertEqual(
            (t.for_owner, [w["kind"] for w in bm.waits_of(m)]), (True, ["criteria"])
        )
        self.assertEqual(
            bm.waits_of(m)[0]["since"],
            began,
            "the row of Waits for you counts from the interview's block, 09:55:24 UTC",
        )
        ctx = self.ctx(m)
        self.assertIn(
            f'data-since="{began}"',
            str(task_pages.pill(ctx, t)),
            "the pill counts from the interview's block",
        )
        facts = str(join(task_pages.facts(ctx, t, [])))
        self.assertIn(
            f'data-since="{began}"',
            facts,
            "In this state counts from the interview's block",
        )


class WaitClock(HomeFolder, unittest.TestCase):
    """A held or blocked block written again with the same first line keeps the clock of
    its wait, and a task in any other status counts from when it entered it (criterion 5
    of waits-for-you-only-when-it-waits), on the row of Waits for you, the pill and In
    this state."""

    def test_the_same_held_line_written_again_by_a_new_session_keeps_the_wait_at_11_39(
        self,
    ) -> None:
        m = self.board(
            self.at(
                "2026-11-23T12:10:00Z",
                "session.open",
                session="S2",
                name=self.SLUG,
                phase="shape",
                why="resume",
            ),
            self.at(
                "2026-11-23T12:10:05Z",
                "task.state",
                status="held",
                text="the criteria wait for the owner",
                lines=[],
            ),
            now="2026-11-23T12:15:00Z",
        )
        began = bm.at(self.CRITERIA)
        self.assertEqual(self.clocks(m), (began, [began], [began]))

    def test_a_blocked_task_counts_from_the_block_that_named_its_wait(self) -> None:
        five, thirty = bm.at(ev(5, "x")["ts"]), bm.at(ev(30, "x")["ts"])
        again = (
            state(0, "building", "task 1 of 2"),
            state(5, "blocked", "the fixture needs a login"),
            state(20, "blocked", "the fixture needs a login"),
        )
        self.assertEqual(
            self.clocks(model(*again), "gift-note"), (five, [five], [five])
        )
        other = model(*again, state(30, "blocked", "the fixture needs a second login"))
        self.assertEqual(self.clocks(other, "gift-note"), (thirty, [thirty], [thirty]))

    def test_a_building_task_counts_from_when_it_started_to_build(self) -> None:
        ten = bm.at(ev(10, "x")["ts"])
        m = model(
            state(0, "queued", "it waits"),
            state(10, "building", "task 1 of 3"),
            state(30, "building", "task 2 of 3"),
        )
        self.assertEqual(self.clocks(m, "gift-note"), (None, [ten], [ten]))


class SessionAtWork(HomeFolder, unittest.TestCase):
    """A held task is the owner's only while its session's newest turn has ended, or
    while Lem cannot read that turn (criteria 1 to 3 of
    waits-for-you-only-when-it-waits): one-home-folder-for-lem, whose owner pressed
    "Discuss in chat" on the criteria page at 11:42:42 UTC; its session's turn ran from
    11:42:52 and ended at 11:43:33 on one question in the terminal. `put_sessions` takes
    the sessions as `lem session list` prints them."""

    RUNS = "2026-11-23T11:43:00Z"
    ENDED = "2026-11-23T11:43:33Z"

    def sessions(
        self,
        turn: str | None,
        *,
        live: bool = True,
        agent: bool = True,
        slug: str | None = None,
    ) -> dict:
        entry = {
            "task": slug or self.SLUG,
            "session": "S1",
            "name": slug or self.SLUG,
            "live": live,
            "agent": agent,
            "unanswered": False,
            "sign": "2026-11-23T11:42:52Z",
            "shell": True,
            "signs": live,
            "turn": turn,
        }
        return bm.sessions_of(bm.session_entries(json.dumps([entry])), set())

    def rows(self, m: "bm.Model") -> list:
        return [(w["kind"], w["key"], w["since"]) for w in bm.waits_of(m)]

    def row_key(self) -> str:
        """The key of the criteria's row, which the board answers with Yes and No: named
        by the held block of 11:39:31."""
        return f"criterion:{self.SLUG}:{bm.lem_answers.stamp_of(self.CRITERIA)}"

    def panel(self, m: "bm.Model") -> dict:
        ctx, t = self.ctx(m), m.by_slug[self.SLUG]
        return {
            "facts": str(join(task_pages.facts(ctx, t, bm.waits_of(m)))),
            "key": str(task_pages.key_line(ctx, t)),
            "now": str(task_pages.now_card(ctx, t)),
        }

    def test_criterion_1_while_the_turn_runs_the_task_is_lems_work_and_no_row(
        self,
    ) -> None:
        m = self.board(now=self.RUNS)
        bm.put_sessions(m, self.sessions("runs"))
        t = m.by_slug[self.SLUG]
        self.assertEqual(self.rows(m), [])
        self.assertEqual(
            (t.works, t.for_owner, t.lane, m.for_owner), (True, False, "build", [])
        )
        self.assertEqual((m.lane["you"], m.lane["build"]), ([], [t]))
        self.assertEqual(t.info, bm.WORKS_INFO)
        self.assertEqual(
            (bm.now_head(t), bm.who_acts(t)),
            ("Its session works on your answer", "The task's session acts"),
        )
        self.assertEqual(
            bm.card_line(t, bm.LANE["build"]),
            "Works on your answer: it waits for you again when the session's turn ends",
        )
        self.assertEqual(pages.summary_of(m), "1 whose session works on your answer")
        # the Inbox keeps what it sent for the row the session holds back
        self.assertEqual(bm.held_back(m), {self.row_key()})
        panel = self.panel(m)
        self.assertNotIn("Waits for", panel["facts"])
        self.assertNotIn("p-key you", panel["key"])
        self.assertNotIn("Where you answer", panel["now"])
        self.assertIn("Its session works on your answer", panel["now"])

    def test_criterion_2_when_the_turn_ends_on_the_same_model_the_row_is_back_since_11_39(
        self,
    ) -> None:
        m = self.board(now=self.RUNS)
        bm.put_sessions(m, self.sessions("runs"))
        # the server keeps the model it derived and sets the sessions again at its
        # next look
        m.now = cast("int", bm.at(self.ENDED))
        bm.put_sessions(m, self.sessions("ended"))
        t = m.by_slug[self.SLUG]
        began = bm.at(self.CRITERIA)
        self.assertEqual(self.rows(m), [("criteria", self.row_key(), began)])
        self.assertEqual(
            (t.works, t.for_owner, t.lane, m.for_owner, m.lane["you"]),
            (False, True, "you", [t], [t]),
        )
        self.assertEqual(bm.held_back(m), set())
        # exactly what settle gave the task, as a model derived at 11:43:33 says
        fresh = self.board(now=self.ENDED)
        bm.put_sessions(fresh, self.sessions("ended"))
        same = fresh.by_slug[self.SLUG]
        self.assertEqual(
            (t.info, t.shown, t.lane, t.for_owner),
            (same.info, same.shown, same.lane, same.for_owner),
        )
        self.assertEqual(self.clocks(m), (began, [began], [began]))
        self.assertIn("Waits for", self.panel(m)["facts"])
        self.assertIn("Where you answer", self.panel(m)["now"])

    def test_the_sessions_put_again_give_the_same_model(self) -> None:
        m = self.board(now=self.RUNS)
        bm.put_sessions(m, self.sessions("runs"))
        t = m.by_slug[self.SLUG]
        once = (
            self.rows(m),
            dict(t.info),
            t.shown,
            t.lane,
            t.for_owner,
            list(m.for_owner),
            {k: list(v) for k, v in m.lane.items()},
        )
        bm.put_sessions(m, self.sessions("runs"))
        self.assertEqual(
            (self.rows(m), t.info, t.shown, t.lane, t.for_owner, m.for_owner, m.lane),
            once,
        )
        # and a turn that ended, twice, gives what settle gave
        bm.put_sessions(m, self.sessions("ended"))
        ended = (self.rows(m), dict(t.info), t.shown, t.lane, t.for_owner)
        bm.put_sessions(m, self.sessions("ended"))
        self.assertEqual((self.rows(m), t.info, t.shown, t.lane, t.for_owner), ended)
        self.assertEqual(ended[0], [("criteria", self.row_key(), bm.at(self.CRITERIA))])

    def test_criterion_3_with_no_turn_lem_can_read_the_task_waits_as_today(
        self,
    ) -> None:
        cases = {
            "the server has not asked": None,
            "no session of the task": {},
            "no transcript Lem reads": self.sessions(None),
            "no agent in its pane": self.sessions("runs", agent=False),
            "not in agterm": self.sessions("runs", live=False),
        }
        for why, facts in cases.items():
            with self.subTest(why=why):
                today = self.board(now=self.RUNS)
                today.sessions = facts
                m = self.board(now=self.RUNS)
                bm.put_sessions(m, facts)
                t = m.by_slug[self.SLUG]
                self.assertIn(
                    ("criteria", self.row_key(), bm.at(self.CRITERIA)), self.rows(m)
                )
                self.assertEqual(self.rows(m), self.rows(today))
                self.assertEqual(
                    (t.works, t.for_owner, t.lane, t.info),
                    (False, True, "you", today.by_slug[self.SLUG].info),
                )

    def test_a_breakers_held_task_follows_the_turn_and_a_blocked_task_keeps_its_row(
        self,
    ) -> None:
        stop = ev(
            20,
            "decision.breaker",
            id=1,
            kind="breaker",
            cause="criteria",
            what="The gift note has no place",
            document="breaker.md",
        )
        m = model(
            state(0, "building", "task 1 of 2"),
            stop,
            state(20, "held", "breaker 1 waits for the owner"),
        )
        bm.put_sessions(m, self.sessions("runs", slug="gift-note"))
        self.assertEqual((bm.waits_of(m), bm.held_back(m)), ([], {bkey()}))
        self.assertEqual(bm.now_head(m.tasks[0]), "Its session works on your answer")
        bm.put_sessions(m, self.sessions("ended", slug="gift-note"))
        self.assertEqual([w["key"] for w in bm.waits_of(m)], [bkey()])
        blocked = model(
            state(0, "building", "task 1 of 2"),
            state(5, "blocked", "the fixture needs a login"),
        )
        bm.put_sessions(blocked, self.sessions("runs", slug="gift-note"))
        self.assertEqual(
            ([w["key"] for w in bm.waits_of(blocked)], blocked.tasks[0].works),
            (["blocked:gift-note"], False),
        )

    def test_two_threads_that_put_the_same_sessions_at_once_leave_the_task_lems_work(
        self,
    ) -> None:
        # the board server's request threads, its forge thread and its Inbox thread each
        # put the sessions on the one model the Reader keeps: here the first put waits
        # inside the held task while a second one puts the same sessions
        m = self.board(now=self.RUNS)
        bm.put_sessions(m, self.sessions("runs"))
        inside, go = threading.Event(), threading.Event()
        real = bm.works_of

        def held_up(t: "bm.Task", model: "bm.Model") -> bool:
            if t.slug == self.SLUG and not inside.is_set():
                inside.set()
                go.wait(5)
            return real(t, model)

        problems: list = []

        def put() -> None:
            try:
                bm.put_sessions(m, self.sessions("runs"))
            except Exception as error:  # noqa: BLE001 - the thread's own error, which the test reports
                problems.append(error)

        with mock.patch.object(bm, "works_of", held_up):
            first = threading.Thread(target=put)
            first.start()
            self.assertTrue(inside.wait(5))
            second = threading.Thread(target=put)
            second.start()
            # a put that took no lock runs to its end here, inside the first one's
            second.join(1)
            go.set()
            first.join(5)
            second.join(5)
        t = m.by_slug[self.SLUG]
        self.assertEqual(problems, [])
        self.assertEqual(
            (self.rows(m), t.works, t.for_owner, t.lane, m.for_owner, bm.held_back(m)),
            ([], True, False, "build", [], {self.row_key()}),
        )

    def waiting(self, turn: str, caller: str | None = None) -> list:
        """The keys of the rows `lem project waiting` lists at 11:43, with the session's
        turn TURN, asked from the agterm session CALLER (none: outside agterm)."""
        from lem import project

        env = {
            k: v
            for k, v in os.environ.items()
            if k not in ("AGTERM_SESSION_ID", "AGT_SESSION_ID")
        } | ({"AGTERM_SESSION_ID": caller} if caller else {})
        with tempfile.TemporaryDirectory() as folder:
            state_folder = Path(folder)
            (state_folder / "events.jsonl").write_text(
                "".join(json.dumps(e) + "\n" for e in self.events()), encoding="utf-8"
            )
            # the task began on the release that runs, so that the board answers its
            # rows (`task_files_look`)
            (state_folder / "tasks" / self.SLUG).mkdir(parents=True)
            (state_folder / "tasks" / self.SLUG / "release.txt").write_text(
                bm.lem_release.running() + "\n", encoding="utf-8"
            )
            with (
                mock.patch.object(project, "state_root", return_value=state_folder),
                mock.patch.object(project, "main_checkout", return_value=state_folder),
                mock.patch.object(project, "owner_records", return_value=[]),
                mock.patch.object(
                    project,
                    "waiting_sessions",
                    return_value=(self.sessions(turn), None),
                ),
                mock.patch.object(bm, "now_ms", return_value=bm.at(self.RUNS)),
                mock.patch.dict(os.environ, env, clear=True),
            ):
                found, _ = project.waiting_model(Path("/lem-unit/repo"), {})
        return [w["key"] for w in bm.waits_of(found)]

    def test_lem_project_waiting_lists_the_task_only_once_the_turn_ended(self) -> None:
        self.assertEqual(self.waiting("runs"), [])
        self.assertEqual(self.waiting("ended"), [self.row_key()])

    def test_the_tasks_own_session_finds_its_row_in_lem_project_waiting_while_its_turn_runs(
        self,
    ) -> None:
        # the session asks inside its own turn, which then runs: a breaker's wake reads
        # its row there to put up its card
        self.assertEqual(self.waiting("runs", caller="S1"), [self.row_key()])
        # another session's ask still reads the task's turn
        self.assertEqual(self.waiting("runs", caller="S2"), [])


class Sessions(unittest.TestCase):
    """When a task is stuck for want of its session (a row of "Waits for you", which the
    push sends), and when the board offers "Open a session" (plan-task-4.md section 7,
    item 2)."""

    @staticmethod
    def rows(m: "bm.Model") -> list:
        return [
            (w["kind"], bm.wait_say(w)["verb"])
            for w in bm.waits_of(m)
            if w["kind"] == "session"
        ]

    def test_a_task_whose_phase_needs_an_agent_and_has_no_live_session_is_a_row_and_gets_the_button(
        self,
    ) -> None:
        events = (
            state(0, "building", "lead: builder"),
            ev(
                1,
                "session.open",
                session="S1",
                name="gift-note",
                phase="build",
                why="handoff",
            ),
        )
        m = model(*events)
        m.sessions = {"gift-note": {"live": True, "agent": False}}
        self.assertEqual(self.rows(m), [("session", "No session runs this task")])
        self.assertTrue(bm.opens_session(m.tasks[0], m))
        m.sessions = {"gift-note": {"live": True, "agent": True}}
        self.assertEqual((self.rows(m), bm.opens_session(m.tasks[0], m)), ([], False))

    def test_the_where_of_a_task_whose_session_is_gone_says_what_its_row_says(
        self,
    ) -> None:
        m = model(
            state(0, "building", "lead: builder"), state(30, "building", "task 2 of 3")
        )
        m.sessions = {}
        t, waits = m.tasks[0], bm.waits_of(m)
        self.assertEqual(self.rows(m), [("session", "No session runs this task")])
        where = cast("dict", bm.waits_for(t, waits))["where"]
        self.assertIn("Open a session here or on the task’s header", where)
        self.assertIn("/lem drop gift-note", where)
        self.assertNotIn("Tell the task’s session", where)

    def test_a_task_with_a_second_row_beside_no_session_is_answered_where_that_row_says(
        self,
    ) -> None:
        # no-session-row-names-open, review round 1, 2026-11-22: a held and a planned
        # task with no session were sent to the session that is gone
        for status, text, second in (
            ("held", "the migration needs the owner", "held"),
            ("planned", "plan written, the owner reads it", "plan"),
        ):
            with self.subTest(status=status):
                m = model(state(0, "building", "lead: builder"), state(5, status, text))
                m.sessions = {}
                t, waits = m.tasks[0], bm.waits_of(m)
                self.assertEqual([w["kind"] for w in waits], ["session", second])
                # the open comes first, and the second row's words follow for the
                # session he opens
                self.assertEqual(
                    cast("dict", bm.waits_for(t, waits))["where"],
                    f"{bm.wait_say(waits[0])['where']} {bm.answer_of(t)}",
                )
                self.assertTrue(
                    bm.wait_say(waits[0])["where"].startswith(
                        "Open a session here or on the task’s header"
                    )
                )

    def test_nothing_is_said_while_the_server_has_not_asked_or_the_session_is_young(
        self,
    ) -> None:
        self.assertEqual(self.rows(model(state(0, "building", "lead: builder"))), [])
        young = model(state(119, "held", "the interview waits for the owner"))
        young.sessions = {}
        self.assertEqual(self.rows(young), [])

    def test_a_task_that_waits_only_for_his_merge_has_the_button_and_no_row(
        self,
    ) -> None:
        m = model(state(0, "open", Merge.PR, "green"))
        m.sessions = {}
        self.assertEqual((self.rows(m), bm.opens_session(m.tasks[0], m)), ([], True))

    def test_a_merged_task_has_a_row_only_while_its_worktree_stays(self) -> None:
        m = model(
            state(0, "open", Merge.PR),
            state(
                10,
                "landed",
                "main: pull request https://github.com/acme/shop/pull/41 is merged",
            ),
        )
        m.sessions = {"gift-note": {"worktree": True}}
        self.assertEqual(
            self.rows(m), [("session", "No session cleans the merged task")]
        )
        m.sessions = {}
        self.assertEqual((self.rows(m), bm.opens_session(m.tasks[0], m)), ([], False))

    CLOSED_ON_GITHUB = (
        state(0, "open", Merge.PR),
        state(10, "dropped", "the pull request was closed on the forge"),
    )

    def test_a_task_dropped_by_a_close_on_github_has_a_row_only_while_its_worktree_stays(
        self,
    ) -> None:
        # decision 28 of github-issues-tracker: the wake of such a task failed, and the
        # board says so
        m = model(*self.CLOSED_ON_GITHUB)
        m.sessions = {"gift-note": {"worktree": True}}
        self.assertEqual(bm.session_need(m.tasks[0], m), "gone")
        rows = [w for w in bm.waits_of(m) if w["kind"] == "session"]
        self.assertEqual(
            [(w["key"], bm.wait_say(w)["verb"], bm.wait_say(w)["note"]) for w in rows],
            [
                (
                    "session:gift-note",
                    "No session cleans the dropped task",
                    "since it was dropped",
                )
            ],
        )
        m.sessions = {}
        self.assertEqual((bm.session_need(m.tasks[0], m), self.rows(m)), (None, []))

    def test_a_task_dropped_by_a_close_on_github_gets_the_button_only_while_its_worktree_stays(
        self,
    ) -> None:
        m = model(*self.CLOSED_ON_GITHUB)
        m.sessions = {"gift-note": {"worktree": True}}
        self.assertTrue(bm.opens_session(m.tasks[0], m))
        m.sessions = {"gift-note": {"worktree": True, "live": True, "agent": True}}
        self.assertFalse(bm.opens_session(m.tasks[0], m))
        m.sessions = {}
        self.assertFalse(bm.opens_session(m.tasks[0], m))

    def test_the_board_offers_a_session_to_each_ended_task_that_phase_of_gives_one(
        self,
    ) -> None:
        # session.py's `phase_of` is the one that opens it: the board agrees with it on
        # every ended state
        from lem import session

        for status in bm.ENDED:
            for worktree in (True, False):
                with self.subTest(status=status, worktree=worktree):
                    try:
                        session.phase_of(
                            "gift-note",
                            status,
                            "it ended",
                            None,
                            worktree=worktree,
                            state="",
                        )
                        gets = True
                    except session.SessionError:
                        gets = False
                    m = model(state(0, "open", Merge.PR), state(10, status, "it ended"))
                    m.sessions = {"gift-note": {"worktree": True}} if worktree else {}
                    self.assertEqual(
                        (
                            bm.opens_session(m.tasks[0], m),
                            bm.session_need(m.tasks[0], m) == "gone",
                        ),
                        (gets, gets),
                    )

    def test_a_wake_nobody_took_is_a_row_of_its_own(self) -> None:
        m = model(state(0, "open", Merge.PR))
        m.sessions = {"gift-note": {"live": True, "agent": True, "unanswered": True}}
        rows = bm.waits_of(m)
        self.assertEqual(
            [
                (w["key"], bm.wait_say(w)["verb"])
                for w in rows
                if w["kind"] == "session"
            ],
            [("deaf:gift-note", "Its session does not answer")],
        )

    def test_a_parked_task_and_one_queued_behind_an_open_task_have_none(self) -> None:
        parked = model(state(0, "parked", "the owner parked it"))
        parked.sessions = {}
        queued = model(
            state(0, "open", Merge.PR, task="coupon"),
            state(1, "queued", "it starts after coupon", "after: coupon"),
        )
        queued.sessions = {}
        self.assertEqual((self.rows(parked), self.rows(queued)), ([], []))
        self.assertFalse(bm.opens_session(queued.by_slug["gift-note"], queued))

    def test_a_demo_reads_a_session_from_the_log_alone(self) -> None:
        demo = bm.derive(
            [
                state(0, "building", "lead: builder"),
                ev(1, "session.open", session="S1", name="gift-note"),
            ],
            [],
            NOW,
            meta={"demo": True},
        )
        self.assertEqual(self.rows(demo), [])
        closed = bm.derive(
            [
                state(0, "building", "lead: builder"),
                ev(1, "session.open", session="S1"),
                ev(2, "session.close", session="S1", why="owner"),
            ],
            [],
            NOW,
            meta={"demo": True},
        )
        self.assertEqual(self.rows(closed), [("session", "No session runs this task")])


class DeafRow(unittest.TestCase):
    """The row "Its session does not answer" in each of its two cases, which `lem
    session list` names beside `unanswered` (`unheard`): the wake's line still waits in
    the session's mailbox, or the pane took it and no turn came (a parked Claude Code
    process). The review of 2026-11-24."""

    def where(self, unheard: dict | None) -> str:
        m = model(state(0, "building", "lead: builder"))
        m.sessions = {
            "gift-note": {
                "live": True,
                "agent": True,
                "unanswered": True,
                "unheard": unheard,
            }
        }
        row = next(w for w in bm.waits_of(m) if w["kind"] == "session")
        return bm.wait_say(row)["where"]

    def test_each_case_says_what_is_true_names_the_wake_and_the_act_that_works(
        self,
    ) -> None:
        # the words say what the mailbox and the transcript show: when Lem sent the
        # line, that the pane took it, and whether a turn ran after it (the review of
        # 2026-11-24 on 0b1bbf9a)
        taken = self.where({"why": "merged", "line": "taken"})
        self.assertEqual(
            taken,
            (
                "Lem sent the wake-up “lem: gift-note merged” 10 minutes ago or more. "
                "The task’s session took it, and took no turn after it. Go to the "
                "session and tell it to go on, or close the session: then this row "
                "offers “Open a session”."
            ),
        )
        # a pane that took the line while a turn or a command of its own runs is
        # busy: no word tells the owner to close it
        runs = self.where({"why": "merged", "line": "runs"})
        self.assertEqual(
            runs,
            (
                "Lem sent the wake-up “lem: gift-note merged” 10 minutes ago or more. "
                "The task’s session took it while a turn or a command of it ran, and "
                "took no turn after it. Look at the session: its agent may run a long "
                "turn or command."
            ),
        )
        waits = self.where({"why": "merged", "line": "waits"})
        self.assertEqual(
            waits,
            (
                "The wake-up “lem: gift-note merged” has waited in the task’s session "
                "for 10 minutes or more. Look at the session: its agent may wait for "
                "an answer, or run a long turn."
            ),
        )
        # an entry with no case, as a `lem session list` of the release before
        # gives it, keeps the words of the line that waits
        self.assertEqual(
            self.where(None),
            (
                "A wake-up has waited in the task’s session for 10 minutes or more. "
                "Look at the session: its agent may wait for an answer, "
                "or run a long turn."
            ),
        )


class Blocked(unittest.TestCase):
    """A task its session stopped (`blocked`) waits for the owner's word, except while
    the base is red."""

    def test_a_blocked_task_is_a_row_of_his_with_its_own_line_and_the_base_red_is_none(
        self,
    ) -> None:
        m = model(
            state(0, "building", "lead: builder"),
            state(5, "blocked", "a builder ended two times with no report"),
        )
        t = m.tasks[0]
        rows = bm.waits_of(m)
        self.assertEqual(
            [(w["key"], bm.wait_say(w)["verb"]) for w in rows],
            [("blocked:gift-note", "Its session stopped: tell it what to do")],
        )
        self.assertIn(
            "a builder ended two times with no report", bm.wait_say(rows[0])["where"]
        )
        self.assertEqual(
            (t.lane, t.info["actor"], bm.now_head(t)),
            ("you", "you", "Its session stopped: it waits for your word"),
        )
        red = model(
            state(0, "landing", "the checks run"),
            state(5, "blocked", "the base is red", "after: fix-the-base"),
        )
        self.assertEqual((bm.waits_of(red), red.tasks[0].lane), ([], "build"))
        self.assertIn("waits for the base", bm.now_head(red.tasks[0]))

    def test_the_where_of_a_blocked_task_says_to_tell_its_session_what_to_do(
        self,
    ) -> None:
        # no-session-row-names-open, 2026-11-22: the tooltip of the card's Waits for
        # fact asked him to have the stopped session build it
        m = model(
            state(0, "building", "lead: builder"),
            state(5, "blocked", "the migration needs the owner"),
        )
        m.sessions = {"gift-note": {"live": True, "agent": True}}
        t, rows = m.tasks[0], bm.waits_of(m)
        where = cast("dict", bm.waits_for(t, rows))["where"]
        self.assertEqual(where, bm.wait_say(rows[0])["where"])
        self.assertEqual(bm.answer_of(t), where)
        self.assertIn("“the migration needs the owner”", where)
        self.assertNotIn("to build it", where)


class ReleaseStop(unittest.TestCase):
    """A task two releases back (lem_release): Lem's first command for it logged
    `release.stop` and stopped. The board shows it blocked with the message, and its
    status stays the one of its state, which the forge's watch and land.py read."""

    SAY = (
        "gift-note began on Lem 0.1.6, and Lem 0.3.0 reads only tasks begun on 0.2.0 "
        "or 0.3.0. Your branch and its commits stay. /lem drop gift-note, then /lem "
        "resume gift-note, starts a new task on 0.3.0 from that branch and from "
        "the notes the task left."
    )

    def stop(self, minute: float) -> dict:
        return ev(
            minute,
            "release.stop",
            began="0.1.6",
            running="0.3.0",
            branch="feat/gift-note",
            say=self.SAY,
        )

    def test_an_open_task_two_releases_back_is_shown_blocked_with_the_message_and_stays_open(
        self,
    ) -> None:
        m = model(
            ev(0, "proposed", green=True, not_green=[], tip="abc123456"),
            state(1, "open", Merge.PR, "green"),
            self.stop(5),
        )
        t = m.tasks[0]
        self.assertEqual((t.status, cast("dict", bm.pr_of(t))["n"]), ("open", "41"))
        self.assertEqual(
            (t.info["label"], t.info["actor"], t.lane, t.shown),
            ("Blocked", "you", "you", self.SAY),
        )
        self.assertEqual(bm.card_line(t, bm.LANE["you"]), f"Blocked: {self.SAY}")
        self.assertIn(t, m.blocked)
        rows = bm.waits_of(m)
        self.assertEqual(
            [(w["kind"], w["key"], w["say"]) for w in rows],
            [("blocked", "blocked:gift-note", self.SAY)],
        )
        self.assertEqual(bm.wait_say(rows[0])["where"], self.SAY)
        # every act of the board would stop in the guard: the drop is the way on
        self.assertEqual(bm.acts_of(t, None), [])

    def test_what_a_task_two_releases_back_waits_for_is_the_stops_message_in_any_status(
        self,
    ) -> None:
        for status, text in (
            ("open", Merge.PR),
            ("building", "the plan talk runs"),
            ("planned", "the plan waits for the owner"),
            ("held", "the criteria wait for the owner"),
            ("blocked", "the session stopped"),
            ("queued", "after: fix-the-base"),
            ("parked", "the owner parked it"),
        ):
            with self.subTest(status=status):
                m = model(state(1, status, text), self.stop(5))
                t = m.tasks[0]
                wait = cast("dict", bm.waits_for(t, bm.waits_of(m)))
                self.assertEqual(
                    (t.status, bm.acts_of(t, None), wait["you"], wait["where"]),
                    (status, [], True, self.SAY),
                )
                self.assertEqual(bm.answer_of(t), self.SAY)
                # one place: "Waits for you" and the blocked tasks, never the parked
                self.assertEqual((t in m.blocked, t in m.parked), (True, False))
                self.assertEqual(
                    bm.card_line(t, bm.LANE["you"]), f"Blocked: {self.SAY}"
                )

    def test_a_landing_two_releases_back_is_out_of_the_guard_of_a_stopped_session(
        self,
    ) -> None:
        t = one(state(0, "landing", "the checks run"), self.stop(5))
        self.assertEqual(t.status, "landing")
        self.assertIn(t.status, bm.GUARDED)
        self.assertFalse(bm.guarded(t))
        self.assertTrue(bm.guarded(one(state(0, "landing", "the checks run"))))

    def test_a_held_task_two_releases_back_stays_blocked_while_its_sessions_turn_runs(
        self,
    ) -> None:
        m = model(state(0, "held", "the criteria wait for the owner"), self.stop(5))
        entry = {
            "task": "gift-note",
            "session": "S1",
            "name": "gift-note",
            "live": True,
            "agent": True,
            "unanswered": False,
            "sign": "2026-11-23T11:42:52Z",
            "shell": True,
            "signs": True,
            "turn": "runs",
        }
        bm.put_sessions(
            m, bm.sessions_of(bm.session_entries(json.dumps([entry])), set())
        )
        t = m.tasks[0]
        self.assertEqual(
            (t.works, t.for_owner, t.lane, t.info["label"], t.shown),
            (False, True, "you", "Blocked", self.SAY),
        )
        self.assertEqual([w["key"] for w in bm.waits_of(m)], ["blocked:gift-note"])

    def test_the_board_answers_no_plan_and_no_breaker_of_a_task_two_releases_back(
        self,
    ) -> None:
        breaker = [
            state(0, "building", "task 1 of 2"),
            ev(
                20,
                "decision.breaker",
                id=1,
                cause="criteria",
                what="The note has no place",
                document="breaker.md",
            ),
            state(20, "held", "breaker 1 waits for the owner"),
        ]
        for name, events in (
            ("breaker", breaker),
            ("plan", [state(1, "planned", "the plan waits for the owner")]),
        ):
            with self.subTest(wait=name):
                t = one(*events, self.stop(30))
                self.assertEqual(
                    (bm.answer_row(t), bm.acts_of(t, None), bm.now_head(t)),
                    (None, [], "It began on an older release of Lem"),
                )

    def test_a_state_after_the_stop_is_the_tasks_own_work_again(self) -> None:
        t = one(
            state(0, "open", Merge.PR),
            self.stop(5),
            state(6, "dropped", "the owner dropped it: it began two releases back"),
        )
        self.assertEqual(
            (t.status, t.release_stop, t.info["label"]), ("dropped", None, "Dropped")
        )
        self.assertEqual(
            bm.waits_of(
                model(
                    state(0, "open", Merge.PR),
                    self.stop(5),
                    state(6, "dropped", "dropped"),
                )
            ),
            [],
        )

    def test_the_mark_of_a_task_two_releases_back_stops_its_acts_before_any_stop_is_logged(
        self,
    ) -> None:
        # no command of Lem ran for the task since the release moved, so the log holds
        # no `release.stop`: the board offered the merge, the approval and the answer of
        # its row all the same, and each would stop in the guard
        with tempfile.TemporaryDirectory() as folder:
            tasks = Path(folder) / "tasks"
            for slug, mark in (("gift-note", "0.0.1"), ("fresh", None)):
                (tasks / slug).mkdir(parents=True)
                (tasks / slug / "release.txt").write_text(
                    (mark or bm.lem_release.running()) + "\n", encoding="utf-8"
                )
            m = model(
                ev(0, "proposed", green=True, not_green=[], tip="abc123456"),
                state(1, "open", Merge.PR, "green"),
                state(1, "held", "the criteria wait for the owner", task="fresh"),
            )
            self.assertEqual(bm.acts_of(m.by_slug["gift-note"], None), ["merge"])
            bm.task_files_look(Path(folder), m)
            bm.task_files_look(Path(folder), m)  # each look, the same
        t = m.by_slug["gift-note"]
        say = cast(
            "dict",
            bm.lem_release.stop(
                "gift-note", "0.0.1", bm.lem_release.running(), bm.lem_release.BEFORE
            ),
        )["say"]
        self.assertEqual(
            (t.status, bm.acts_of(t, None), bm.answer_row(t), bm.now_head(t)),
            ("open", [], None, bm.OLDER_RELEASE),
        )
        self.assertEqual(
            (t.info["label"], t.info["actor"], t.lane, t.shown),
            ("Blocked", "you", "you", say),
        )
        self.assertEqual(
            ([x.slug for x in m.blocked], [x.slug for x in m.for_owner]),
            # a held task's criteria press more than a blocked task (OWNER_ORDER)
            (["gift-note"], ["fresh", "gift-note"]),
        )
        self.assertEqual(
            [(w["key"], w.get("say")) for w in bm.waits_of(m) if w["t"] is t],
            [("blocked:gift-note", say)],
        )
        # a task of this release keeps its acts
        self.assertIsNone(m.by_slug["fresh"].release_stop)


class SeatThatFailed(unittest.TestCase):
    """A task a seat's error blocked (`lem project seat-failed`) is a row of "Waits for
    you" with its first line, as any blocked task; the timeline says each stand-in,
    block and go on; and a block of the merge agent's seat keeps its pull request in the
    server's look at GitHub."""

    LINE = (
        "the reviewer `codex/gpt-6.2-sol:high` gave an error: no tokens, and this "
        "project permits no fallback"
    )
    PR = "pull request https://github.com/acme/shop/pull/41"

    def test_the_block_is_his_row_with_its_line(self) -> None:
        m = model(
            state(0, "building", "the plan talk runs", "lead: session"),
            state(5, "blocked", self.LINE, "the seat that failed: reviewer"),
        )
        t = m.tasks[0]
        self.assertEqual(
            (t.failed_seat, t.text, t.lane), ("reviewer", self.LINE, "you")
        )
        self.assertEqual([w["key"] for w in bm.waits_of(m)], ["blocked:gift-note"])
        self.assertIn(self.LINE, bm.wait_say(bm.waits_of(m)[0])["where"])
        self.assertIsNone(
            one(
                state(0, "blocked", "the base is red", "after: fix-the-base")
            ).failed_seat
        )

    def test_the_timeline_says_each_seat_event(self) -> None:
        m = model(state(0, "building", "the plan talk runs"))
        stood = bm.describe(
            ev(
                1,
                "seat.stand-in",
                seat="reviewer",
                failed="codex/gpt-6.2-sol:high",
                took="claude/opus:high",
                error="tokens",
                said="no tokens left",
            ),
            m,
        )
        self.assertEqual(
            (stood["head"], stood["text"], stood["sub"]),
            (
                "The fallback stood in for the reviewer",
                "claude/opus:high in place of codex/gpt-6.2-sol:high",
                "no tokens left",
            ),
        )
        blocked = bm.describe(
            ev(
                2,
                "seat.blocked",
                seat="merger",
                failed="codex/gpt-6.2-sol:high",
                error="tokens",
                say=self.LINE,
            ),
            m,
        )
        self.assertEqual(
            (blocked["head"], blocked["text"], blocked["info"]["actor"]),
            (
                "The seat of the merge agent gave an error, and no fallback stood in",
                self.LINE,
                "you",
            ),
        )
        again = bm.describe(
            ev(
                3,
                "seat.again",
                seat="reviewer",
                say=(
                    "the owner's go on: the reviewer codex/gpt-6.2-sol:high is tried "
                    "again"
                ),
            ),
            m,
        )
        self.assertEqual(
            (again["head"], again["text"]),
            (
                "Your go on: the seat is tried again",
                "the owner's go on: the reviewer codex/gpt-6.2-sol:high is tried again",
            ),
        )

    def test_a_block_of_the_merge_agent_keeps_its_pull_request_in_the_look_at_github(
        self,
    ) -> None:
        from lem import serve

        merger = self.LINE.replace("the reviewer", "the merge agent")
        m = model(
            state(0, "open", self.PR),
            state(5, "blocked", merger, "the seat that failed: merger"),
            state(0, "open", self.PR.replace("41", "42"), task="other"),
            state(
                5, "blocked", self.LINE, "the seat that failed: reviewer", task="other"
            ),
        )
        self.assertEqual([pr["task"] for pr in serve.open_prs(m)], ["gift-note"])


class NewTask(unittest.TestCase):
    """A task whose session opened and wrote no state block is on the board from its
    first minute."""

    def test_a_session_open_with_no_block_is_a_task_that_starts(self) -> None:
        m = model(
            ev(
                0,
                "session.open",
                session="S1",
                name="gift-note",
                phase="shape",
                why="new",
            )
        )
        t = m.by_slug["gift-note"]
        self.assertEqual(
            (t.status, t.info["label"], t.lane, bm.now_head(t)),
            (bm.NEW, "Starting", "build", "Its session opened: it reads the request"),
        )
        self.assertEqual(bm.waits_of(m), [])
        m.sessions = {}
        self.assertEqual([w["key"] for w in bm.waits_of(m)], ["session:gift-note"])
        self.assertTrue(bm.opens_session(t, m))
        later = model(
            ev(0, "session.open", session="S1"),
            state(1, "held", "the request waits for one answer"),
        )
        self.assertEqual(later.tasks[0].status, "held")


class ForgeLook(unittest.TestCase):
    def test_the_servers_last_look_is_read_from_the_state_folder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            self.assertIsNone(bm.forge_look(folder))
            (folder / bm.FORGE_LOOK).write_text(
                json.dumps(
                    {
                        "looked": "2026-11-21T10:00:00Z",
                        "seen": {
                            "gift-note": {"mergeable": "CONFLICTING", "head": "abc"}
                        },
                    }
                )
            )
            self.assertEqual(
                cast("dict", bm.forge_look(folder))["seen"]["gift-note"]["head"], "abc"
            )
            (folder / bm.FORGE_LOOK).write_text("half")
            self.assertIsNone(bm.forge_look(folder))

    def test_sessions_of_adds_the_worktrees_of_ended_tasks(self) -> None:
        found = bm.sessions_of(
            bm.session_entries(
                '[{"task": "a", "live": true, "agent": true, "turn": "runs"}]'
            ),
            {"b"},
        )
        self.assertEqual(
            found,
            {
                "a": {
                    "live": True,
                    "agent": True,
                    "unanswered": None,
                    "unheard": None,
                    "session": None,
                    "name": None,
                    "sign": None,
                    "shell": None,
                    "signs": None,
                    "turn": "runs",
                    "worktree": False,
                },
                "b": {"worktree": True},
            },
        )


class Workspace(unittest.TestCase):
    def test_the_owners_newest_record_says_whether_he_is_away(self) -> None:
        away = {
            "ts": "2026-11-20T10:00:00Z",
            "event": "owner",
            "away": True,
            "words": "out",
        }
        back = {"ts": "2026-11-20T10:30:00Z", "event": "owner", "away": False}
        self.assertEqual(
            cast("dict", model(state(0, "queued", "x"), owner=[away]).away)["words"],
            "out",
        )
        self.assertIsNone(model(state(0, "queued", "x"), owner=[away, back]).away)

    def test_done_shows_the_newest_first_and_a_task_with_no_block_has_no_card(
        self,
    ) -> None:
        m = model(
            state(0, "landed", "merged", task="old-one"),
            state(50, "landed", "merged", task="new-one"),
            ev(5, "criteria.read", task="early"),
        )
        self.assertEqual([t.slug for t in m.lane["done"]], ["new-one", "old-one"])
        self.assertNotIn("early", [t.slug for t in m.tasks])

    def test_done_keeps_every_ended_task_and_the_ones_after_its_newest_20_are_the_older(
        self,
    ) -> None:
        ended = ("landed", "dropped", "answered")
        m = model(
            *(
                state(i, ended[i % 3], "it ended", task=f"task-{i:02d}")
                for i in range(25)
            ),
            state(30, "building", "task 1 of 2", task="builds"),
        )
        self.assertEqual(bm.DONE_SHOWN, 20)
        self.assertEqual(len(m.lane["done"]), 25)
        self.assertEqual(
            [t.slug for t in bm.done_older(m)],
            ["task-04", "task-03", "task-02", "task-01", "task-00"],
        )
        self.assertEqual(
            bm.done_older(
                model(
                    *(
                        state(i, "landed", "merged", task=f"task-{i:02d}")
                        for i in range(20)
                    )
                )
            ),
            [],
        )

    def test_the_phases_of_the_fast_track_and_of_the_standard_track(self) -> None:
        fast = one(
            state(0, "building", "small change: one builder"),
            state(9, "landing", "the checks start"),
        )
        self.assertEqual(
            (bm.phases_of(fast)["names"][0], bm.phases_of(fast)["at"]), ("Change", 1)
        )
        standard = one(state(0, "building", "plan committed, 3 tasks"))
        self.assertEqual(
            (bm.phases_of(standard)["names"][0], bm.phases_of(standard)["at"]),
            ("Criteria", 2),
        )


class Reader(unittest.TestCase):
    def test_the_log_is_read_on_from_where_it_stopped_and_a_bad_line_is_said(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            reader = bm.Reader(Path(tmp), Path(tmp))
            log = Path(tmp) / "events.jsonl"
            log.write_text(json.dumps(state(0, "queued", "x")) + "\n")
            reader.read_log()
            self.assertEqual((len(reader.events), reader.problems), (1, {}))
            with log.open("a") as out:
                out.write(
                    "not json\n"
                    + json.dumps(state(1, "building", "y"))
                    + "\n"
                    + '{"ts": "half'
                )
            reader.read_log()
            self.assertEqual(
                [e["status"] for e in reader.events], ["queued", "building"]
            )
            self.assertIn("line 2", reader.problems["events"])
            with log.open("a") as out:
                out.write(' a line"}\n')
            reader.read_log()
            self.assertIn("line 4", reader.problems["events"])

    def test_a_bad_line_is_named_by_its_line_of_the_file_after_a_blank_line(
        self,
    ) -> None:
        said = (
            "events.jsonl: line 3 is no event with a time, and the board leaves it out"
        )
        good = json.dumps(state(0, "queued", "x"))
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "events.jsonl"
            # in one read: a blank line, a good event, then a line that is no JSON
            log.write_text(f"\n{good}\nnot json\n")
            reader = bm.Reader(Path(tmp), Path(tmp))
            reader.read_log()
            self.assertEqual(reader.problems["events"], said)
            # in two reads: the bad line comes after the read of the first two
            log.write_text(f"\n{good}\n")
            reader = bm.Reader(Path(tmp), Path(tmp))
            reader.read_log()
            with log.open("a") as out:
                out.write("not json\n")
            reader.read_log()
            self.assertEqual(reader.problems["events"], said)


class Inbox(unittest.TestCase):
    """What the task's page reads of the owner's Inbox: the board server's record
    (`inbox.json`, which lem_inbox.Watcher writes), read as `forge.json` is, and what it
    says for a task that waits for him while his mark says away (criteria 6 and 7
    of away-questions-reach-phone)."""

    AWAY = [
        {
            "ts": "2026-11-20T10:00:00Z",
            "event": "owner",
            "away": True,
            "words": "I'm away",
        }
    ]
    LIVE = {"gift-note": {"live": True, "agent": True, "session": "S1"}}
    TAILNET = "https://studio.tail4e2a.ts.net:8443/"

    @classmethod
    def record(cls, *sent: object, **door: object) -> dict:
        return {
            "running": True,
            "url": "http://plannotator.localhost:50026/",
            "tailnet_url": cls.TAILNET,
            "why": None,
            "said": "",
            "problem": None,
            **door,
            "sent": list(sent),
        }

    @staticmethod
    def thing(
        key: str | None = None,
        kind: str = "breaker",
        form: str = "question",
        *,
        asks: bool = True,
        task: str = "gift-note",
        **more: object,
    ) -> dict:
        return {
            "key": key or bkey(),
            "task": task,
            "kind": kind,
            "form": form,
            "asks": asks,
            "session": "C1" if form == "question" else None,
            "message_id": "msg_01ABC",
            "thread_id": "msg_01ABC",
            "thread_url": "http://plannotator.localhost:50026/#thread=msg_01ABC",
            **more,
        }

    def breaker(
        self,
        record: dict | None,
        owner: list[dict] = AWAY,
        sessions: dict | None = LIVE,
    ) -> dict | None:
        m = model(
            ev(0, "session.open", session="S1", name="gift-note"),
            state(1, "building", "task 2 of 3"),
            Breakers.STOP,
            Breakers.HELD,
            owner=owner,
        )
        m.sessions, m.inbox = sessions, record
        return bm.inbox_of(m.tasks[0], m)

    def test_the_record_is_the_servers_file_read_whole_and_each_why_has_its_words(
        self,
    ) -> None:
        from lem import inbox as lem_inbox

        self.assertEqual(
            (bm.INBOX_LOOK, set(bm.INBOX_WHY)), (lem_inbox.RECORD, set(lem_inbox.WHYS))
        )
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            self.assertIsNone(bm.inbox_look(folder))
            (folder / bm.INBOX_LOOK).write_text(
                json.dumps(self.record(self.thing(), {"task": "gift-note"}, "x"))
            )
            self.assertEqual(
                [s["key"] for s in cast("dict", bm.inbox_look(folder))["sent"]],
                [bkey()],
            )
            (folder / bm.INBOX_LOOK).write_text("half")
            self.assertIsNone(bm.inbox_look(folder))

    def test_the_reader_puts_the_record_into_the_model_and_reads_it_again_when_it_changes(
        self,
    ) -> None:
        from types import ModuleType, SimpleNamespace

        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)

            def load(root: Path) -> Never:
                raise ValueError("no settings here")

            lem_state = SimpleNamespace(
                owner_mark=lambda: folder / "owner.jsonl", StateError=OSError
            )
            board = SimpleNamespace(
                lem_project=SimpleNamespace(
                    lem_state=lem_state,
                    owner_records=list,
                    SettingsError=OSError,
                    load=load,
                ),
                meta_of=lambda *_: {},
            )
            reader = bm.Reader(folder, folder)
            self.assertIsNone(reader.current(cast("ModuleType", board), NOW).inbox)
            (folder / bm.INBOX_LOOK).write_text(json.dumps(self.record(self.thing())))
            self.assertEqual(
                cast("dict", reader.current(cast("ModuleType", board), NOW).inbox)[
                    "tailnet_url"
                ],
                self.TAILNET,
            )
            (folder / bm.INBOX_LOOK).write_text(
                json.dumps(
                    self.record(running=False, tailnet_url=None, why="not running")
                )
            )
            self.assertEqual(
                cast("dict", reader.current(cast("ModuleType", board), NOW).inbox)[
                    "why"
                ],
                "not running",
            )

    def test_criterion_6_a_question_sent_while_he_is_away_links_to_its_thread_at_the_tailnet_address(
        self,
    ) -> None:
        self.assertEqual(
            self.breaker(self.record(self.thing())),
            {
                "thread": f"{self.TAILNET}#thread=msg_01ABC",
                "asks": True,
                "gone": False,
                "why": None,
            },
        )
        # an address with no slash at its end, and a thread id that needs quoting
        said = cast(
            "dict",
            self.breaker(
                self.record(
                    self.thing(thread_id='m"1 <x>'),
                    tailnet_url="https://studio.tail4e2a.ts.net:8443",
                )
            ),
        )
        self.assertEqual(
            said["thread"],
            "https://studio.tail4e2a.ts.net:8443/#thread=m%221%20%3Cx%3E",
        )

    def test_criterion_7_with_the_door_closed_the_page_gets_why_and_no_link(
        self,
    ) -> None:
        for why, words in (
            (
                "not running",
                "The Inbox does not run on this Mac, so no question went there.",
            ),
            (
                "no tailnet address",
                "The Inbox has no tailnet address, so the phone cannot open it.",
            ),
        ):
            with self.subTest(why=why):
                said = self.breaker(
                    self.record(running=why != "not running", tailnet_url=None, why=why)
                )
                self.assertEqual(
                    said, {"thread": None, "asks": False, "gone": False, "why": words}
                )
        # a question of the task that went before the door closed is there: the line
        # says so, not that none went
        self.assertEqual(set(bm.INBOX_WHY_SENT), set(bm.INBOX_WHY))
        for why, words in (
            (
                "not running",
                (
                    "A message of this task went to the Inbox, but the Inbox does not "
                    "run on this Mac now, so the phone cannot open it."
                ),
            ),
            (
                "no tailnet address",
                "The Inbox has no tailnet address, so the phone cannot open it.",
            ),
        ):
            with self.subTest(why=why, sent=True):
                said = self.breaker(
                    self.record(
                        self.thing(),
                        running=why != "not running",
                        tailnet_url=None,
                        why=why,
                    )
                )
                self.assertEqual(
                    said, {"thread": None, "asks": False, "gone": False, "why": words}
                )
        self.assertTrue(
            all(
                "no question went there" not in words
                for words in bm.INBOX_WHY_SENT.values()
            )
        )
        # a word the model does not know is still said, and no address but http or https
        # is a link
        self.assertIn(
            "“later”",
            cast(
                "dict",
                self.breaker(self.record(running=False, tailnet_url=None, why="later")),
            )["why"],
        )
        self.assertIsNone(
            self.breaker(self.record(self.thing(), tailnet_url="javascript:alert(1)"))
        )

    def test_nothing_changes_while_he_is_there_while_nothing_of_the_task_went_and_for_an_old_row(
        self,
    ) -> None:
        self.assertIsNone(self.breaker(self.record(self.thing()), owner=[]))
        self.assertIsNone(self.breaker(None))
        self.assertIsNone(self.breaker(self.record()))
        # the note of a session that came back, which the server forgets at its
        # next look
        self.assertIsNone(
            self.breaker(
                self.record(
                    self.thing("session:gift-note", "session", "note", asks=False)
                )
            )
        )
        # a thing that waits for its send again after a call that failed
        unsent = {
            k: v
            for k, v in self.thing().items()
            if k not in ("message_id", "thread_id")
        }
        self.assertEqual(
            cast(
                "dict",
                self.breaker(
                    self.record(
                        unsent,
                        problem=f"the send of {bkey()}: server_error: down",
                    )
                ),
            )["why"],
            bm.INBOX_UNSENT,
        )
        self.assertIsNone(self.breaker(self.record(unsent)))

    def test_a_note_says_whether_a_session_can_take_a_reply_and_the_merge_review_is_the_merges_thing(
        self,
    ) -> None:
        gone = cast(
            "dict",
            self.breaker(
                self.record(
                    self.thing("session:gift-note", "session", "note", asks=False)
                ),
                sessions={},
            ),
        )
        self.assertEqual((gone["asks"], gone["gone"]), (False, True))
        merge = model(
            state(0, "open", Merge.PR),
            ev(
                1,
                "merge.review",
                verdict="call",
                calls=True,
                why="careful",
                by="claude",
                tip="abc",
            ),
            owner=self.AWAY,
        )
        merge.sessions, merge.inbox = (
            self.LIVE,
            self.record(self.thing("merge:gift-note", "merge", "note", asks=False)),
        )
        self.assertEqual(
            [w["key"] for w in bm.waits_of(merge)],
            ["review:gift-note", "merge:gift-note"],
        )
        said = cast("dict", bm.inbox_of(merge.tasks[0], merge))
        self.assertEqual(
            (said["asks"], said["gone"], said["thread"]),
            (False, False, f"{self.TAILNET}#thread=msg_01ABC"),
        )


if __name__ == "__main__":
    unittest.main()


class MovedBase(unittest.TestCase):
    """An open task whose merge met a moved base is Lem's to land again, and one whose
    owner's merge stood through that landing is the server's to merge; a dropped task
    does not start the task queued behind it."""

    PR = "pull request https://github.com/acme/shop/pull/41"

    def test_a_base_refusal_is_no_row_and_githubs_is_his(self) -> None:
        proposed = (
            ev(0, "proposed", green=True, not_green=[], tip="abc123456"),
            state(1, "open", self.PR),
        )
        base = model(
            *proposed,
            ev(
                2,
                "merge.refused",
                by="owner",
                via="server",
                **{"from": "lem"},
                kind="base",
                said="origin/main moved after the checks ran",
                tip="abc123456",
            ),
        )
        t = base.tasks[0]
        # the merge agent reads what moved, and nothing waits for the owner
        self.assertEqual(
            (t.merge_wait, t.for_owner, t.info["label"], bm.waits_of(base)),
            ("reads", False, "The merge agent reads it", []),
        )
        github = model(
            *proposed,
            ev(
                2,
                "merge.refused",
                by="owner",
                via="server",
                **{"from": "github"},
                said="Required status check is expected",
                tip="abc123456",
            ),
        )
        self.assertEqual([w["kind"] for w in bm.waits_of(github)], ["merge"])

    def read(
        self, minute: float, call: str, verdict: str = "merge", *, calls: bool = False
    ) -> dict:
        return ev(
            minute,
            "merge.review",
            verdict=verdict,
            calls=calls,
            by="claude",
            tip="abc123456",
            base="m2m2m2m2m",
            base_call=call,
            base_why="B changed only docs/board.md, which the change does not read",
        )

    def test_a_safe_read_of_the_moved_base_answers_lems_refusal(self) -> None:
        proposed = (
            ev(0, "proposed", green=True, not_green=[], tip="abc123456"),
            state(1, "open", self.PR),
        )
        refused = (
            *proposed,
            ev(
                2,
                "merge.refused",
                by="merger",
                via="server",
                **{"from": "lem"},
                kind="base",
                said="origin/main moved after the checks ran",
                tip="abc123456",
            ),
        )
        t = one(*refused, self.read(3, "safe"))
        self.assertEqual(
            (t.refused, t.merge_wait, t.info["label"]),
            (None, "merges", "Lem merges it"),
        )
        self.assertEqual(
            cast("dict", t.merge_review)["base_why"],
            "B changed only docs/board.md, which the change does not read",
        )
        # the owner's merge that the moved base refused stands on the safe read, with a
        # careful change's `Verdict: call.`
        his = (
            *proposed,
            ev(
                2,
                "merge.refused",
                by="owner",
                via="server",
                **{"from": "lem"},
                kind="base",
                said="origin/main moved",
                tip="abc123456",
            ),
            self.read(3, "safe", verdict="call", calls=True),
            ev(3, "merge.stands", by="owner", tip="abc123456", **{"from": "abc123456"}),
        )
        m = model(*his)
        self.assertEqual(
            (m.tasks[0].refused, m.tasks[0].merge_wait, bm.waits_of(m)),
            (None, "merges", []),
        )
        # a record with no verdict (two ends with no answer, or two replies with none)
        # on the checks' own base after a revert answers nothing: his merge does not
        # stand, and the refusal stays
        mute = {**self.read(3, "safe"), "base_call": None, "base_why": None}
        del mute["verdict"]
        silent = model(*his[:3], {**mute, "calls": True})
        self.assertEqual(
            (silent.tasks[0].refused is not None, silent.tasks[0].stood),
            (True, None),
        )
        # no read answers GitHub's refusal
        github = one(
            *proposed,
            ev(
                2,
                "merge.refused",
                by="merger",
                via="server",
                **{"from": "github"},
                said="Required status check is expected",
                tip="abc123456",
            ),
            self.read(3, "safe"),
        )
        self.assertEqual(
            (cast("dict", github.refused)["from"], github.merge_wait),
            ("github", "owner"),
        )

    def test_a_review_that_calls_him_after_lems_refusal_of_his_merge_waits_for_him(
        self,
    ) -> None:
        # Lem refused his merge because the base moved; the base went back to the
        # checks' tree, and two merge agents of the brief on that base ended with no
        # answer, which `merge-review --no-answer` records as a review that calls him,
        # with no verdict and no call on a move, and the refusal stays
        refused = (
            ev(0, "proposed", green=True, not_green=[], tip="abc123456"),
            state(1, "open", self.PR),
            ev(
                2,
                "merge.refused",
                by="owner",
                via="server",
                **{"from": "lem"},
                kind="base",
                said="origin/main moved after the checks ran",
                tip="abc123456",
            ),
        )
        silent = ev(
            4,
            "merge.review",
            calls=True,
            by="claude",
            tip="abc123456",
            base="m1m1m1m1m",
            why="the merge agent ended twice with no answer",
        )
        m = model(*refused, silent)
        t = m.tasks[0]
        rows = bm.waits_of(m)
        # the row "Read the merge review" that the step promised, and his merge, which
        # he gives afresh: the refused one does not go through by itself
        self.assertEqual(
            (
                t.merge_wait,
                [(w["kind"], bm.wait_say(w)["verb"]) for w in rows],
                bm.owner_stands(t),
                "merge" in bm.acts_of(t, None),
                t.refused is not None,
            ),
            (
                "owner",
                [
                    ("review", "Read the merge review"),
                    ("merge", "Merge the pull request #41"),
                ],
                False,
                True,
                True,
            ),
        )
        # before the review, the merge agent reads what moved, as before
        self.assertEqual(one(*refused).merge_wait, "reads")

    def test_a_read_on_the_checks_base_answers_lems_refusal_after_a_revert(
        self,
    ) -> None:
        # main moved and the merge was refused; a revert gave main the checks' tree
        # again, so the read's brief named the checks' own base and its review has no
        # call on a move: it answers the refusal too
        proposed = (
            ev(0, "proposed", green=True, not_green=[], tip="abc123456"),
            state(1, "open", self.PR),
        )
        refused = (
            *proposed,
            ev(
                2,
                "merge.refused",
                by="merger",
                via="server",
                **{"from": "lem"},
                kind="base",
                said="origin/main moved after the checks ran",
                tip="abc123456",
            ),
        )
        back = ev(
            3,
            "merge.review",
            verdict="merge",
            calls=False,
            by="claude",
            tip="abc123456",
            base="m1m1m1m1m",
        )
        t = one(*refused, back)
        self.assertEqual(
            (t.refused, t.merge_wait, t.info["label"]),
            (None, "merges", "Lem merges it"),
        )
        stands = bm.describe(
            ev(
                3,
                "merge.stands",
                by="owner",
                tip="abc123456",
                after="a read of the base back on the checks' tree",
                base="m1m1m1m1m",
            ),
            model(*proposed),
        )
        self.assertEqual(
            stands["text"],
            (
                "the merge agent read it on the base the checks ran on, which main has "
                "again: the board’s server runs it, and nobody asks you again"
            ),
        )
        # GitHub's refusal stays
        github = one(
            *proposed,
            ev(
                2,
                "merge.refused",
                by="merger",
                via="server",
                **{"from": "github"},
                said="Required status check is expected",
                tip="abc123456",
            ),
            back,
        )
        self.assertEqual(github.merge_wait, "owner")

    def test_another_round_relands_until_the_next_proposal(self) -> None:
        proposed = (
            ev(0, "proposed", green=True, not_green=[], tip="abc123456"),
            state(1, "open", self.PR),
        )
        refusal = ev(
            4,
            "merge.refused",
            by="merger",
            via="server",
            **{"from": "lem"},
            kind="base",
            said="the merge agent asks for another round of the checks",
            tip="abc123456",
        )
        again = (*proposed, self.read(3, "another round"), refusal)
        t = one(*again)
        self.assertEqual(
            (t.merge_wait, t.for_owner, t.info["label"]),
            ("relands", False, "Lem lands it again"),
        )
        # a later safe read answers nothing: the refusal an another-round read keeps is
        # the new landing's
        later = one(*again, self.read(5, "safe"))
        self.assertEqual(
            (later.refused is not None, later.merge_wait), (True, "relands")
        )
        # an another-round read with no refusal before it is the session's too, never
        # the server's merge
        self.assertEqual(
            one(*proposed, self.read(3, "another round")).merge_wait, "relands"
        )
        # the next proposal forgets it
        landed = one(
            *again,
            ev(6, "proposed", green=True, not_green=[], tip="def456789"),
            state(7, "open", self.PR),
        )
        self.assertEqual(landed.merge_wait, "reads")

    def test_the_feed_shows_the_read_of_a_moved_base_with_its_call(self) -> None:
        m = model(
            ev(0, "proposed", green=True, not_green=[], tip="abc123456"),
            state(1, "open", self.PR),
        )
        safe = bm.describe(self.read(3, "safe"), m)
        self.assertEqual(
            (safe["head"], safe["text"], safe["sub"]),
            (
                "The merge agent read the task and the moved base",
                "the moved base m2m2m2m2m is safe; it merges",
                "B changed only docs/board.md, which the change does not read",
            ),
        )
        again = bm.describe(self.read(3, "another round"), m)
        self.assertEqual(
            (again["info"]["actor"], again["text"]),
            (
                "gate",
                (
                    "the moved base m2m2m2m2m needs another round of the checks: "
                    "Lem lands it again"
                ),
            ),
        )
        # another round that Lem recorded because the answer could not be recorded
        why = (
            "the merge agent's answer could not be recorded twice (it ended with no "
            "answer), and in doubt the checks run again"
        )
        unread = bm.describe({**self.read(3, "another round"), "base_why": why}, m)
        self.assertEqual(
            (unread["head"], unread["text"], unread["sub"]),
            (
                "The merge agent's answer could not be recorded",
                (
                    "the moved base m2m2m2m2m gets another round of the checks in "
                    "doubt: Lem lands it again"
                ),
                why,
            ),
        )
        self.assertEqual(
            (bm.UNRECORDED, land.unrecorded_why("it ended with no answer")),
            (land.UNRECORDED, why),
        )
        plain = bm.describe(
            ev(
                3,
                "merge.review",
                verdict="merge",
                calls=False,
                by="claude",
                tip="abc123456",
            ),
            m,
        )
        self.assertEqual(
            (plain["head"], plain["text"], plain["sub"]),
            ("The merge agent read the task", "it merges", "by claude"),
        )

    def test_a_merge_the_moved_base_refused_is_not_offered_again_until_the_next_proposal(
        self,
    ) -> None:
        # his merge from the board met a moved base: it stands (`owner_tap`), and the
        # server runs it after a read that says safe, so while the merge agent reads, a
        # second press could only meet the same moved base: the page offers no Merge
        # (guard-sees-unreadable-sessions, 2026-11-23, #60). Once a read asks for
        # another round, the same tip is refused again, so the task's page offers no
        # Merge while Lem lands it again, and the new proposal offers it
        proposed = (
            ev(0, "proposed", green=True, not_green=[], tip="abc123456"),
            state(1, "open", self.PR),
            ev(
                2,
                "merge.review",
                verdict="call",
                calls=True,
                why="a careful request is merged by the owner",
                by="claude",
                tip="abc123456",
            ),
        )
        refused = (
            *proposed,
            ev(3, "merge.start", by="owner", via="server"),
            ev(
                3,
                "merge.refused",
                by="owner",
                via="server",
                **{"from": "lem"},
                kind="base",
                said="origin/main moved after the checks ran",
                tip="abc123456",
            ),
        )
        self.assertEqual(bm.acts_of(one(*proposed), None), ["merge"])
        self.assertEqual(
            (one(*refused).merge_wait, bm.acts_of(one(*refused), None)), ("reads", [])
        )
        # the merge agent's own merge that the moved base refused is no word of his: his
        # press stays offered
        merger = (
            *proposed,
            ev(
                3,
                "merge.refused",
                by="merger",
                via="server",
                **{"from": "lem"},
                kind="base",
                said="origin/main moved after the checks ran",
                tip="abc123456",
            ),
        )
        self.assertEqual(
            (one(*merger).merge_wait, bm.acts_of(one(*merger), None)),
            ("reads", ["merge"]),
        )
        another = (
            *refused,
            self.read(4, "another round", verdict="call", calls=True),
            ev(
                4,
                "merge.refused",
                by="owner",
                via="server",
                **{"from": "lem"},
                kind="base",
                said="the merge agent asks for another round of the checks",
                tip="abc123456",
            ),
        )
        self.assertEqual(one(*another).merge_wait, "relands")
        self.assertEqual(bm.acts_of(one(*another), None), [])
        again = (
            *another,
            state(5, "landing", "the base moved: the checks run again"),
            ev(9, "proposed", green=True, not_green=[], tip="def456789"),
            state(9, "open", self.PR),
        )
        self.assertEqual(bm.acts_of(one(*again), None), ["merge"])

    def test_his_standing_merge_waits_for_nobody_between_the_safe_read_and_its_stands_line(
        self,
    ) -> None:
        # standing-merge-shows-as-waiting, 2026-11-23, #60: the read's `merge.review`
        # (a careful request) and its `merge.stands` carry 10:41:22; a look between the
        # two lines gave him a review row and a merge row for his own standing merge
        m = model(
            ev(0, "proposed", green=True, not_green=[], tip="faac6eb3b"),
            state(1, "open", self.PR),
            ev(
                8,
                "merge.refused",
                by="owner",
                via="server",
                **{"from": "lem"},
                kind="base",
                said="origin/main moved after the checks ran",
                tip="faac6eb3b",
            ),
            ev(
                11,
                "merge.review",
                verdict="call",
                calls=True,
                why="a careful request is merged by the owner",
                by="claude",
                tip="faac6eb3b",
                base="d48c6a9bd",
                base_call="safe",
            ),
        )
        t = m.tasks[0]
        self.assertEqual(
            (t.merge_wait, t.for_owner, t.lane, bm.waits_of(m)),
            ("merges", False, "checks", []),
        )

    def test_his_merge_stands_from_the_refusal_through_the_servers_merge_and_its_sentence_follows_the_span(
        self,
    ) -> None:
        # guard-sees-unreadable-sessions, 2026-11-23, #60: 10:38:03 the moved base
        # refused his merge; 10:41:22 a fresh read said safe on d48c6a9bd and
        # `merge.stands` was logged; 10:41:27 the server ran his merge
        proposed = (
            ev(0, "proposed", green=True, not_green=[], tip="faac6eb3b"),
            state(1, "open", self.PR),
            ev(
                2,
                "merge.review",
                verdict="call",
                calls=True,
                why="a careful request is merged by the owner",
                by="claude",
                tip="faac6eb3b",
                base="ea54c2a2c",
                base_call="safe",
            ),
        )
        refused = (
            *proposed,
            ev(8, "merge.start", by="owner", via="server"),
            ev(
                8,
                "merge.refused",
                by="owner",
                via="server",
                **{"from": "lem"},
                kind="base",
                said="origin/main moved after the checks ran",
                tip="faac6eb3b",
            ),
        )
        safe = ev(
            11,
            "merge.review",
            verdict="call",
            calls=True,
            why="a careful request is merged by the owner",
            by="claude",
            tip="faac6eb3b",
            base="d48c6a9bd",
            base_call="safe",
            base_why=(
                "B changed only docs/rulings/rulings.md, which the change does not read"
            ),
        )
        stands = ev(
            11,
            "merge.stands",
            by="owner",
            tip="faac6eb3b",
            after="a read of the moved base",
            base="d48c6a9bd",
        )
        # it waits for the read: criterion 1's sentence
        t = one(*refused)
        self.assertEqual(
            (t.merge_wait, bm.owner_stands(t), bm.stands_said(t)),
            (
                "reads",
                True,
                (
                    "Your merge stands. It goes through when the merge agent’s read of "
                    "the new base says safe."
                ),
            ),
        )
        # the server runs it, from the safe read's `merge.stands` to its merge
        t = one(*refused, safe, stands)
        self.assertEqual(
            (t.merge_wait, bm.owner_stands(t), bm.acts_of(t, None), bm.stands_said(t)),
            ("merges", True, [], "Your merge stands. Lem merges it now."),
        )
        # cut between the read's `merge.review` and its `merge.stands`, inside one
        # `merge-review` run: the read's mark holds it
        t = one(*refused, safe)
        self.assertEqual(
            (t.merge_wait, bm.owner_stands(t), bm.acts_of(t, None), bm.stands_said(t)),
            ("merges", True, [], "Your merge stands. Lem merges it now."),
        )
        # the server's merge started at 10:41:27: the span ends there, so a try that
        # land.py refuses with no refusal on record (the pull request's base changed on
        # GitHub) offers his Merge again, and a press meets land.py's own line
        started = ev(
            12,
            "merge.start",
            by="owner",
            via="server",
            after="a read of the moved base",
            base="d48c6a9bd",
        )
        t = one(*refused, safe, stands, started)
        self.assertEqual(
            (t.merge_wait, bm.owner_stands(t), bm.stands_said(t), bm.acts_of(t, None)),
            ("merges", False, None, ["merge"]),
        )
        # while the forge calls the pull request conflicting, the conflict's text says
        # what comes next, not his merge's
        t = one(*refused, safe, stands)
        conflicting = {"gift-note": {"mergeable": "CONFLICTING", "head": "faac6eb3b"}}
        self.assertEqual(
            (
                bm.owner_stands(t),
                bm.stands_said(t, seen=conflicting),
                bm.acts_of(t, conflicting),
            ),
            (True, None, []),
        )
        # GitHub refused the standing merge: it waits for him, and his Merge is
        # offered again
        github = one(
            *refused,
            safe,
            stands,
            ev(12, "merge.start", by="owner", via="server", after="a re-check"),
            ev(
                12,
                "merge.refused",
                by="owner",
                via="server",
                **{"from": "github"},
                said="Required status check is expected",
                tip="faac6eb3b",
            ),
        )
        self.assertEqual(
            (
                github.merge_wait,
                bm.owner_stands(github),
                bm.stands_said(github),
                bm.acts_of(github, None),
            ),
            ("owner", False, None, ["merge"]),
        )
        # the merge agent's own merge that the moved base refused, then a safe read: no
        # merge of his stands
        merger = one(
            *proposed,
            ev(
                8,
                "merge.refused",
                by="merger",
                via="server",
                **{"from": "lem"},
                kind="base",
                said="origin/main moved after the checks ran",
                tip="faac6eb3b",
            ),
        )
        self.assertEqual(
            (bm.owner_stands(merger), bm.acts_of(merger, None)), (False, ["merge"])
        )
        self.assertFalse(
            bm.owner_stands(
                one(
                    *proposed,
                    ev(
                        8,
                        "merge.refused",
                        by="merger",
                        via="server",
                        **{"from": "lem"},
                        kind="base",
                        said="moved",
                        tip="faac6eb3b",
                    ),
                    safe,
                )
            )
        )
        # for the tip of a note: his merge stands for the proposed tip, and for no other
        t = one(*refused)
        self.assertEqual(
            (
                bm.owner_stands(t, "faac6eb3b" + "0" * 31),
                bm.owner_stands(t, "abc123456"),
            ),
            (True, False),
        )
        # a new proposal that carried his merge to another tip: it stands for the new
        # tip only
        carried = one(
            *refused,
            safe,
            stands,
            ev(13, "proposed", green=True, not_green=[], tip="def456789"),
            state(14, "open", self.PR),
            ev(
                14, "merge.stands", by="owner", tip="def456789", **{"from": "faac6eb3b"}
            ),
        )
        self.assertEqual(
            (
                bm.owner_stands(carried, "def456789"),
                bm.owner_stands(carried, "faac6eb3b"),
            ),
            (True, False),
        )
        # and a new proposal with no carry ends it
        self.assertFalse(
            bm.owner_stands(
                one(
                    *refused,
                    safe,
                    ev(13, "proposed", green=True, not_green=[], tip="def456789"),
                    state(14, "open", self.PR),
                )
            )
        )

    def test_a_merge_of_his_that_stands_is_the_servers(self) -> None:
        again = (
            ev(0, "proposed", green=True, not_green=[], tip="def456789"),
            state(1, "open", self.PR),
            ev(
                2,
                "merge.review",
                verdict="merge",
                calls=True,
                why="branch.land is owner",
                by="claude",
                tip="def456789",
                carried="abc123456",
            ),
            ev(3, "merge.stands", by="owner", tip="def456789", **{"from": "abc123456"}),
        )
        t = one(*again)
        self.assertEqual((t.merge_wait, t.for_owner), ("merges", False))
        # a stand of an older tip is none
        older = one(*again[:3], ev(3, "merge.stands", by="owner", tip="fff000111"))
        self.assertEqual(older.merge_wait, "owner")

    def test_a_dropped_task_leaves_the_task_behind_it_queued(self) -> None:
        queued = state(1, "queued", "it starts after coupon", "after: coupon")
        for status, ended, dropped in (
            ("landed", True, False),
            ("answered", True, False),
            ("dropped", False, True),
            ("open", False, False),
        ):
            m = model(
                state(
                    0,
                    status,
                    "it ended" if status != "open" else self.PR,
                    task="coupon",
                ),
                queued,
            )
            t = m.by_slug["gift-note"]
            self.assertEqual(
                (bm.after_ended(t, m), bm.after_dropped(t, m)), (ended, dropped), status
            )


class AfterDropped(unittest.TestCase):
    """A task queued after a task that was dropped is one row of "Waits for you", with
    the two words that start it or end it, until his word (criterion 1
    of docs/plans/2026-11-21-owner-order-open-defects.md)."""

    GIFT = "gift-note-in-export"
    ORDER = "export-notes-in-order"
    # his order, its type and its path, as step 7 of "The request" writes a queued block
    QUEUED = state(
        5,
        "queued",
        'the owner\'s order: "After gift-note-in-export"',
        "after: gift-note-in-export",
        "type: feat, because a new order",
        "then: the interview",
        task=ORDER,
    )

    def gift(self, status: str, minute: float = 30) -> tuple:
        return (
            state(0, "building", "lead: builder", task=self.GIFT),
            state(
                minute,
                status,
                "the owner dropped it" if status == "dropped" else "task 2 of 3",
                task=self.GIFT,
            ),
        )

    def test_a_task_queued_after_a_dropped_task_is_one_row_with_his_two_words(
        self,
    ) -> None:
        m = model(*self.gift("dropped"), self.QUEUED)
        m.sessions = {}
        rows = bm.waits_of(m)
        self.assertEqual(
            [(w["kind"], w["key"], w["after"]) for w in rows],
            [("after_dropped", f"after_dropped:{self.ORDER}", self.GIFT)],
        )
        # since the drop, which came after the task was queued
        self.assertEqual(rows[0]["since"], bm.at(ev(30, "x")["ts"]))
        say = bm.wait_say(rows[0])
        self.assertEqual(
            (say["verb"], say["start"], say["drop"]),
            (
                "gift-note-in-export was dropped: your word starts or ends this task",
                f"start {self.ORDER} now",
                f"/lem drop {self.ORDER}",
            ),
        )
        self.assertEqual(
            say["where"],
            (
                "It waited for gift-note-in-export, which was dropped, so the result "
                f"it waited for never came. Type “start {self.ORDER} now” to start it "
                f"without that result, or /lem drop {self.ORDER} to end it, in any Lem "
                "session of this repository."
            ),
        )
        # the task's own card says where he answers as the row does, not "tell the
        # task's session", since none runs
        self.assertEqual(
            cast("dict", bm.waits_for(m.by_slug[self.ORDER], rows))["where"],
            say["where"],
        )

    def test_the_task_waits_for_him_on_every_view_of_the_board(self) -> None:
        m = model(*self.gift("dropped"), self.QUEUED)
        m.sessions = {}
        t = m.by_slug[self.ORDER]
        say = bm.wait_say(bm.waits_of(m)[0])
        # the kanban, the summary's count, the Overview's eyebrow and its "Where you
        # answer" agree with the row
        self.assertEqual(
            (t.for_owner, t.lane, [x.slug for x in m.for_owner], bm.who_acts(t)),
            (True, "you", [self.ORDER], "You act"),
        )
        self.assertEqual(bm.answer_of(t), say["where"])
        # the Overview's headline says what the row says, under "You act": it waits for
        # his word, not for a task
        self.assertEqual(bm.now_head(t), say["verb"])
        # behind a task that still runs, Lem holds it
        runs = model(*self.gift("building"), self.QUEUED).by_slug[self.ORDER]
        self.assertEqual(
            (runs.for_owner, runs.lane, bm.who_acts(runs), bm.now_head(runs)),
            (False, "build", "Lem acts", "Waits for another task"),
        )

    def test_a_row_of_another_kind_leaves_where_he_answers_to_the_task_state(
        self,
    ) -> None:
        # a breaker whose task has no session: the session's row does not take the
        # breaker's words away, and says first that a session is to be opened
        m = model(state(0, "building", "task 2 of 3"), Breakers.STOP, Breakers.HELD)
        m.sessions = {}
        t = m.tasks[0]
        rows = bm.waits_of(m)
        self.assertEqual([w["kind"] for w in rows], ["session", "breaker"])
        self.assertEqual(
            cast("dict", bm.waits_for(t, rows))["where"],
            f"{bm.wait_say(rows[0])['where']} {bm.answer_of(t)}",
        )
        self.assertIn(
            "/lem park gift-note", cast("dict", bm.waits_for(t, rows))["where"]
        )

    def test_a_need_gets_the_same_row(self) -> None:
        need = state(
            5,
            "queued",
            "it needs the gift note column that gift-note-in-export adds",
            "after: gift-note-in-export",
            task=self.ORDER,
        )
        rows = bm.waits_of(model(*self.gift("dropped"), need))
        self.assertEqual(
            [(w["key"], bm.wait_say(w)["start"]) for w in rows],
            [(f"after_dropped:{self.ORDER}", f"start {self.ORDER} now")],
        )

    def test_no_row_behind_a_task_that_runs_or_ended_with_its_result(self) -> None:
        for status in ("building", "landed", "answered"):
            m = model(*self.gift(status), self.QUEUED)
            self.assertEqual(
                [w["key"] for w in bm.waits_of(m) if w["t"].slug == self.ORDER],
                [],
                status,
            )

    def test_the_row_is_gone_after_his_word(self) -> None:
        # "start it": the queued block again with each line but `after:` (task 2 of the
        # plan writes it), then the start
        started = state(
            40,
            "queued",
            'the owner\'s order: "After gift-note-in-export"',
            "type: feat, because a new order",
            "then: the interview",
            'the owner\'s order was removed: "start export-notes-in-order now"',
            task=self.ORDER,
        )
        building = state(41, "building", "the interview runs", task=self.ORDER)
        dropped = state(40, "dropped", "the owner dropped it", task=self.ORDER)
        for word in ((started,), (started, building), (dropped,)):
            m = model(*self.gift("dropped"), self.QUEUED, *word)
            m.sessions = {}
            self.assertEqual(
                [w["key"] for w in bm.waits_of(m) if w["kind"] == "after_dropped"],
                [],
                word[-1]["status"],
            )


PULL_12 = "https://github.com/acme/shop/pull/12"


def report_dates() -> list[dict]:
    """The 60 events of `report-dates`, which landed with pull request 12 (criterion 2
    of the task old-task-events-summarized): its interview and its criteria of the
    standard track, its build, 50 checks, a careful review, a green proposal, the open
    pull request, its merge review and its end."""
    rd = "report-dates"
    events = [
        ev(
            0,
            "task.mode",
            rd,
            mode="alone",
            by="lem",
            words="the night of 2026-11-20",
            was="with-owner",
        ),
        {
            **state(
                1,
                "held",
                "the interview waits for the owner",
                "type: feat, because the report shows no dates",
                task=rd,
            ),
            "ask": "Dates on the report.",
        },
        ev(
            1.5,
            "task.criteria",
            rd,
            size="full",
            why="the report every merchant reads",
            digest="d1",
            criteria=["Each report shows its dates."],
        ),
        {
            **state(
                2, "building", "lead: session", "plan committed with 2 tasks", task=rd
            ),
            "branch": "feat/report-dates",
            "head": "abc1234",
            "subject": "feat: dates",
        },
    ]
    events += [
        ev(
            3 + n / 10,
            "gate",
            rd,
            command=f"check {n}",
            exit=0,
            last="ok",
            tip="abc1234",
        )
        for n in range(50)
    ]
    events += [
        ev(
            10,
            "review",
            rd,
            attempt=1,
            round=1,
            of=1,
            kind="read",
            verdict="clean",
            must_fix=0,
            should=0,
            nit=0,
            tip="abc1234",
            careful=True,
            careful_why="it changes the report every merchant reads",
        ),
        ev(11, "proposed", rd, green=True, not_green=[], tip="abc1234"),
        state(
            12,
            "open",
            "the pull request waits for its merge",
            f"pull request: {PULL_12}",
            "green",
            task=rd,
        ),
        ev(
            13,
            "session.transcript",
            rd,
            claude="c1",
            transcript="/t/c1.jsonl",
            source="startup",
        ),
        ev(
            14,
            "merge.review",
            rd,
            verdict="merge",
            calls=False,
            why="it reads well",
            by="claude",
            tip="abc1234",
        ),
        state(15, "landed", "main: pull request 12 is merged", task=rd),
    ]
    return events


def summarized(events: list[dict], *slugs: str) -> list[dict]:
    """EVENTS with the events of each of SLUGS replaced by its one summary, in the place
    of its newest event, as `lem project prune` writes it (project.py `summary_of`)."""
    from lem import project

    out = list(events)
    for slug in slugs:
        mine = [e for e in out if e.get("task") == slug]
        at_ = max(i for i, e in enumerate(out) if e.get("task") == slug)
        summary = project.summary_of(slug, mine, NOW)
        out = [
            summary if i == at_ else e
            for i, e in enumerate(out)
            if i == at_ or e.get("task") != slug
        ]
    return out


class Summary(unittest.TestCase):
    """A task whose events became one summary reads on the board as it did before
    (criterion 2 of the task old-task-events-summarized), and the board's reader of the
    log reads a summarized log once and whole (criterion 4)."""

    OTHERS = [
        state(
            20,
            "queued",
            "it starts after report-dates",
            "after: report-dates",
            task="report-dates-in-export",
        ),
        state(
            0,
            "building",
            "small change: one builder",
            "type: fix, because a typo",
            task="card-foot",
        ),
        state(16, "dropped", "the owner dropped it", task="card-foot"),
        state(
            21,
            "queued",
            "it starts after card-foot",
            "after: card-foot",
            task="card-foot-after",
        ),
        state(
            4,
            "building",
            "an investigator finds the answer",
            "investigation: question",
            task="why-slow",
        ),
        ev(
            8,
            "investigation",
            "why-slow",
            type="question",
            call="answer",
            line="the export reads every order twice",
            where="export.py",
        ),
        state(9, "answered", "the report is investigation.md", task="why-slow"),
        state(30, "building", "lead: builder", task="gift-note"),
    ]

    @staticmethod
    def facts(t: "bm.Task") -> tuple:
        proposal = {k: v for k, v in (t.proposal or {}).items() if k != "order"}
        return (
            t.status,
            t.info,
            t.since,
            t.first,
            t.last_ts,
            t.closed,
            t.lane,
            t.shown,
            t.more,
            bm.card_line(t, bm.LANE[t.lane]),
            t.type,
            t.ask,
            t.branch,
            t.lead,
            bm.lead_of(t),
            bm.careful_of(t),
            bm.pr_of(t),
            bm.is_green(t),
            bm.verdict_of(t),
            proposal,
            t.investigation,
        )

    def test_an_old_ended_tasks_card_and_its_followers_read_the_same_after_its_events_became_one_summary(
        self,
    ) -> None:
        log = sorted(report_dates() + self.OTHERS, key=lambda e: e["ts"])
        self.assertEqual(sum(1 for e in log if e["task"] == "report-dates"), 60)
        before = model(*log)
        after = model(*summarized(log, "report-dates", "card-foot", "why-slow"))
        self.assertEqual(
            [e["event"] for e in after.events if e["task"] == "report-dates"],
            ["task.summary"],
        )

        def card(m: "bm.Model", slug: str) -> str:
            t = m.by_slug[slug]
            return str(
                pages.task_card(
                    pages.Ctx(
                        host="h", workspace="w", model=m, asset=lambda name: name
                    ),
                    t,
                    bm.LANE[t.lane],
                )
            )

        rd = before.by_slug["report-dates"]
        # criterion 2.1: landed, the time of its end, its last line, its type, green,
        # and pull request 12
        shown = card(before, "report-dates")
        for said in (
            "s-landed",
            f'data-ago="{bm.at(ev(15, "x")["ts"])}"',
            "Landed: main: pull request 12 is merged",
            ">feat<",
            ">green<",
            "#12",
            "careful",
            "plan talk",
        ):
            self.assertIn(said, shown)
        self.assertEqual(
            (rd.status, rd.since, cast("dict", bm.pr_of(rd))["n"]),
            ("landed", bm.at(ev(15, "x")["ts"]), "12"),
        )
        # criterion 2.2: the same card, word for word, and the same facts its
        # board reads
        for slug in ("report-dates", "card-foot", "why-slow"):
            self.assertIsNotNone(after.by_slug[slug].summary, slug)
            self.assertEqual(
                self.facts(after.by_slug[slug]), self.facts(before.by_slug[slug]), slug
            )
            self.assertEqual(card(after, slug), card(before, slug), slug)
        self.assertEqual(
            [t.slug for t in after.lane["done"]], [t.slug for t in before.lane["done"]]
        )
        # a task queued after it still starts, and one queued after a dropped one still
        # waits for his word
        for m in (before, after):
            self.assertTrue(bm.after_ended(m.by_slug["report-dates-in-export"], m))
            self.assertTrue(bm.after_dropped(m.by_slug["card-foot-after"], m))
            self.assertEqual(m.by_slug["card-foot-after"].lane, "you")
        # the activity says what the one event stands for
        said = bm.describe(
            next(e for e in after.events if e["task"] == "report-dates"), after
        )
        self.assertEqual(said["head"], "Its events became one summary")
        self.assertTrue(
            said["text"].startswith(
                "60 events in one event that keeps the task's status, its end and its "
                "pull request: nothing of the task happened for "
                "state.keep_days days after its end"
            )
        )

    def test_a_summary_with_a_newer_state_dates_since_from_the_run_its_past_began(
        self,
    ) -> None:
        log = summarized(
            sorted(report_dates() + self.OTHERS, key=lambda e: e["ts"]), "report-dates"
        )
        t = model(
            *log,
            state(
                40,
                "landed",
                "main: pull request 12 is merged, and the session cleaned up",
                task="report-dates",
            ),
        ).by_slug["report-dates"]
        self.assertEqual(
            (t.status, t.since, t.first, cast("dict", bm.pr_of(t))["n"]),
            ("landed", bm.at(ev(15, "x")["ts"]), bm.at(ev(1, "x")["ts"]), "12"),
        )

    def test_a_summary_keeps_the_path_of_each_transcript_of_the_task_once_in_the_logs_order(
        self,
    ) -> None:
        # lem_tokens reads them by each transcript's first prompt, so a fork of another
        # task logged here still counts for that task
        from lem import project

        def logged(minute: float, name: str, task: str = "report-dates") -> dict:
            return ev(
                minute,
                "session.transcript",
                task,
                claude=name,
                transcript=f"/t/{name}.jsonl",
                source="startup",
            )

        events = [
            state(1, "building", "lead: builder", task="report-dates"),
            logged(2, "c1"),
            logged(3, "6fe214ec"),
            logged(4, "c1"),
            state(5, "landed", "main: pull request 12 is merged", task="report-dates"),
        ]
        summary = project.summary_of("report-dates", events, NOW)
        self.assertEqual(summary["transcripts"], ["/t/c1.jsonl", "/t/6fe214ec.jsonl"])
        # a summary with newer events: the old summary's paths first, then each newer
        # one not yet named
        again = project.summary_of(
            "report-dates",
            [
                summary,
                logged(6, "6fe214ec"),
                logged(7, "c2"),
                state(
                    8, "landed", "main: pull request 12 is merged", task="report-dates"
                ),
            ],
            NOW,
        )
        self.assertEqual(
            again["transcripts"], ["/t/c1.jsonl", "/t/6fe214ec.jsonl", "/t/c2.jsonl"]
        )

    def test_the_reader_reads_a_log_that_prune_replaced_once_and_whole(self) -> None:
        from unittest import mock

        def lines(events: list[dict]) -> str:
            return "".join(json.dumps(e) + "\n" for e in events)

        log_events = sorted(
            [*report_dates(), state(30, "building", "lead: builder")],
            key=lambda e: e["ts"],
        )
        with tempfile.TemporaryDirectory() as tmp:
            log, new = Path(tmp) / "events.jsonl", Path(tmp) / "events.new"
            log.write_text(lines(log_events))
            reader = bm.Reader(Path(tmp), Path(tmp))
            reader.read_log()
            self.assertEqual(len(reader.events), 61)
            first = reader.log_id()
            # gift-note writes `ready` into the old file, and prune writes the new log
            # with it after the summary
            ready = state(31, "ready", "the build is done")
            with log.open("a") as out:
                out.write(json.dumps(ready) + "\n")
            new.write_text(lines([*summarized(log_events, "report-dates"), ready]))
            # the replace lands between the reader's look at the log and its read of it
            real_open = Path.open

            def open_after_replace(path: Path, *args: Any, **kwargs: Any) -> IO:  # noqa: ANN401 - it stands in for Path.open and passes on what it is given
                if path == log and new.exists():
                    new.replace(log)
                return real_open(path, *args, **kwargs)

            with mock.patch.object(Path, "open", open_after_replace):
                reader.read_log()
            m = bm.derive(reader.events, [], NOW)
            self.assertEqual(
                [e["event"] for e in reader.events if e["task"] == "report-dates"],
                ["task.summary"],
            )
            self.assertEqual(m.by_slug["gift-note"].status, "ready")
            self.assertEqual([t.slug for t in m.lane["done"]], ["report-dates"])
            self.assertEqual(
                len(reader.events),
                len({json.dumps(e, sort_keys=True) for e in reader.events}),
                "no event twice",
            )
            self.assertEqual(reader.log_id(), bm.log_version(log.stat().st_ino, 3))
            self.assertNotEqual(reader.log_id(), first)


class SummarizedBoard(unittest.TestCase):
    """The board of a task whose events became one summary (the task
    old-task-events-summarized, decision 2): its header says the same status, end and
    pull request as before; its Overview opens with one card that says so, what the
    summary keeps and what its folder holds, from the folder (the task
    an-ended-task-s-records-stay-on-the-machine-for-ever, criterion 6); each other tab
    says its detail went with the events, and no section is drawn empty."""

    def boards(self) -> tuple["bm.Model", "bm.Model"]:
        log = report_dates()
        return model(*log), model(*summarized(log, "report-dates"))

    @staticmethod
    def ctx(
        m: "bm.Model",
        tab: str = "overview",
        folder: dict | None = None,
        keep_days: int | None = 30,
    ) -> "pages.Ctx":
        ctx = pages.Ctx(
            host="h",
            workspace="w",
            model=m,
            asset=lambda name: name,
            task="report-dates",
            tab=tab,
            keep_days=keep_days,
        )
        ctx.told = lambda slug: {
            "outcome": "Each report shows its dates.",
            "filed": None,
        }
        ctx.folder_of = lambda slug: folder
        return ctx

    @staticmethod
    def folder(*extra: str) -> tuple[tempfile.TemporaryDirectory, Path]:
        """A state folder whose task report-dates holds its small record as prune leaves
        it (its state, its request, its pull request and its lock files), and EXTRA
        beside it."""
        held = tempfile.TemporaryDirectory()
        state_dir = Path(held.name)
        directory = state_dir / "tasks" / "report-dates"
        directory.mkdir(parents=True)
        for name in (
            "state.md",
            "ask.txt",
            "task.md",
            "landing.json",
            "state.lock",
            "decisions.lock",
            *extra,
        ):
            (directory / name).parent.mkdir(parents=True, exist_ok=True)
            (directory / name).write_text("x\n", encoding="utf-8")
        return held, state_dir

    def card(self, state_dir: Path, keep_days: int | None = 30) -> str:
        _, after = self.boards()
        folder = task_pages.folder_of(state_dir, "report-dates")
        return str(
            task_pages.summary_card(
                self.ctx(after, folder=folder, keep_days=keep_days),
                after.by_slug["report-dates"],
            )
        )

    def test_a_pruned_task_whose_folder_holds_its_small_record_alone_says_what_stayed_and_that_the_rest_left(
        self,
    ) -> None:
        held, state_dir = self.folder()
        with held:
            drawn = self.card(state_dir)
        self.assertNotIn("Its files stay", drawn)
        self.assertIn(
            (
                "What stayed of its folder is its small record: its state, "
                "its request and its pull request."
            ),
            drawn,
        )
        self.assertIn(
            (
                "Its other files left: Lem keeps only this record of an ended task "
                "after 30 days in which nothing of it happened (state.keep_days, as "
                "the settings say now)."
            ),
            drawn,
        )
        self.assertNotIn("ticket", drawn)

    def test_a_pruned_task_with_a_ticket_names_its_files_and_the_number_is_the_settings_of_now(
        self,
    ) -> None:
        held, state_dir = self.folder(
            "ticket.txt", "ticket-repo.txt", "ticket-steps.txt", "resumed-from.txt"
        )
        with held:
            drawn = self.card(state_dir, keep_days=7)
        self.assertIn(
            (
                "its small record: its state, its request, its pull request, its "
                "ticket’s files and the name of the task it was resumed from."
            ),
            drawn,
        )
        self.assertIn("after 7 days in which nothing of it happened", drawn)

    def test_settings_that_do_not_read_give_no_number_on_the_card(self) -> None:
        held, state_dir = self.folder()
        with held:
            drawn = self.card(state_dir, keep_days=None)
        self.assertIn(
            (
                "after state.keep_days days in which nothing of it happened (the "
                "settings do not read now, so the board does not say that number)"
            ),
            drawn,
        )
        self.assertNotIn("30", drawn.split('id="summary-files"')[1])

    def test_a_pruned_task_whose_folder_still_holds_files_beyond_its_record_says_only_how_many(
        self,
    ) -> None:
        held, state_dir = self.folder(
            "report.md", "media/after.png", "reviews/r/round.lock"
        )
        with held:
            drawn = self.card(state_dir)
        self.assertIn(
            (
                "3 files of its folder are still there beside its small record: "
                "its state, its request and its pull request."
            ),
            drawn,
        )
        self.assertNotIn("left", drawn.split('id="summary-files"')[1])
        self.assertNotIn("Its files stay", drawn)

    def test_a_pruned_task_whose_folder_does_not_read_claims_nothing_of_its_files(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as empty:
            self.assertIsNone(task_pages.folder_of(Path(empty), "report-dates"))
            drawn = self.card(Path(empty))
        self.assertIn(
            (
                "Its folder does not read, so the board cannot say which of its "
                "files are still there."
            ),
            drawn,
        )
        self.assertNotIn("left", drawn.split('id="summary-files"')[1])

    def test_an_answered_task_names_its_report_only_while_its_folder_holds_it(
        self,
    ) -> None:
        events = [
            state(
                4,
                "building",
                "an investigator finds the answer",
                "investigation: question",
                task="why-slow",
            ),
            ev(
                8,
                "investigation",
                "why-slow",
                type="question",
                call="answer",
                line="the export reads every order twice",
                where="export.py",
            ),
            state(9, "answered", "the report is investigation.md", task="why-slow"),
        ]
        m = model(*events)
        t = m.by_slug["why-slow"]
        line = "The report is investigation.md in the task directory"
        with tempfile.TemporaryDirectory() as held:
            directory = Path(held) / "tasks" / "why-slow"
            directory.mkdir(parents=True)
            (directory / "state.md").write_text("x\n", encoding="utf-8")
            (directory / "investigation.md").write_text(
                "# Investigation\n", encoding="utf-8"
            )
            ctx = pages.Ctx(
                host="h",
                workspace="w",
                model=m,
                asset=lambda name: name,
                task="why-slow",
            )
            ctx.folder_of = lambda slug: task_pages.folder_of(Path(held), slug)
            self.assertIn(line, str(task_pages.now_card(ctx, t)))
            (directory / "investigation.md").unlink()
            drawn = str(task_pages.now_card(ctx, t))
        self.assertNotIn(line, drawn)
        self.assertIn("the export reads every order twice", drawn)

    def test_the_header_says_the_same_status_end_pull_request_and_track(self) -> None:
        import re

        before, after = self.boards()

        def said(m: "bm.Model") -> tuple[str, ...]:
            ctx = self.ctx(m)
            t = m.by_slug["report-dates"]
            facts = str(join(task_pages.facts(ctx, t, [])))
            return (
                str(task_pages.pill(ctx, t)),
                re.findall(r'<dd id="dd-pr">.*?</dd>', facts)[0],
                re.findall(r'<dd id="dd-time">.*?</dd>', facts)[0],
                str(task_pages.key_line(ctx, t)),
                re.findall(r'<dd id="dd-type">.*?</dd>', facts)[0],
            )

        self.assertEqual(said(after), said(before))
        self.assertIn("acme/shop#12", said(after)[1])
        # the Type row still says the track, from the criteria's size the summary keeps
        # (decision 21)
        self.assertIn("<b>feat</b> · standard track", said(after)[4])

    def test_the_overview_opens_with_the_summary_and_no_tab_draws_an_empty_section(
        self,
    ) -> None:
        _, after = self.boards()
        t = after.by_slug["report-dates"]
        parts = [str(x) for x in task_pages.overview_tab(self.ctx(after), t) if x]
        self.assertIn('id="summary"', parts[0])
        self.assertIn("Its 60 events became one summary:", parts[0])
        self.assertIn("state.keep_days", parts[0])
        for kept in (
            "landed",
            "pull request acme/shop#12",
            "green",
            "type feat",
            "careful: yes",
            "branch feat/report-dates",
        ):
            self.assertIn(kept, parts[0])
        self.assertIn("Artifacts", parts[0])
        self.assertTrue(
            any('id="building"' in x for x in parts),
            "What we are building reads its task.md, which stays",
        )
        self.assertFalse(
            any('id="progress"' in x for x in parts),
            "no stats whose checks, review and decisions would read as none",
        )
        for tab, went in (
            (
                "criteria",
                (
                    "Its acceptance criteria, their approval, the personas’ read and "
                    "its decisions went with its events"
                ),
            ),
            (
                "checks",
                (
                    "Its runs of the checks, its review rounds and the proposal’s "
                    "reasons went with its events"
                ),
            ),
            ("timeline", "Its timeline and its events went with its events"),
        ):
            drawn = "".join(
                str(x)
                for x in {
                    "criteria": task_pages.criteria_tab,
                    "checks": task_pages.checks_tab,
                    "timeline": task_pages.timeline_tab,
                }[tab](self.ctx(after, tab), t)
            )
            self.assertIn(f'id="went-{tab}"', drawn)
            self.assertIn(went, drawn)
            self.assertNotIn('class="empty"', drawn)
            self.assertNotIn("with no checks and no review on record", drawn)
            self.assertNotIn("with no criteria and no decision on record", drawn)
        self.assertEqual(
            task_pages.empty_reason(t, "checks"),
            "no document: what showed it went with the events, into one summary",
        )
        self.assertEqual(
            task_pages.empty_reason(t, "proposal"),
            "no document: green or not green is on the Overview",
        )

    def test_a_task_whose_events_are_whole_has_no_summary_card(self) -> None:
        before, _ = self.boards()
        t = before.by_slug["report-dates"]
        parts = [str(x) for x in task_pages.overview_tab(self.ctx(before), t) if x]
        self.assertFalse(any('id="summary"' in x for x in parts))
        self.assertTrue(any('id="progress"' in x for x in parts))


class AnsweredInSession(unittest.TestCase):
    """Which rows of "Waits for you" the owner answers in the task's own session, so
    that the row's verb goes to that session while it lives (decision 4
    of docs/plans/2026-11-22-board-cards-keyboard.md)."""

    LIVE = {"gift-note": {"live": True, "agent": True, "session": "S1"}}

    def row(
        self, *events: dict, sessions: dict | None = None, kind: str | None = None
    ) -> tuple:
        m = model(ev(0, "session.open", session="S1", name="gift-note"), *events)
        m.sessions = self.LIVE if sessions is None else sessions
        rows = [w for w in bm.waits_of(m) if kind is None or w["kind"] == kind]
        self.assertEqual(len(rows), 1, [w["kind"] for w in bm.waits_of(m)])
        w = rows[0]
        return w["kind"], bm.answered_in_session(w, m), bm.session_of_wait(w, m)

    def test_a_held_step_with_no_yes_on_the_board_goes_to_the_session(self) -> None:
        self.assertEqual(
            self.row(state(1, "held", "the interview waits for the owner")),
            ("held", True, "S1"),
        )

    def test_a_held_step_whose_yes_is_on_the_board_and_criteria_stay_on_the_board(
        self,
    ) -> None:
        interview_read = (
            state(1, "held", "the interview waits for the owner"),
            ev(5, "criteria.read", **Acts.READ),
        )
        self.assertEqual(self.row(*interview_read), ("held", False, None))
        self.assertEqual(
            self.row(state(1, "held", "the criteria wait for the owner")),
            ("criteria", False, None),
        )

    def test_a_task_its_session_stopped_goes_to_the_session(self) -> None:
        self.assertEqual(
            self.row(
                state(1, "building", "lead: builder"),
                state(5, "blocked", "a builder ended two times with no report"),
            ),
            ("blocked", True, "S1"),
        )

    def test_a_session_that_does_not_answer_goes_to_it_and_a_task_with_no_session_does_not(
        self,
    ) -> None:
        deaf = {
            "gift-note": {
                "live": True,
                "agent": True,
                "unanswered": True,
                "session": "S1",
            }
        }
        self.assertEqual(
            self.row(
                state(1, "building", "lead: builder"), sessions=deaf, kind="session"
            ),
            ("session", True, "S1"),
        )
        gone = {"gift-note": {"live": True, "agent": False, "session": "S1"}}
        self.assertEqual(
            self.row(
                state(1, "building", "lead: builder"), sessions=gone, kind="session"
            ),
            ("session", False, None),
        )

    def test_a_merge_a_breaker_a_plan_and_a_task_after_a_dropped_one_stay_on_the_board(
        self,
    ) -> None:
        self.assertEqual(self.row(state(1, "open", Merge.PR)), ("merge", False, None))
        self.assertEqual(
            self.row(state(1, "building", "task 2 of 3"), Breakers.STOP, Breakers.HELD),
            ("breaker", False, None),
        )
        self.assertEqual(
            self.row(state(1, "planned", "the plan waits for the owner")),
            ("plan", False, None),
        )
        dropped = (*AfterDropped().gift("dropped"), AfterDropped.QUEUED)
        self.assertEqual(
            self.row(*dropped, kind="after_dropped"), ("after_dropped", False, None)
        )

    def test_a_session_that_does_not_live_takes_no_jump(self) -> None:
        self.assertEqual(
            self.row(
                state(1, "held", "the interview waits for the owner"),
                sessions={},
                kind="held",
            ),
            ("held", True, None),
        )
        demo = bm.derive(
            [state(0, "held", "the interview waits for the owner")],
            [],
            NOW,
            meta={"demo": True},
        )
        self.assertEqual(bm.session_of_wait(bm.waits_of(demo)[0], demo), None)
        demo = bm.derive(
            [
                state(0, "held", "the interview waits for the owner"),
                ev(1, "session.open", session="S9", name="gift-note"),
            ],
            [],
            NOW,
            meta={"demo": True},
        )
        self.assertEqual(bm.session_of_wait(bm.waits_of(demo)[0], demo), "S9")


class Search(unittest.TestCase):
    """The rows of the search over every card (criteria 2, 4 and 5 of
    docs/plans/2026-11-22-board-card-search.md): every task of the workspace, a parked
    one and an ended one Done has no card for too, and every backlog item, in the order
    the search lists them with nothing typed, each with its chip."""

    # 2026-11-22 10:00 UTC; each event's minute counts from START, 2026-11-20 09:00 UTC
    NOW = int(datetime(2026, 11, 22, 10, 0, tzinfo=UTC).timestamp() * 1000)
    # noon UTC of 2026-11-21, which is that day on any clock from UTC-11 to UTC+11
    NOON_21 = 27 * 60
    # as board.backlog reads them: the reviewer's items after the others, a held one
    # before an undecided one
    BACKLOG = {
        "items": [
            {
                "slug": "export-in-one-query",
                "key": "export-in-one-query",
                "title": "Read the monthly export in one query",
                "worth": "later",
            },
            {"slug": "odd-item", "key": "odd-item", "title": "An item with no worth"},
            {
                "slug": "the-board-s-done-column-has-no-limit",
                "key": "the-board-s-done-column-has-no-limit",
                "title": "The board's done column has no limit",
                "worth": "yes",
            },
            {
                "slug": "a-thing-not-to-do",
                "key": "a-thing-not-to-do",
                "title": "A thing not to do",
                "worth": "no",
            },
            {
                "slug": "a-flaky-check",
                "key": "-a-flaky-check",
                "title": "A check of the export fails by chance",
                "worth": "later",
                "reviewer": True,
                "held": {"task": "flaky-export-check", "status": "building"},
            },
            {
                "slug": "export-in-one-query",
                "key": "-export-in-one-query",
                "title": "The lessons of the export",
                "worth": "later",
                "reviewer": True,
                "held": None,
            },
        ]
    }

    def events(self) -> list:
        return [
            state(0, "building", "task 1 of 3", task="refund-rounding"),
            state(
                1, "held", "the criteria wait for the owner", task="board-card-search"
            ),
            state(2, "queued", "it waits", task="clear-a-reported-deadline"),
            state(3, "landing", "the checks run", task="coupon-has-a-slug"),
            state(4, "parked", "wait for the merchants", task="old-export-fix"),
            state(
                5,
                "held",
                "the interview waits for the owner",
                task="stock-on-product-page",
            ),
            state(
                self.NOON_21,
                "landed",
                "main: pull request #41 is merged",
                task="agents-md-read-on-demand",
            ),
            *(
                state(10 + i, "landed", "merged", task=f"task-{i:02d}")
                for i in range(bm.DONE_SHOWN)
            ),
        ]

    def rows(self) -> list:
        return bm.search_rows(bm.derive(self.events(), [], self.NOW), self.BACKLOG)

    def test_criterion_4_the_order_the_columns_then_the_parked_then_every_ended_task_newest_first_then_the_backlog_by_worth(
        self,
    ) -> None:
        m = bm.derive(self.events(), [], self.NOW)
        slugs = [r["slug"] for r in bm.search_rows(m, self.BACKLOG)]
        columns = [t.slug for key in ("you", "build", "checks") for t in m.lane[key]]
        self.assertEqual(
            columns,
            [
                "board-card-search",
                "stock-on-product-page",
                "clear-a-reported-deadline",
                "refund-rounding",
                "coupon-has-a-slug",
            ],
        )
        ended = [
            "agents-md-read-on-demand",
            *(f"task-{i:02d}" for i in reversed(range(bm.DONE_SHOWN))),
        ]
        # the reviewer's items before the others, the undecided one first; an item of
        # each folder with one stem is two rows
        self.assertEqual(
            slugs,
            [
                *columns,
                "old-export-fix",
                *ended,
                "-export-in-one-query",
                "-a-flaky-check",
                "the-board-s-done-column-has-no-limit",
                "export-in-one-query",
                "odd-item",
                "a-thing-not-to-do",
            ],
        )
        # with nothing typed, the search lists the tasks that have not ended: the
        # columns', then the parked one
        self.assertEqual(
            [r["slug"] for r in bm.search_rows(m, self.BACKLOG) if r["open"]],
            [*columns, "old-export-fix"],
        )

    def test_criterion_2_every_task_a_parked_one_and_an_ended_one_done_draws_no_card_for_and_every_backlog_item(
        self,
    ) -> None:
        m = bm.derive(self.events(), [], self.NOW)
        rows = {r["title"]: r for r in bm.search_rows(m, self.BACKLOG)}
        self.assertEqual(len(m.lane["done"]), bm.DONE_SHOWN + 1)
        self.assertIn("task-00", [t.slug for t in bm.done_older(m)])
        for title, kind in (
            ("Board card search", "task"),
            ("Old export fix", "task"),
            ("Task 00", "task"),
            ("The board's done column has no limit", "item"),
        ):
            self.assertEqual(rows[title]["kind"], kind, title)
        self.assertEqual(len(rows), len(m.tasks) + len(self.BACKLOG["items"]))
        # no backlog read: the tasks alone
        self.assertEqual(len(bm.search_rows(m, None)), len(m.tasks))

    def test_criterion_5_each_chip_says_its_place_and_its_state_in_the_color_of_its_column(
        self,
    ) -> None:
        rows = {r["title"]: (r["chip"], r["actor"]) for r in self.rows()}
        self.assertEqual(rows["Board card search"], ("Waits for you · held", "you"))
        self.assertEqual(
            rows["Clear a reported deadline"], ("Building · queued", "lead")
        )
        self.assertEqual(
            rows["Coupon has a slug"], ("Checks and review · landing", "gate")
        )
        self.assertEqual(rows["Old export fix"], ("parked", "quiet"))
        self.assertEqual(
            rows["Agents md read on demand"], ("landed 2026-11-21", "done")
        )
        self.assertEqual(
            rows["The board's done column has no limit"],
            ("Backlog · worth: yes", "gate"),
        )
        self.assertEqual(
            rows["Read the monthly export in one query"],
            ("Backlog · worth: later", "you"),
        )
        self.assertEqual(
            rows["An item with no worth"], ("Backlog · worth: unset", "quiet")
        )
        self.assertEqual(
            rows["The lessons of the export"], ("Backlog · undecided", "you")
        )
        self.assertEqual(
            rows["A check of the export fails by chance"],
            ("Backlog · held by flaky-export-check", "lead"),
        )

    def test_the_count_on_the_backlog_key_is_the_reviewer_s_items_no_task_holds(
        self,
    ) -> None:
        # criterion 6 of docs/plans/2026-11-23-scheduled-runs-one-branch.md: an item of
        # the backlog folder is not counted, nor a held one
        self.assertEqual(bm.undecided(self.BACKLOG), 1)
        self.assertEqual(bm.undecided({"items": self.BACKLOG["items"][:4]}), 0)
        self.assertIsNone(bm.undecided(None))

    def test_criterion_4_a_refuted_item_of_the_reviewer_is_not_counted_and_is_under_decided_against(
        self,
    ) -> None:
        # criterion 4 of docs/plans/2026-11-23-backlog-refuted-items-and-jev.md: 2
        # reviewer's items that wait for the owner and 1 refuted give 2 on the key, and
        # the view lists all 3
        def mine(stem: str, worth: str) -> dict:
            return {
                "slug": stem,
                "key": f"-{stem}",
                "title": stem,
                "worth": worth,
                "reviewer": True,
                "held": None,
            }

        backlog = {
            "items": [
                mine("the-board-s-colors", "later"),
                mine("run-make-lint-before-each-commit", "no"),
                mine("a-flaky-check", "later"),
            ]
        }
        self.assertEqual(bm.undecided(backlog), 2)
        self.assertEqual(
            [it["key"] for it in bm.reviewer_items(backlog["items"])],
            ["-the-board-s-colors", "-a-flaky-check"],
        )
        self.assertEqual(
            [it["key"] for it in bm.worth_items(backlog["items"], "no")],
            ["-run-make-lint-before-each-commit"],
        )
        rows = {
            r["slug"]: r["chip"]
            for r in bm.search_rows(bm.derive(self.events(), [], self.NOW), backlog)
            if r["kind"] == "item"
        }
        self.assertEqual(
            rows,
            {
                "-the-board-s-colors": "Backlog · undecided",
                "-a-flaky-check": "Backlog · undecided",
                "-run-make-lint-before-each-commit": "Backlog · worth: no",
            },
        )


class StoppedSession(unittest.TestCase):
    """The guard of a stopped session (`stop_due`), on the events of 2026-11-22
    (merge-leaves-board-lock, #37): its checks ended at 10:54, its session stayed live
    with an agent in its pane, and nothing woke it until the owner found it at 15:37.
    The step due at each look: the status message at 11:39, the restart at 11:49, and
    when the fresh session stops too, the stop, once. The row of "Waits for you" for a
    stop, and the timeline's words, are StoppedRow's."""

    def ev(
        self: "StoppedSession | StoppedRow", hhmm: str, event: str, **fields: object
    ) -> dict:
        return {
            "ts": f"2026-11-22T{hhmm}{'' if hhmm.count(':') == 2 else ':00'}Z",
            "event": event,
            "task": "gift-note",
            **fields,
        }

    @staticmethod
    def ms(hhmm: str) -> int:
        text = f"2026-11-22T{hhmm}{'' if hhmm.count(':') == 2 else ':00'}Z"
        return int(
            datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ")
            .replace(tzinfo=UTC)
            .timestamp()
            * 1000
        )

    def model(
        self: "StoppedSession | StoppedRow",
        *events: dict,
        at: str,
        session: str = "S1",
        sign: str | None = "2026-11-22T10:15:42Z",
        shell: bool = False,
        signs: bool = True,
        live: bool = True,
    ) -> "bm.Model":
        m = bm.derive(list(events), [], self.ms(at))
        m.sessions = {
            "gift-note": {
                "live": live,
                "agent": live,
                "unanswered": False,
                "session": session,
                "name": "gift-note",
                "sign": sign,
                "shell": shell,
                "signs": signs,
            }
        }
        return m

    def landing(self: "StoppedSession | StoppedRow") -> tuple:
        return (
            self.ev(
                "01:33",
                "session.open",
                session="S1",
                name="gift-note",
                phase="land",
                why="handoff",
            ),
            self.ev(
                "10:15",
                "task.state",
                status="landing",
                text="the base moved: the checks run again",
                lines=[],
            ),
            self.ev("10:18", "gate.start", tip="5ccc53d36", commands=1),
            self.ev(
                "10:22",
                "gate",
                command="bash tests/all.sh",
                exit=0,
                last="all suites passed",
                tip="5ccc53d36",
            ),
            self.ev(
                "10:54", "gate.end", result="passed", seconds=2156, tip="5ccc53d36"
            ),
        )

    def woken(self: "StoppedSession | StoppedRow", **fields: object) -> tuple:
        # `unread=True` is the message `cmd_wake` logs when the signs it read in the
        # task's lock do not read
        return (
            *self.landing(),
            self.ev("11:39", "session.wake", session="S1", why="status", **fields),
        )

    def restarted(self: "StoppedSession | StoppedRow") -> tuple:
        return (
            *self.woken(),
            self.ev(
                "11:49",
                "session.open",
                session="S2",
                name="gift-note",
                phase="land",
                why="stopped",
            ),
            self.ev("11:49", "session.wake", session="S1", why="replaced"),
        )

    def due(self, *events: dict, at: str, **given: Any) -> tuple | None:  # noqa: ANN401 - passed on whole to model, whose parameters type them
        m = self.model(*events, at=at, **given)
        found = bm.stop_due(m.by_slug["gift-note"], m)
        return (found["step"], found["session"], found["from"]) if found else None

    def test_45_minutes_after_the_newest_sign_the_status_message_is_due(self) -> None:
        self.assertIsNone(self.due(*self.landing(), at="11:38:59"))
        # the newest sign is the end of the checks, newer than the session's own last
        # turn at 10:15
        self.assertEqual(
            self.due(*self.landing(), at="11:39"), ("status", "S1", self.ms("10:54"))
        )
        self.assertEqual(
            self.due(*self.landing(), at="15:37"), ("status", "S1", self.ms("10:54"))
        )
        # a newer turn of the session (or of a subagent) moves the clock
        self.assertIsNone(
            self.due(*self.landing(), at="11:39", sign="2026-11-22T11:30:00Z")
        )
        self.assertEqual(
            self.due(*self.landing(), at="12:15", sign="2026-11-22T11:30:00Z"),
            ("status", "S1", self.ms("11:30")),
        )

    def test_a_shell_command_that_runs_is_work_and_a_session_that_is_not_live_gets_nothing(
        self,
    ) -> None:
        # the checks of a landing run for 50 minutes with no event: their shell command
        # is the sign
        checks = (*self.landing()[:3],)
        self.assertIsNone(self.due(*checks, at="11:08", shell=True))
        self.assertEqual(
            self.due(*checks, at="11:08"), ("status", "S1", self.ms("10:18"))
        )
        self.assertIsNone(self.due(*self.landing(), at="15:37", live=False))
        m = self.model(*self.landing(), at="15:37")
        m.sessions = None
        self.assertIsNone(bm.stop_due(m.by_slug["gift-note"], m))
        demo = bm.derive(
            list(self.landing()), [], self.ms("15:37"), meta={"demo": True}
        )
        demo.sessions = self.model(*self.landing(), at="15:37").sessions
        self.assertIsNone(bm.stop_due(demo.by_slug["gift-note"], demo))

    def test_the_restart_is_due_10_minutes_after_the_message_with_no_sign(self) -> None:
        self.assertIsNone(self.due(*self.woken(), at="11:48:59"))
        self.assertEqual(
            self.due(*self.woken(), at="11:49"), ("restart", "S1", self.ms("11:39"))
        )

    def test_a_sign_in_the_10_minutes_ends_that_stop(self) -> None:
        self.assertIsNone(
            self.due(*self.woken(), at="11:49", sign="2026-11-22T11:41:00Z")
        )
        # a work event answers too; the session's answer in the second of the message
        # counts as after it
        self.assertIsNone(
            self.due(*self.woken(), self.ev("11:44", "review.start"), at="11:49")
        )
        self.assertIsNone(
            self.due(*self.woken(), at="11:49", sign="2026-11-22T11:39:00Z")
        )
        # the guard's own records and the owner's click are no work
        self.assertEqual(
            cast(
                "tuple",
                self.due(
                    *self.woken(),
                    self.ev("11:45", "board.act", act="open", via="board"),
                    at="11:49",
                ),
            )[0],
            "restart",
        )
        # a later stop of 45 minutes is a new stop, with a message of its own
        self.assertEqual(
            self.due(*self.woken(), at="12:26", sign="2026-11-22T11:41:00Z"),
            ("status", "S1", self.ms("11:41")),
        )

    def test_the_fresh_sessions_clock_starts_at_its_open(self) -> None:
        # the look 20 seconds after the restart, and one 10 minutes after the old
        # message: nothing
        self.assertIsNone(
            self.due(*self.restarted(), at="11:49:20", session="S2", sign=None)
        )
        self.assertIsNone(
            self.due(*self.restarted(), at="11:59", session="S2", sign=None)
        )
        self.assertEqual(
            self.due(*self.restarted(), at="12:34", session="S2", sign=None),
            ("status", "S2", self.ms("11:49")),
        )
        self.assertEqual(
            self.due(
                *self.restarted(), at="12:37", session="S2", sign="2026-11-22T11:52:00Z"
            ),
            ("status", "S2", self.ms("11:52")),
        )

    def test_a_fresh_session_that_stops_too_is_logged_once_and_not_restarted(
        self,
    ) -> None:
        again = (
            *self.restarted(),
            self.ev("12:37", "session.wake", session="S2", why="status"),
        )
        self.assertIsNone(
            self.due(*again, at="12:46", session="S2", sign="2026-11-22T11:52:00Z")
        )
        self.assertEqual(
            self.due(*again, at="12:47", session="S2", sign="2026-11-22T11:52:00Z"),
            ("stopped", "S2", self.ms("12:37")),
        )
        stopped = (*again, self.ev("12:47", "session.stopped", session="S2"))
        for at in ("12:47:20", "13:40", "17:00"):
            self.assertIsNone(
                self.due(*stopped, at=at, session="S2", sign="2026-11-22T11:52:00Z"), at
            )

    def test_a_work_event_after_the_restart_makes_a_new_restart_possible(self) -> None:
        worked = (
            *self.restarted(),
            self.ev("11:55", "gate.start", tip="77aa", commands=1),
            self.ev("11:58", "gate.end", result="passed", tip="77aa"),
            self.ev("12:43", "session.wake", session="S2", why="status"),
        )
        self.assertEqual(
            self.due(*worked, at="12:53", session="S2", sign="2026-11-22T11:58:00Z"),
            ("restart", "S2", self.ms("12:43")),
        )

    def test_a_task_out_of_building_ready_and_landing_gets_nothing(self) -> None:
        opened = self.ev(
            "01:33",
            "session.open",
            session="S1",
            name="gift-note",
            phase="build",
            why="handoff",
        )
        lines = {
            "held": "the criteria wait for the owner",
            "queued": "after: other-task",
            "planned": "the plan waits for the owner",
            "blocked": "a builder ended two times with no report",
            "open": "PR #12 opened",
            "parked": "the owner parked it",
            "landed": "merged as #12",
            "dropped": "the owner dropped it",
            "answered": "the answer is in the report",
        }
        for status, text in lines.items():
            self.assertIsNone(
                self.due(
                    opened,
                    self.ev("10:15", "task.state", status=status, text=text, lines=[]),
                    at="15:37",
                ),
                status,
            )
        for status in bm.GUARDED:
            self.assertIsNotNone(
                self.due(
                    opened,
                    self.ev(
                        "10:15",
                        "task.state",
                        status=status,
                        text="task 2 of 5",
                        lines=[],
                    ),
                    at="15:37",
                ),
                status,
            )

    def test_a_stop_stands_until_a_work_event_or_a_session_opens(self) -> None:
        stopped = (
            *self.restarted(),
            self.ev("12:37", "session.wake", session="S2", why="status"),
            self.ev("12:47", "session.stopped", session="S2"),
        )

        def task(*events: dict) -> "bm.Task":
            return bm.derive(list(events), [], self.ms("13:00")).by_slug["gift-note"]

        self.assertEqual(cast("dict", bm.stop_stands(task(*stopped)))["session"], "S2")
        self.assertEqual(
            cast(
                "dict",
                bm.stop_stands(
                    task(
                        *stopped, self.ev("12:50", "board.act", act="open", via="board")
                    )
                ),
            )["session"],
            "S2",
        )
        self.assertIsNone(
            bm.stop_stands(
                task(
                    *stopped,
                    self.ev(
                        "12:50",
                        "session.open",
                        session="S3",
                        name="gift-note",
                        phase="land",
                        why="stopped",
                    ),
                )
            )
        )
        self.assertIsNone(
            bm.stop_stands(task(*stopped, self.ev("12:50", "review.start")))
        )
        self.assertIsNone(bm.stop_stands(task(*self.restarted())))

    def test_a_quiet_task_whose_signs_do_not_read_is_woken_or_shown(self) -> None:
        # #37 as it ran: its session opened at 01:33, before the hook wrote `session`
        # into a transcript record, so `lem session list` read "signs": false for it all
        # day; at 15:37, nearly five hours after the checks ended, the owner's request
        # (2026-11-22) wants the task woken or shown to him
        m = self.model(*self.landing(), at="15:37", sign=None, signs=False)
        t = m.by_slug["gift-note"]
        rows = [w["kind"] for w in bm.waits_of(m) if w["t"] is t]
        self.assertTrue(
            bm.stop_due(t, m) is not None or rows,
            (
                "a live session quiet since 10:54 whose signs do not read gets no step "
                "of the guard and no row"
            ),
        )

    def unread(self) -> dict:
        # the signs of #37 as `lem session list` gave them: no record of its own, so
        # nothing read
        return {"sign": None, "signs": False}

    def test_criterion_1_signs_that_do_not_read_get_the_message_45_minutes_after_the_newest_event(
        self,
    ) -> None:
        self.assertIsNone(self.due(*self.landing(), at="11:38:59", **self.unread()))
        self.assertEqual(
            self.due(*self.landing(), at="11:39", **self.unread()),
            ("status", "S1", self.ms("10:54")),
        )
        # a turn's time read beside signs that do not read is no sign of work: the clock
        # stays at 10:54
        self.assertEqual(
            self.due(
                *self.landing(), at="11:39", sign="2026-11-22T11:30:00Z", signs=False
            ),
            ("status", "S1", self.ms("10:54")),
        )
        # no agent in the pane, or a shell command that runs, still gets nothing
        m = self.model(*self.landing(), at="11:39", **self.unread())
        cast("dict", m.sessions)["gift-note"]["agent"] = None
        self.assertIsNone(bm.stop_due(m.by_slug["gift-note"], m))
        self.assertIsNone(
            self.due(*self.landing(), at="11:39", sign=None, signs=False, shell=True)
        )

    def test_criterion_2_ten_minutes_after_the_message_signs_that_do_not_read_give_the_stop_never_a_restart(
        self,
    ) -> None:
        self.assertIsNone(
            self.due(*self.woken(unread=True), at="11:48:59", **self.unread())
        )
        self.assertEqual(
            self.due(*self.woken(unread=True), at="11:49", **self.unread()),
            ("stopped", "S1", self.ms("11:39")),
        )
        self.assertEqual(
            self.due(*self.woken(unread=True), at="15:37", **self.unread()),
            ("stopped", "S1", self.ms("11:39")),
        )
        stopped = (
            *self.woken(unread=True),
            self.ev("11:49", "session.stopped", session="S1", unread=True),
        )
        for at in ("11:49:20", "11:50", "17:00"):
            self.assertIsNone(self.due(*stopped, at=at, **self.unread()), at)
        # at 11:50 the signs read again, with the turn of 10:15: a logged stop waits for
        # the owner, so no restart
        self.assertIsNone(self.due(*stopped, at="11:50"))
        self.assertEqual(
            cast(
                "dict",
                bm.stop_stands(self.model(*stopped, at="11:50").by_slug["gift-note"]),
            )["session"],
            "S1",
        )

    def test_criterion_3_a_work_event_ends_the_wait_and_the_guards_own_message_is_none(
        self,
    ) -> None:
        block = self.ev(
            "11:42",
            "task.state",
            status="landing",
            text="the pull request waits for its checks",
            lines=[],
        )
        self.assertIsNone(
            self.due(*self.woken(unread=True), block, at="11:49", **self.unread())
        )
        self.assertIsNone(
            self.due(*self.woken(unread=True), block, at="12:26:59", **self.unread())
        )
        self.assertEqual(
            self.due(*self.woken(unread=True), block, at="12:27", **self.unread()),
            ("status", "S1", self.ms("11:42")),
        )
        m = self.model(*self.woken(unread=True), block, at="11:49", **self.unread())
        self.assertEqual(
            [w["kind"] for w in bm.waits_of(m) if w["t"].slug == "gift-note"], []
        )
        # a state block logged after the look at 11:49 but before the stop's record: the
        # log's order decides
        raced = (
            *self.woken(unread=True),
            self.ev(
                "11:49",
                "task.state",
                status="landing",
                text="the pull request waits for its checks",
                lines=[],
            ),
            self.ev("11:49", "session.stopped", session="S1", unread=True),
        )
        m = self.model(*raced, at="11:50", **self.unread())
        t = m.by_slug["gift-note"]
        self.assertEqual(
            (
                bm.stop_stands(t),
                bm.stopped_of(t, m),
                [w["kind"] for w in bm.waits_of(m) if w["t"] is t],
            ),
            (None, None, []),
        )
        self.assertIsNone(self.due(*raced, at="12:33:59", **self.unread()))
        self.assertEqual(
            self.due(*raced, at="12:34", **self.unread()),
            ("status", "S1", self.ms("11:49")),
        )

    def test_each_clock_counts_only_the_status_message_it_sent(self) -> None:
        # the unread clock's message at 11:39, and at 11:49 the signs read again with a
        # turn at 11:30: the readable clock counts from that turn, so no fresh session
        # 19 minutes after it, and its own message at 12:15
        unread = self.woken(unread=True)
        self.assertIsNone(self.due(*unread, at="11:49", sign="2026-11-22T11:30:00Z"))
        self.assertEqual(
            self.due(*unread, at="12:15", sign="2026-11-22T11:30:00Z"),
            ("status", "S1", self.ms("11:30")),
        )
        # the readable clock's message at 11:39, turns until 12:30, and at 12:40 the
        # signs do not read: the unread clock sends its own message, and logs the stop
        # only 10 minutes after it
        self.assertEqual(
            self.due(
                *self.woken(), at="12:40", sign="2026-11-22T12:30:00Z", signs=False
            ),
            ("status", "S1", self.ms("10:54")),
        )
        again = (
            *self.woken(),
            self.ev("12:40", "session.wake", session="S1", why="status", unread=True),
        )
        self.assertIsNone(
            self.due(*again, at="12:49:59", sign="2026-11-22T12:30:00Z", signs=False)
        )
        self.assertEqual(
            self.due(*again, at="12:50", sign="2026-11-22T12:30:00Z", signs=False),
            ("stopped", "S1", self.ms("12:40")),
        )
        # the message before a stop that stands counts for both clocks: a readable stop
        # and signs that no longer read give no second message and no second stop
        stopped = (
            *self.restarted(),
            self.ev("12:37", "session.wake", session="S2", why="status"),
            self.ev("12:47", "session.stopped", session="S2"),
        )
        for at in ("13:40", "17:00"):
            self.assertIsNone(
                self.due(*stopped, at=at, session="S2", sign=None, signs=False), at
            )

    def test_criterion_4_a_readable_stop_and_a_newer_turn_still_give_the_status_message(
        self,
    ) -> None:
        stopped = (
            *self.restarted(),
            self.ev("12:37", "session.wake", session="S2", why="status"),
            self.ev("12:47", "session.stopped", session="S2"),
        )
        self.assertIsNone(
            self.due(*stopped, at="13:44", session="S2", sign="2026-11-22T13:00:00Z")
        )
        self.assertEqual(
            self.due(*stopped, at="13:45", session="S2", sign="2026-11-22T13:00:00Z"),
            ("status", "S2", self.ms("13:00")),
        )

    def test_the_numbers_are_the_owners(self) -> None:
        self.assertEqual((bm.QUIET_MS, bm.ANSWER_MS), (45 * 60 * 1000, 10 * 60 * 1000))

    # A turn that a readable look saw after a status message Lem sent while it could not
    # read the session (`session.worked`). The owner's answer of 2026-11-24: "B · Log
    # the turn once: the row goes, and the clock starts again."

    def unread_stopped(self) -> tuple:
        return (
            *self.woken(unread=True),
            self.ev("11:49", "session.stopped", session="S1", unread=True),
        )

    def worked(self, hhmm: str, turn: str) -> dict:
        return self.ev(
            hhmm, "session.worked", session="S1", turn=f"2026-11-22T{turn}:00Z"
        )

    def rows(self, m: "bm.Model") -> list:
        return [w["kind"] for w in bm.waits_of(m) if w["t"].slug == "gift-note"]

    # the writer of the record, which the release after this one turns on
    @mock.patch("lem.board_model.WRITES_WORKED", True)
    def test_a_turn_read_after_an_unread_stop_is_logged_once_and_the_stop_goes(
        self,
    ) -> None:
        # the item's first run: the unread message at 11:39 and the unread stop at
        # 11:49; from 11:50 the signs read, and the session takes a turn at 11:55 with
        # no state block
        turned = {"sign": "2026-11-22T11:55:00Z"}
        logged = (*self.unread_stopped(), self.worked("11:56", "11:55"))
        m = self.model(*logged, at="11:57", **turned)
        t = m.by_slug["gift-note"]
        self.assertEqual(
            (bm.stop_stands(t), bm.stopped_of(t, m), self.rows(m)), (None, None, [])
        )
        # the look after the turn logs it; no look before the turn, nor after its
        # record, logs it
        self.assertIsNone(self.due(*self.unread_stopped(), at="11:54"))
        self.assertEqual(
            self.due(*self.unread_stopped(), at="11:56", **turned),
            ("worked", "S1", self.ms("11:55")),
        )
        for at in ("11:57", "12:39"):
            self.assertIsNone(self.due(*logged, at=at, **turned), at)
        # the clock counts from the turn: the readable clock's message at 12:40, and
        # the unread clock's too, when the signs stop reading again
        self.assertEqual(
            self.due(*logged, at="12:40", **turned), ("status", "S1", self.ms("11:55"))
        )
        self.assertIsNone(self.due(*logged, at="12:39:59", **self.unread()))
        self.assertEqual(
            self.due(*logged, at="12:40", **self.unread()),
            ("status", "S1", self.ms("11:55")),
        )
        # the session answers the message of 12:40 at 12:41, and no row comes back
        answered = (
            *logged,
            self.ev("12:40", "session.wake", session="S1", why="status"),
        )
        m = self.model(*answered, at="13:00", sign="2026-11-22T12:41:00Z")
        self.assertEqual(self.rows(m), [])
        # the timeline says it in words of its own
        said = bm.describe(logged[-1], m)
        self.assertEqual(
            (said["head"], said["text"]),
            (
                "Lem read the task’s session again, and it worked",
                (
                    "a turn of the session came after the status message that Lem sent "
                    "while it could not read it, so no stop waits for you"
                ),
            ),
        )

    # the writer of the record, which the release after this one turns on
    @mock.patch("lem.board_model.WRITES_WORKED", True)
    def test_a_turn_read_between_two_unread_looks_keeps_the_stop_from_being_logged(
        self,
    ) -> None:
        # the item's second run: the unread message at 11:39; a look at 11:45 reads the
        # signs and sees a turn at 11:40; a look at 11:49 does not read them
        woken = self.woken(unread=True)
        logged = (*woken, self.worked("11:45", "11:40"))
        self.assertIsNone(self.due(*logged, at="11:49", **self.unread()))
        self.assertEqual(
            self.due(*woken, at="11:45", sign="2026-11-22T11:40:00Z"),
            ("worked", "S1", self.ms("11:40")),
        )
        self.assertIsNone(self.due(*logged, at="12:24:59", **self.unread()))
        self.assertEqual(
            self.due(*logged, at="12:25", **self.unread()),
            ("status", "S1", self.ms("11:40")),
        )
        # a turn in the second of the message answers it, as for every clock
        self.assertEqual(
            self.due(*woken, at="11:45", sign="2026-11-22T11:39:00Z"),
            ("worked", "S1", self.ms("11:39")),
        )
        # a turn before the message is none, and a log of the old form, with no record
        # of a turn, gives the stop as before
        self.assertIsNone(self.due(*woken, at="11:45", sign="2026-11-22T11:30:00Z"))
        self.assertEqual(
            self.due(*woken, at="11:49", **self.unread()),
            ("stopped", "S1", self.ms("11:39")),
        )

    # the writer of the record, which the release after this one turns on
    @mock.patch("lem.board_model.WRITES_WORKED", True)
    def test_a_second_unread_period_gets_its_own_record_once(self) -> None:
        again = (
            *self.unread_stopped(),
            self.worked("11:56", "11:55"),
            self.ev("12:40", "session.wake", session="S1", why="status", unread=True),
            self.ev("12:50", "session.stopped", session="S1", unread=True),
        )
        m = self.model(*again, at="12:51", **self.unread())
        self.assertEqual(self.rows(m), ["stopped"])
        turned = {"sign": "2026-11-22T13:00:00Z"}
        self.assertEqual(
            self.due(*again, at="13:01", **turned), ("worked", "S1", self.ms("13:00"))
        )
        twice = (*again, self.worked("13:01", "13:00"))
        self.assertIsNone(self.due(*twice, at="13:02", **turned))
        self.assertEqual(self.rows(self.model(*twice, at="13:02", **turned)), [])

    # the writer of the record, which the release after this one turns on
    @mock.patch("lem.board_model.WRITES_WORKED", True)
    def test_a_turn_answers_only_the_status_message_that_the_standing_stop_followed(
        self,
    ) -> None:
        # the review's run of 2026-11-24: the unread message at 11:39 and its stop at
        # 11:49; a turn at 11:55 that no record holds yet; the readable clock's
        # message at 12:40 and its stop at 12:50. The turn came before the message of
        # 12:40, so it answers nothing that stands: no record is due, and the stop of
        # 12:50 keeps its row and the owner's "Open a session"
        twice = (
            *self.unread_stopped(),
            self.ev("12:40", "session.wake", session="S1", why="status"),
            self.ev("12:50", "session.stopped", session="S1"),
        )
        turned = {"sign": "2026-11-22T11:55:00Z"}
        self.assertIsNone(self.due(*twice, at="17:00", **turned))
        m = self.model(*twice, at="17:00", **turned)
        t = m.by_slug["gift-note"]
        self.assertIs(bm.stop_stands(t), twice[-1])
        self.assertEqual(self.rows(m), ["stopped"])
        # a record of that turn after the stop ends nothing either
        logged = (*twice, self.worked("12:51", "11:55"))
        m = self.model(*logged, at="17:00", **turned)
        t = m.by_slug["gift-note"]
        self.assertIs(bm.stop_stands(t), twice[-1])
        self.assertIsNotNone(bm.stopped_of(t, m))
        self.assertEqual(self.rows(m), ["stopped"])
        self.assertIsNone(self.due(*logged, at="17:00", **turned))
        # a turn after the message of 12:40 is no turn of the unread clock: the
        # readable stop stands, as for every readable stop
        self.assertIsNone(
            self.due(*twice, at="13:00", sign="2026-11-22T12:55:00Z"),
        )

    def test_after_the_record_a_quiet_session_gets_a_stop_never_a_restart(
        self,
    ) -> None:
        # be719e8c's run, with the record of the turn at 12:00: the readable clock's
        # message at 12:45 and no answer; Lem opens no fresh session by itself in the
        # run of work in which a stop of the task stood, and logs one newer stop
        logged = (
            *self.unread_stopped(),
            self.worked("12:01", "12:00"),
            self.ev("12:45", "session.wake", session="S1", why="status"),
        )
        turned = {"sign": "2026-11-22T12:00:00Z"}
        self.assertIsNone(self.due(*logged, at="12:54:59", **turned))
        self.assertEqual(
            self.due(*logged, at="12:55", **turned), ("stopped", "S1", self.ms("12:45"))
        )
        # a readable session with no stop before keeps its restart (criterion 4)
        self.assertEqual(
            self.due(*self.woken(), at="11:49"), ("restart", "S1", self.ms("11:39"))
        )

    def test_this_release_reads_the_record_and_writes_none(self) -> None:
        # a reader of 0.3.1 folds the record as a step of the landing, so this release
        # only reads it: the item's run gives the steps of the release before, and the
        # unread stop keeps its row
        self.assertFalse(bm.WRITES_WORKED)
        turned = {"sign": "2026-11-22T11:55:00Z"}
        self.assertIsNone(self.due(*self.unread_stopped(), at="11:56", **turned))
        self.assertEqual(
            self.due(*self.unread_stopped(), at="12:40", **turned),
            ("status", "S1", self.ms("11:55")),
        )
        m = self.model(*self.unread_stopped(), at="11:56", **turned)
        self.assertEqual(self.rows(m), ["stopped"])

    def test_the_record_of_a_turn_changes_no_step_of_the_landing(self) -> None:
        # the review's run of 2026-11-24: a landing whose checks wait for the load, an
        # unread status message and its stop, then the record of a turn; and one whose
        # polish pass runs. The card says the same before the record and after it.
        waiting = (
            *self.landing()[:2],
            self.ev("10:18", "gate.start", tip="5ccc53d36", commands=1),
            self.ev("10:19", "gate.wait", load=12, start=5),
            self.ev("11:39", "session.wake", session="S1", why="status", unread=True),
            self.ev("11:49", "session.stopped", session="S1", unread=True),
        )
        polishing = (
            *self.landing()[:2],
            self.ev("10:18", "polish.start", tip="5ccc53d36"),
            *waiting[-2:],
        )
        record = self.worked("11:56", "11:55")
        for events in (waiting, polishing):
            one, other = (
                bm.derive(list(log), [], self.ms("12:00")).by_slug["gift-note"]
                for log in (events, (*events, record))
            )
            self.assertEqual(
                (bm.now_head(other), other.waits, other.landing_step),
                (bm.now_head(one), one.waits, one.landing_step),
            )
        self.assertEqual(
            bm.now_head(bm.derive(list(waiting), [], 0).by_slug["gift-note"]),
            "Waits for the load: 12, starts below 5",
        )

    def test_the_record_of_a_turn_is_no_work_and_no_fact_of_the_card(self) -> None:
        # what a reader of the release before reads of it: `derive` keeps every record
        # in the task's events and folds nothing from one it does not know, and every
        # `session.*` record is no work
        record = self.worked("11:56", "11:55")
        self.assertFalse(bm.work_event(record))
        one, other = (
            self.model(*events, at="11:57").by_slug["gift-note"]
            for events in (self.unread_stopped(), (*self.unread_stopped(), record))
        )
        self.assertEqual(
            (other.status, other.since, other.blocks, other.wakes, other.opened),
            (one.status, one.since, one.blocks, one.wakes, one.opened),
        )
        self.assertEqual(
            (other.lane, other.for_owner, other.info),
            (one.lane, one.for_owner, one.info),
        )
        # the prune's summary of the task counts it as one event more, and says the
        # same of the task
        from lem import project

        now = self.ms("11:57")
        plain = project.summary_of("gift-note", list(self.unread_stopped()), now)
        more = project.summary_of("gift-note", [*self.unread_stopped(), record], now)
        self.assertEqual(more.pop("events"), plain.pop("events") + 1)
        self.assertEqual(more.pop("ts"), record["ts"])
        plain.pop("ts")
        self.assertEqual(more, plain)


class StoppedRow(unittest.TestCase):
    """Criteria 5 and 6 on the board: a stop the guard logged is the row `stopped` of
    "Waits for you", with "Open a session", until a session opens or the task's agent
    works again; and the timeline says each act of the guard with its time. The events
    are those of #37, from StoppedSession."""

    ev, model, landing, woken, restarted = (
        StoppedSession.ev,
        StoppedSession.model,
        StoppedSession.landing,
        StoppedSession.woken,
        StoppedSession.restarted,
    )
    ms = staticmethod(StoppedSession.ms)

    def stopped(self) -> tuple:
        return (
            *self.restarted(),
            self.ev("12:34", "session.wake", session="S2", why="status"),
            self.ev("12:44", "session.stopped", session="S2"),
        )

    def rows(self, *events: dict, at: str = "13:00", **given: Any) -> list:  # noqa: ANN401 - passed on whole to model, whose parameters type them
        m = self.model(*events, at=at, session="S2", sign=None, **given)
        return [
            (w["key"], w["kind"], bm.wait_say(w)["verb"], w["since"])
            for w in bm.waits_of(m)
        ]

    def test_a_stop_is_a_row_with_the_button_that_opens_a_fresh_session(self) -> None:
        self.assertEqual(
            self.rows(*self.stopped()),
            [
                (
                    "stopped:gift-note",
                    "stopped",
                    "Its session stopped: open a fresh one",
                    self.ms("12:44"),
                )
            ],
        )
        m = self.model(*self.stopped(), at="13:00", session="S2", sign=None)
        t = m.by_slug["gift-note"]
        self.assertTrue(bm.opens_session(t, m))
        say = bm.wait_say(bm.waits_of(m)[0])
        self.assertEqual(
            (say["actor"], say["to"], say["note"]),
            ("bad", "overview", "since Lem logged the stop"),
        )
        self.assertIn("Open a session here or on the task’s header", say["where"])
        # he acts on the board, so the verb opens the panel and never jumps to the
        # stopped pane
        self.assertIsNone(bm.session_of_wait(bm.waits_of(m)[0], m))
        self.assertIn(
            "Open a session here",
            cast("dict", bm.waits_for(t, bm.waits_of(m)))["where"],
        )
        html = str(
            pages.waits_page(
                pages.Ctx(
                    host="h",
                    workspace="w",
                    model=m,
                    asset=lambda name: name,
                    can_act=True,
                )
            )
        )
        row = html[html.index('id="wait-stopped-gift-note"') :]
        self.assertIn("Open a session", row[: row.index("</article>")])

    def test_no_row_before_the_stop_is_logged_or_after_a_session_opens_or_the_agent_works(
        self,
    ) -> None:
        before = self.stopped()[:-1]
        self.assertEqual(self.rows(*before, at="12:43"), [])
        opened = (
            *self.stopped(),
            self.ev(
                "12:50",
                "session.open",
                session="S3",
                name="gift-note",
                phase="land",
                why="stopped",
            ),
        )
        m = self.model(*opened, at="13:00", session="S3", sign=None)
        self.assertEqual(
            (
                [w["kind"] for w in bm.waits_of(m)],
                bm.opens_session(m.by_slug["gift-note"], m),
            ),
            ([], False),
        )
        worked = (
            *self.stopped(),
            self.ev("12:50", "gate.start", tip="77aa", commands=1),
        )
        self.assertEqual(self.rows(*worked), [])
        # the record of his click is no work and no open: the row goes with the open it
        # asked for
        self.assertEqual(
            len(
                self.rows(
                    *self.stopped(),
                    self.ev("12:50", "board.act", act="session", via="board"),
                )
            ),
            1,
        )

    def test_a_stopped_session_that_is_gone_is_the_no_session_row_alone(self) -> None:
        # the old pane closed after the stop: the open of "No session runs this task"
        # takes no stop, so no row `stopped` stands beside it
        self.assertEqual(
            [
                (k, kind, verb)
                for k, kind, verb, _ in self.rows(*self.stopped(), live=False)
            ],
            [("session:gift-note", "session", "No session runs this task")],
        )
        m = self.model(*self.stopped(), at="13:00", session="S2", sign=None, live=False)
        self.assertIsNone(bm.stopped_of(m.by_slug["gift-note"], m))
        self.assertTrue(bm.opens_session(m.by_slug["gift-note"], m))

    def test_a_stop_takes_the_place_of_a_wake_nobody_took(self) -> None:
        m = self.model(*self.stopped(), at="13:00", session="S2", sign=None)
        cast("dict", m.sessions)["gift-note"]["unanswered"] = True
        self.assertEqual([w["key"] for w in bm.waits_of(m)], ["stopped:gift-note"])

    def test_a_task_out_of_its_phase_has_no_row_whatever_its_stop(self) -> None:
        parked = (
            *self.stopped(),
            self.ev(
                "12:50",
                "task.state",
                status="parked",
                text="the owner parked it",
                lines=[],
            ),
        )
        self.assertEqual(self.rows(*parked), [])

    def test_the_timeline_says_each_act_of_the_guard_with_its_time(self) -> None:
        m = self.model(*self.stopped(), at="13:00", session="S2", sign=None)
        t = m.by_slug["gift-note"]
        said = {
            (e["event"], e.get("why")): (bm.describe(e, m), e["ts"])
            for e in t.events
            if e["event"].startswith("session.")
        }
        status, ts = said[("session.wake", "status")]
        self.assertEqual(
            status["head"], "The board’s server asked the task’s session for its status"
        )
        self.assertIn("no sign of work for 45 minutes", status["text"])
        restart, ts = said[("session.open", "stopped")]
        self.assertEqual(
            (restart["head"], ts),
            ("A fresh session took the task over", "2026-11-22T11:49:00Z"),
        )
        self.assertIn("beside the one that stopped", restart["sub"])
        self.assertEqual(
            said[("session.wake", "replaced")][0]["head"],
            "The board’s server told the old session that a fresh one replaced it",
        )
        stop, ts = said[("session.stopped", None)]
        self.assertEqual(
            (stop["head"], stop["info"]["actor"], ts),
            ("The task’s session stopped", "bad", "2026-11-22T12:44:00Z"),
        )
        # each with its time in the task's Activity
        ctx = pages.Ctx(
            host="h",
            workspace="w",
            model=m,
            asset=lambda name: name,
            task="gift-note",
            tab="timeline",
        )
        html = str(task_pages.feed_card(ctx, t))
        for head in (
            "asked the task’s session for its status",
            "A fresh session took the task over",
            "The task’s session stopped",
        ):
            self.assertIn(head, html)
        self.assertEqual(html.count(bm.stamp(self.ms("12:44"), m.now)), 1)

    def unread_model(self, *events: dict, at: str = "11:50") -> "bm.Model":
        return self.model(*events, at=at, session="S1", sign=None, signs=False)

    def test_criterion_2_an_unread_stop_is_the_row_stopped_that_says_lem_cannot_read_the_session(
        self,
    ) -> None:
        events = (
            *self.landing(),
            self.ev("11:39", "session.wake", session="S1", why="status", unread=True),
            self.ev("11:49", "session.stopped", session="S1", unread=True),
        )
        m = self.unread_model(*events)
        t = m.by_slug["gift-note"]
        rows = bm.waits_of(m)
        self.assertEqual(
            [(w["key"], w["kind"], bm.wait_say(w)["verb"], w["since"]) for w in rows],
            [
                (
                    "stopped:gift-note",
                    "stopped",
                    "Its session stopped, and Lem cannot read it: open a fresh one",
                    self.ms("11:49"),
                )
            ],
        )
        say = bm.wait_say(rows[0])
        self.assertEqual(
            (say["actor"], say["to"], say["note"]),
            ("bad", "overview", "since Lem logged the stop"),
        )
        for words in (
            "Lem cannot read whether the task’s session works",
            "the status message after 45 minutes with no event of the task",
            "no event of the task in the 10 minutes after it",
            "Lem opens no second session by itself",
            "open a session here or on the task’s header",
        ):
            self.assertIn(words, say["where"])
        # no fresh session took its place, so the readable row's words are not said
        self.assertNotIn("fresh session that took its place", say["where"])
        self.assertTrue(bm.opens_session(t, m))
        self.assertIn(
            "Lem cannot read whether", cast("dict", bm.waits_for(t, rows))["where"]
        )
        html = str(
            pages.waits_page(
                pages.Ctx(
                    host="h",
                    workspace="w",
                    model=m,
                    asset=lambda name: name,
                    can_act=True,
                )
            )
        )
        row = html[html.index('id="wait-stopped-gift-note"') :]
        row = row[: row.index("</article>")]
        self.assertIn("Open a session", row)
        self.assertIn("Lem cannot read it", row)
        # a work event of the task after the stop removes the row; the readable stop
        # keeps its own verb
        worked = (
            *events,
            self.ev(
                "11:55",
                "task.state",
                status="landing",
                text="the pull request waits for its checks",
                lines=[],
            ),
        )
        self.assertEqual(bm.waits_of(self.unread_model(*worked, at="11:56")), [])
        self.assertEqual(
            [
                bm.wait_say(w)["verb"]
                for w in bm.waits_of(
                    self.model(*self.stopped(), at="13:00", session="S2", sign=None)
                )
            ],
            ["Its session stopped: open a fresh one"],
        )

    def test_the_timeline_says_an_unread_wake_and_stop_in_words_of_their_own(
        self,
    ) -> None:
        events = (
            *self.landing(),
            self.ev("11:39", "session.wake", session="S1", why="status", unread=True),
            self.ev("11:49", "session.stopped", session="S1", unread=True),
        )
        m = self.unread_model(*events)
        said = {
            e["event"]: bm.describe(e, m)
            for e in m.by_slug["gift-note"].events
            if e["event"] in ("session.wake", "session.stopped")
        }
        wake, stop = said["session.wake"], said["session.stopped"]
        self.assertEqual(
            wake["head"], "The board’s server asked the task’s session for its status"
        )
        self.assertEqual(
            wake["text"],
            (
                "no event of the task for 45 minutes, and Lem cannot read its session: "
                "it says where the task stands and goes on with its next step"
            ),
        )
        self.assertEqual(
            (stop["head"], stop["info"]["actor"]), ("The task’s session stopped", "bad")
        )
        self.assertEqual(
            stop["text"],
            (
                "no event of the task in the 10 minutes after the status message, and "
                "Lem cannot read its session: “Open a session” on the "
                "board starts a fresh one"
            ),
        )
        # the readable wake and stop keep today's words
        readable = self.model(*self.stopped(), at="13:00", session="S2", sign=None)
        kept = {
            (e["event"], e.get("why")): bm.describe(e, readable)
            for e in readable.by_slug["gift-note"].events
        }
        self.assertEqual(
            kept[("session.wake", "status")]["text"],
            (
                "no sign of work for 45 minutes: it says where the task stands and "
                "goes on with its next step"
            ),
        )
        self.assertEqual(
            kept[("session.stopped", None)]["text"],
            (
                "no sign of work after the status message, nor in the fresh session: "
                "“Open a session” on the board starts another"
            ),
        )

    def test_a_stop_over_a_standing_unread_stop_names_no_fresh_session(self) -> None:
        # review 2 of guard-sees-unreadable-sessions (#60): the unread stop of 11:49, a
        # turn at 12:00, the readable message at 12:45 and a newer stop at 12:55, and no
        # fresh session ever opened; a log of the release before, with no record of the
        # turn (`session.worked`)
        events = (
            *self.woken(unread=True),
            self.ev("11:49", "session.stopped", session="S1", unread=True),
            self.ev("12:45", "session.wake", session="S1", why="status"),
            self.ev("12:55", "session.stopped", session="S1"),
        )
        m = self.model(*events, at="13:00", sign="2026-11-22T12:00:00Z")
        row = next(w for w in bm.waits_of(m) if w["kind"] == "stopped")
        self.assertEqual(
            bm.wait_say(row)["where"],
            (
                "The task’s session showed no sign of work in the 10 minutes after "
                "Lem asked it for its status, and Lem opened no fresh session by "
                "itself, since the task already stopped once after its last work. Open "
                "a session here or on the task’s header: a fresh agent reads the task’s "
                "state and goes on from there, and the old pane stays open in agterm."
            ),
        )
        stop = m.by_slug["gift-note"].events[-1]
        self.assertEqual(
            bm.describe(stop, m)["text"],
            (
                "no sign of work after the status message, and Lem opened no fresh "
                "session by itself: “Open a session” on the board starts one"
            ),
        )
        # a stop after the spent restart keeps its words
        readable = self.model(*self.stopped(), at="13:00", session="S2", sign=None)
        row = next(w for w in bm.waits_of(readable) if w["kind"] == "stopped")
        self.assertIn(
            "and neither did the fresh session that took its place",
            bm.wait_say(row)["where"],
        )
        self.assertEqual(
            bm.describe(readable.by_slug["gift-note"].events[-1], readable)["text"],
            (
                "no sign of work after the status message, nor in the fresh session: "
                "“Open a session” on the board starts another"
            ),
        )

    def test_the_timeline_says_that_a_stop_over_new_work_leaves_nothing_waiting(
        self,
    ) -> None:
        # a state block logged after the look at 11:49 but before the stop's record: the
        # stop never stood
        raced = (
            *self.landing(),
            self.ev("11:39", "session.wake", session="S1", why="status", unread=True),
            self.ev(
                "11:49",
                "task.state",
                status="landing",
                text="the pull request waits for its checks",
                lines=[],
            ),
            self.ev("11:49", "session.stopped", session="S1", unread=True),
        )
        m = self.unread_model(*raced)
        t = m.by_slug["gift-note"]
        stop = next(e for e in t.events if e["event"] == "session.stopped")
        said = bm.describe(stop, m)
        self.assertEqual(
            (said["head"], said["info"]["actor"]),
            ("Lem logged a stop of the task’s session, but the task worked", "quiet"),
        )
        self.assertIn(
            "so the stop does not stand and nothing waits for you", said["text"]
        )
        self.assertEqual(bm.waits_of(m), [])
        # the same in the task's Activity
        ctx = pages.Ctx(
            host="h",
            workspace="w",
            model=m,
            asset=lambda name: name,
            task="gift-note",
            tab="timeline",
        )
        self.assertIn("but the task worked", str(task_pages.feed_card(ctx, t)))
        # a stop that stood keeps its words when work comes after it: the work ends the
        # row, not what the stop was
        wake, block, stop_record = raced[-3:]
        later = self.unread_model(*self.landing(), wake, stop_record, block, at="11:50")
        stood = next(
            e
            for e in later.by_slug["gift-note"].events
            if e["event"] == "session.stopped"
        )
        self.assertEqual(
            bm.describe(stood, later)["head"], "The task’s session stopped"
        )
        # a record that is not one of the task's own events is no such stop
        self.assertFalse(bm.stop_over_work(t, dict(stop)))

    def waiting(self, m: "bm.Model") -> dict:
        from unittest import mock

        from lem import project

        task = {
            "slug": "gift-note",
            "ask": "a gift note",
            "since": "2026-11-22T12:44:00Z",
            "night": None,
            "state": "",
            "status": "landing",
        }
        pending = mock.Mock(
            returncode=0, stdout=json.dumps({"waiting": [], "ended": []})
        )
        with (
            tempfile.TemporaryDirectory() as state,
            mock.patch.object(project, "load", return_value={}),
            mock.patch.object(project, "read_tasks", return_value=[task]),
            mock.patch.object(project, "waiting_model", return_value=(m, None)),
            mock.patch.object(project.subprocess, "run", return_value=pending),
            mock.patch.object(project, "owner_records", return_value=[]),
            mock.patch.object(project, "state_root", return_value=Path(state)),
        ):
            return project.cmd_waiting(Path("/lem-unit/repo"))

    def test_lem_project_waiting_lists_the_stop_as_the_board_has_it(self) -> None:
        found = self.waiting(
            self.model(*self.stopped(), at="13:00", session="S2", sign=None)
        )
        self.assertEqual(
            [(e["task"], e["open"], e["unread"]) for e in found["stopped"]],
            [("gift-note", "lem session open gift-note --why stopped", False)],
        )
        self.assertEqual(
            (found["rows"], found["no_session"], found["count"]),
            (
                [{"key": "stopped:gift-note", "kind": "stopped", "task": "gift-note"}],
                [],
                1,
            ),
        )

    def test_lem_project_waiting_says_that_lem_cannot_read_the_stopped_session(
        self,
    ) -> None:
        events = (
            *self.landing(),
            self.ev("11:39", "session.wake", session="S1", why="status", unread=True),
            self.ev("11:49", "session.stopped", session="S1", unread=True),
        )
        found = self.waiting(self.unread_model(*events))
        self.assertEqual(
            [(e["task"], e["open"], e["unread"]) for e in found["stopped"]],
            [("gift-note", "lem session open gift-note --why stopped", True)],
        )


class Cards(unittest.TestCase):
    """A `lem-ask` card of a task's session (criterion 1 of board-answers-a-card): a row
    of "Waits for you" with its question while its folder says it is open and the
    session that put it up is the task's live one."""

    PAGE = "P-1"
    ASKED = [
        state(0, "building", "task 1 of 2", task="export-notes"),
        ev(1, "session.open", "export-notes", session="S1", name="export-notes"),
        ev(2, "card.asked", "export-notes", page=PAGE, prompt="Keep the empty cell?"),
    ]

    def model(
        self, *more: dict, session: str = "S1", live: bool = True, cards: bool = True
    ) -> "bm.Model":
        m = model(*self.ASKED, *more)
        m.sessions = {
            "export-notes": {
                "live": live,
                "agent": live,
                "unanswered": False,
                "session": "S1",
            }
        }
        if cards:
            m.cards = {
                "export-notes": [
                    {
                        "page": self.PAGE,
                        "prompt": "Keep the empty cell?",
                        "since": bm.at(self.ASKED[2]["ts"]),
                        "session": session,
                        "chat": True,
                    }
                ]
            }
        return m

    def test_an_open_card_of_the_live_session_is_a_row_with_its_question_whose_verb_opens_the_card(
        self,
    ) -> None:
        m = self.model()
        rows = [w for w in bm.waits_of(m) if w["kind"] == "card"]
        self.assertEqual(
            [(w["key"], bm.wait_say(w)["verb"], bm.wait_say(w)["to"]) for w in rows],
            [("card:export-notes:P-1", "Keep the empty cell?", "card/P-1")],
        )
        self.assertFalse(bm.answered_in_session(rows[0], m))
        self.assertIn("never a conversation", bm.wait_say(rows[0])["where"])

    def test_a_card_of_an_earlier_session_or_of_a_session_that_does_not_run_has_no_row(
        self,
    ) -> None:
        for m in (
            self.model(session="S0"),
            self.model(live=False),
            self.model(cards=False),
        ):
            self.assertEqual(
                [w["key"] for w in bm.waits_of(m) if w["kind"] == "card"], []
            )

    def test_the_folder_says_which_cards_are_open_and_the_end_event_closes_one_in_the_log(
        self,
    ) -> None:
        from lem import cards as lem_cards

        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            folder = state_dir / "tasks" / "export-notes"
            (folder / "cards").mkdir(parents=True)
            lem_cards.card_file(folder, self.PAGE).write_text(
                json.dumps(
                    {
                        "page": self.PAGE,
                        "session": "S1",
                        "questions": [
                            {"id": "answer", "prompt": "Keep the empty cell?"}
                        ],
                    }
                )
            )
            m = model(*self.ASKED)
            self.assertEqual(
                [
                    (c["page"], c["session"], c["prompt"])
                    for c in bm.cards_look(state_dir, m)["export-notes"]
                ],
                [(self.PAGE, "S1", "Keep the empty cell?")],
            )
            lem_cards.end_file(folder, self.PAGE).write_text(
                json.dumps({"page": self.PAGE, "status": "answered", "from": "board"})
            )
            self.assertEqual(bm.cards_look(state_dir, m), {})
            lem_cards.end_file(folder, self.PAGE).unlink()
            answered = model(
                *self.ASKED,
                ev(
                    3,
                    "card.answered",
                    "export-notes",
                    page=self.PAGE,
                    **{"from": "board"},
                ),
            )
            self.assertEqual(
                (answered.tasks[0].cards, bm.cards_look(state_dir, answered)), ({}, {})
            )
