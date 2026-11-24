"""The rows the board answers with its own buttons (the task board-answers-a-card, task
3): a plan (Build, Drop), a breaker (Help, Park, Drop), "Skip the persona read?" and
"Approve this criterion?" (Yes, No). Each row's key, named by its state block
(lem_board_model `answer_row`); its one answer form in the row and on the task's page
(lem_board_pages `answer_form`) and Drop's confirm step (lem_board_task `drop_step`);
the answer route and the record that orders every act of the board on a row (serve.py
`act_answer`, `act_park`, `act_approve`, lem_answers); the row that leaves while his
answer is on record; and `board_answer` of `lem project tasks`. The routes run in
tests/lem-board-act.sh with a server, and Drop's confirm on a phone
in tests/lem-board-keys.sh.

    .venv/bin/python -B -m unittest discover -s tests/unit
"""

import json
import subprocess
import sys
import tempfile
import threading
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast
from unittest import mock

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from lem import answers as lem_answers
from lem import board_model as bm
from lem import board_pages as pages
from lem import board_task as task_pages
from lem import project, serve

START = datetime(2026, 11, 23, 15, 0, tzinfo=UTC)
NOW = int((START + timedelta(hours=1)).timestamp() * 1000)
SLUG = "export-notes"
IPHONE = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/18.1 Mobile/15E148 Safari/604.1"
)
PHONE = {"via": "door", "device": "phone", "agent": IPHONE}
CRITERION = (
    "## Acceptance criteria\n\nSize: small, because one cell.\n\n"
    "1. An empty note writes an empty cell.\n"
)


def ev(minute: float, event: str, **fields: object) -> dict:
    return {
        "ts": (START + timedelta(minutes=minute)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event": event,
        "task": SLUG,
        **fields,
    }


def state(minute: float, status: str, text: str, *lines: str) -> dict:
    return ev(minute, "task.state", status=status, text=text, lines=list(lines))


def stamp(minute: float) -> str:
    return (START + timedelta(minutes=minute)).strftime("%Y%m%dT%H%M%SZ")


OPENED = ev(0.5, "session.open", session="S1", name=SLUG, phase="build")
BREAKER = [
    state(0, "building", "task 2 of 3"),
    OPENED,
    ev(
        20,
        "decision.breaker",
        id=1,
        cause="criteria",
        what="The note has no place",
        document="breaker.md",
    ),
    state(
        20,
        "held",
        "breaker 1 waits for the owner",
        "The note has no place: no option keeps the criteria",
    ),
]
PLAN = [
    state(0, "building", "lead: builder"),
    OPENED,
    state(10, "planned", "the owner reads the plan"),
]
SKIP = [
    state(0, "held", "the interview waits for the owner", "type: fix, because a cell"),
    OPENED,
    ev(1, "interview.start"),
    ev(5, "interview.end"),
    ev(12, "read.skip.asked"),
]
FAST = [state(0, "held", bm.FAST_CRITERION, "type: fix, because a cell"), OPENED]


def model(*events: dict, answers: dict | None = None) -> bm.Model:
    m = bm.derive(list(events), [], NOW)
    m.sessions = {
        SLUG: {"live": True, "agent": True, "unanswered": False, "session": "S1"}
    }
    m.answers = answers
    return m


class Workspace:
    """The workspace of the server as the acts read it: its state folder, its model over
    EVENTS and the answers in the folder, the criteria that wait, and its count
    of acts."""

    def __init__(
        self, state_: Path, events: list, criteria: str | None = CRITERION
    ) -> None:
        self.state, self.events, self.criteria, self.acted, self.path = (
            state_,
            events,
            criteria,
            0,
            str(state_.parent.parent),
        )

    def model(self) -> bm.Model:
        m = model(*self.events)
        m.answers = bm.answers_look(self.state, m)
        return m

    def criteria_waiting(self, slug: str) -> dict | None:
        return (
            None
            if self.criteria is None
            else {"path": "/t/criteria.md", "text": self.criteria, "digest": "d1g3st"}
        )

    def look_sessions(self) -> None:
        pass


class Acts(unittest.TestCase):
    """The acts over a task folder, with `lem session wake`, the scripts and the log of
    `board.act` stood in for."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state = Path(self.tmp.name) / ".lem" / "state"
        self.folder = self.state / "tasks" / SLUG
        self.folder.mkdir(parents=True)
        self.calls: list = []
        self.refuse = False

        def run(ws: Workspace, file: str, *args: str) -> subprocess.CompletedProcess:
            self.calls.append((file, *args))
            return subprocess.CompletedProcess(
                args, 1 if self.refuse else 0, "", "it refused" if self.refuse else ""
            )

        for name, fake in (
            (
                "tell_session",
                lambda ws, slug: (
                    self.calls.append(("wake", slug))
                    or {"woke": True, "opened": False, "said": ""}
                ),
            ),
            (
                "asked_from",
                lambda ws, slug, act, via, *more: (
                    self.calls.append(("board.act", act, via, *more)) or ""
                ),
            ),
            ("lem_run", run),
        ):
            patcher = mock.patch.object(serve, name, side_effect=fake)
            patcher.start()
            self.addCleanup(patcher.stop)

    def ws(self, *events: dict, criteria: str | None = CRITERION) -> Workspace:
        return Workspace(self.state, list(events or BREAKER), criteria)

    def answer(
        self, form: dict, *events: dict, heard: dict = PHONE, **kw: str | None
    ) -> dict:
        return serve.act_answer(
            cast("serve.Workspace", self.ws(*events, **kw)), SLUG, form, dict(heard)
        )

    def key(self, *events: dict) -> str:
        return cast("dict", bm.answer_row(model(*events).tasks[0]))["key"]

    def record(self, key: str) -> dict | None:
        return lem_answers.on_record(self.folder, key)

    def test_criterion_6_a_breaker_offers_help_park_and_drop_and_drop_after_its_confirm_is_on_record_and_wakes_the_session(
        self,
    ) -> None:
        key = self.key(*BREAKER)
        self.assertEqual(key, f"breaker:{SLUG}:1:{stamp(20)}")
        self.assertEqual(
            list(
                cast("dict", bm.answer_row(model(*BREAKER).tasks[0]))[
                    "options"
                ].values()
            ),
            ["Help", "Park", "Drop"],
        )
        unconfirmed = self.answer({"key": key, "option": "drop"})
        self.assertEqual(
            unconfirmed,
            {
                "ok": False,
                "said": (
                    "Drop asks for a confirm first: open Drop… and confirm there. "
                    "Nothing was recorded."
                ),
            },
        )
        self.assertIsNone(self.record(key))
        done = self.answer(
            {
                "key": key,
                "option": "drop",
                "confirm": "yes",
                "words": "  the export   goes  another way ",
            }
        )
        self.assertEqual(
            done,
            {
                "ok": True,
                "said": (
                    f"{bm.ANSWER_ON_RECORD} The task’s session got word of it, and it "
                    "drops the task as on /lem drop."
                ),
            },
        )
        self.assertIn(("wake", SLUG), self.calls)
        self.assertIn(
            (
                "board.act",
                "answer",
                bm.VIA["door"],
                f"key={key}",
                "option=drop",
                f"question=Breaker 1 of {SLUG}: help, park or drop the task?",
            ),
            self.calls,
        )
        # the server never runs the drop itself: no script of Lem's ran
        self.assertEqual(
            [c for c in self.calls if c[0] not in ("wake", "board.act")], []
        )
        self.assertEqual(
            cast("dict", self.record(key))["note"], "the export goes another way"
        )

    def test_criterion_9_the_record_is_the_owners_with_the_question_option_note_time_and_device(
        self,
    ) -> None:
        key = self.key(*BREAKER)
        self.answer(
            {"key": key, "option": "help", "words": "Put the note in the last column."}
        )
        made = cast("dict", self.record(key))
        self.assertEqual(
            {
                k: made[k]
                for k in (
                    "key",
                    "kind",
                    "question",
                    "option",
                    "label",
                    "note",
                    "from",
                    "via",
                    "device",
                    "agent",
                )
            },
            {
                "key": key,
                "kind": "breaker",
                "question": f"Breaker 1 of {SLUG}: help, park or drop the task?",
                "option": "help",
                "label": "Help",
                "note": "Put the note in the last column.",
                "from": "board",
                "via": "door",
                "device": "phone",
                "agent": IPHONE,
            },
        )
        self.assertRegex(made["at"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
        # a computer on this Mac is the other place
        plan_key = self.key(*PLAN)
        self.answer(
            {"key": plan_key, "option": "build"},
            *PLAN,
            heard={"via": "local", "device": "computer", "agent": "Mac"},
        )
        self.assertEqual(
            (
                cast("dict", self.record(plan_key))["device"],
                cast("dict", self.record(plan_key))["via"],
            ),
            ("computer", "local"),
        )

    def test_criterion_6_help_needs_his_words_and_no_option_is_refused(self) -> None:
        key = self.key(*BREAKER)
        self.assertEqual(
            self.answer({"key": key, "option": "help", "words": "  "})["said"],
            "Help needs your words for the lead: nothing was recorded.",
        )
        self.assertEqual(
            self.answer({"key": key, "words": "only a note"})["said"],
            "Pick an option first: nothing was recorded.",
        )
        self.assertIn(
            "takes Help, Park, Drop", self.answer({"key": key, "option": "yes"})["said"]
        )
        self.assertIsNone(self.record(key))
        self.assertNotIn(("wake", SLUG), self.calls)

    def test_criterion_6_only_the_first_answer_counts_and_a_later_one_says_what_took_effect(
        self,
    ) -> None:
        key = self.key(*BREAKER)
        self.answer({"key": key, "option": "drop", "confirm": "yes"})
        later = self.answer({"key": key, "option": "help", "words": "go on"})
        self.assertFalse(later["ok"])
        self.assertRegex(
            later["said"],
            (
                r"^You picked Drop for breaker 1 at \d\d:\d\d, from the phone: "
                r"the task’s session takes it\.$"
            ),
        )
        self.assertEqual(cast("dict", self.record(key))["option"], "drop")
        # Park, from its own step, reads the same record first
        parked = serve.act_park(
            cast("serve.Workspace", self.ws()),
            SLUG,
            {"key": key, "why": "later"},
            bm.VIA["local"],
            heard=PHONE,
        )
        self.assertEqual(parked["said"], later["said"])
        self.assertNotIn(("project.py", "state", SLUG, "parked", "later"), self.calls)

    def test_a_park_links_the_rows_record_first_and_a_later_drop_is_told_what_took_effect(
        self,
    ) -> None:
        key = self.key(*BREAKER)
        parked = serve.act_park(
            cast("serve.Workspace", self.ws()),
            SLUG,
            {"key": key, "why": "wait for the new reader"},
            bm.VIA["door"],
            heard=PHONE,
        )
        self.assertTrue(parked["ok"])
        self.assertEqual(
            (
                cast("dict", self.record(key))["option"],
                cast("dict", self.record(key))["note"],
            ),
            ("park", "wait for the new reader"),
        )
        self.assertIn(
            ("project.py", "state", SLUG, "parked", "wait for the new reader"),
            self.calls,
        )
        drop = self.answer({"key": key, "option": "drop", "confirm": "yes"})
        self.assertRegex(
            drop["said"],
            (
                r"^You picked Park for breaker 1 at \d\d:\d\d, from the phone: "
                r"the task’s session takes it\.$"
            ),
        )

    def test_a_park_whose_script_refuses_takes_its_record_back(self) -> None:
        key = self.key(*BREAKER)
        self.refuse = True
        self.assertEqual(
            serve.act_park(
                cast("serve.Workspace", self.ws()),
                SLUG,
                {"key": key},
                bm.VIA["local"],
                heard=PHONE,
            ),
            {"ok": False, "said": "it refused"},
        )
        self.assertIsNone(self.record(key))

    def test_a_key_that_no_longer_waits_says_what_holds_now_and_records_nothing(
        self,
    ) -> None:
        key = self.key(*BREAKER)
        parked = [*BREAKER, state(25, "parked", "the owner parked it")]
        said = self.answer({"key": key, "option": "drop", "confirm": "yes"}, *parked)[
            "said"
        ]
        self.assertRegex(
            said,
            (
                rf"^Breaker 1 of {SLUG} no longer waits: you parked it at \d\d:\d\d\. "
                r"Nothing was recorded\.$"
            ),
        )
        # his Help ended with no decision: the held block is written again, a new row,
        # and the old page's answer is refused
        again = [
            *BREAKER,
            state(
                30,
                "held",
                "breaker 1 waits for the owner",
                "the lead's line to his note",
            ),
        ]
        self.assertEqual(self.key(*again), f"breaker:{SLUG}:1:{stamp(30)}")
        said = self.answer({"key": key, "option": "drop", "confirm": "yes"}, *again)[
            "said"
        ]
        self.assertRegex(
            said,
            (
                rf"^Breaker 1 of {SLUG} waits again since \d\d:\d\d, and the page you "
                r"answered from showed an earlier wait"
            ),
        )
        self.assertFalse((self.folder / "answers").exists())
        self.assertIn(
            "names no row",
            self.answer({"key": "merge:export-notes", "option": "drop"})["said"],
        )

    def test_criterion_6_a_plan_offers_build_and_drop_and_build_is_on_record_for_the_session(
        self,
    ) -> None:
        key = self.key(*PLAN)
        self.assertEqual(
            (
                key,
                list(
                    cast("dict", bm.answer_row(model(*PLAN).tasks[0]))[
                        "options"
                    ].values()
                ),
            ),
            (f"plan:{SLUG}:{stamp(10)}", ["Build", "Drop"]),
        )
        done = self.answer({"key": key, "option": "build"}, *PLAN)
        self.assertTrue(done["ok"])
        self.assertEqual(cast("dict", self.record(key))["option"], "build")
        self.assertEqual([w["kind"] for w in bm.waits_of(self.ws(*PLAN).model())], [])

    def test_criterion_7_yes_on_skip_the_persona_read_is_on_record_and_wakes_the_session_as_his_y_does(
        self,
    ) -> None:
        key = self.key(*SKIP)
        self.assertEqual(key, f"skip:{SLUG}:{stamp(0)}")
        rows = bm.waits_of(model(*SKIP))
        self.assertEqual(
            [(w["key"], list(w["asks"]["options"].values())) for w in rows],
            [(key, ["Yes", "No"])],
        )
        self.assertFalse(
            bm.answered_in_session(rows[0], model(*SKIP)), "the board answers it now"
        )
        self.assertTrue(self.answer({"key": key, "option": "yes"}, *SKIP)["ok"])
        self.assertEqual(
            (
                cast("dict", self.record(key))["question"],
                cast("dict", self.record(key))["label"],
            ),
            ("Skip the persona read?", "Yes"),
        )
        self.assertIn(("wake", SLUG), self.calls)
        self.assertEqual(bm.waits_of(self.ws(*SKIP).model()), [])

    def test_criterion_7_yes_on_the_criterion_links_the_record_then_approves_the_bytes_the_page_showed(
        self,
    ) -> None:
        key = self.key(*FAST)
        self.assertEqual(key, f"criterion:{SLUG}:{stamp(0)}")
        stale = self.answer({"key": key, "option": "yes", "digest": "other"}, *FAST)
        self.assertEqual(
            stale["said"],
            (
                "The criteria changed since the page showed them. Read them again, "
                "then approve."
            ),
        )
        self.assertIsNone(self.record(key))
        done = self.answer({"key": key, "option": "yes", "digest": "d1g3st"}, *FAST)
        self.assertTrue(done["ok"], done)
        self.assertIn(
            (
                "criteria.py",
                "approve",
                SLUG,
                "--file",
                "/t/criteria.md",
                "--shown",
                "d1g3st",
            ),
            self.calls,
        )
        self.assertEqual(
            (
                cast("dict", self.record(key))["option"],
                cast("dict", self.record(key))["digest"],
            ),
            ("yes", "d1g3st"),
        )

    def test_a_yes_whose_approval_refuses_takes_its_record_back(self) -> None:
        key = self.key(*FAST)
        self.refuse = True
        self.assertEqual(
            self.answer({"key": key, "option": "yes", "digest": "d1g3st"}, *FAST),
            {"ok": False, "said": "it refused"},
        )
        self.assertIsNone(self.record(key))

    def test_criterion_7_no_on_the_criterion_needs_his_words_and_the_text_the_page_showed(
        self,
    ) -> None:
        key = self.key(*FAST)
        self.assertEqual(
            self.answer({"key": key, "option": "no", "digest": "d1g3st"}, *FAST)[
                "said"
            ],
            "No needs your words: what should the criterion say? Nothing was recorded.",
        )
        self.assertEqual(
            self.answer(
                {"key": key, "option": "no", "digest": "other", "words": "a dash"},
                *FAST,
            )["said"],
            (
                "The criterion changed since the page showed it. Read it again, then "
                "answer: nothing was recorded."
            ),
        )
        self.assertIsNone(self.record(key))
        self.assertTrue(
            self.answer(
                {
                    "key": key,
                    "option": "no",
                    "digest": "d1g3st",
                    "words": "a dash, as in the invoice export",
                },
                *FAST,
            )["ok"]
        )
        self.assertEqual(
            (
                cast("dict", self.record(key))["note"],
                cast("dict", self.record(key))["digest"],
            ),
            ("a dash, as in the invoice export", "d1g3st"),
        )
        self.assertNotIn("criteria.py", [c[0] for c in self.calls])

    def test_two_answers_at_once_record_one(self) -> None:
        key = self.key(*BREAKER)
        results: list = []
        threads = [
            threading.Thread(
                target=lambda o=o: results.append(
                    lem_answers.record(self.folder, key, "q", o, "", **PHONE)[0]
                )
            )
            for o in ("help", "park", "drop") * 4
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(sorted(results), [False] * 11 + [True])
        self.assertEqual(
            sorted(p.name for p in (self.folder / "answers").iterdir()), [f"{key}.json"]
        )


class Rows(unittest.TestCase):
    """The rows and the task's page: the one answer form, the row that leaves while his
    answer is on record, and Drop's step."""

    def ctx(
        self,
        *events: dict,
        answers: dict | None = None,
        can_act: bool = True,
        tab: str = "overview",
        query: dict | None = None,
        view: str = "waits",
    ) -> pages.Ctx:
        ctx = pages.Ctx(
            host="h",
            workspace="w",
            model=model(*events, answers=answers),
            asset=lambda name: name,
            can_act=can_act,
            task=SLUG,
            tab=tab,
            query=query or {},
        )
        ctx.view = view
        ctx.criteria_waiting = lambda slug: {"text": CRITERION, "digest": "d1g3st"}
        ctx.artifact = lambda task, name: {"text": "# The note has no place"}
        ctx.artifact_files = []
        return ctx

    def test_criterion_6_the_breakers_row_and_its_overview_hold_one_answer_form_with_help_park_and_drop(
        self,
    ) -> None:
        ctx = self.ctx(*BREAKER)
        key = f"breaker:{SLUG}:1:{stamp(20)}"
        waits = str(pages.waits_page(ctx))
        overview = "".join(
            str(x) for x in task_pages.overview_tab(ctx, ctx.model.tasks[0]) if x
        )
        for html in (waits, overview):
            self.assertIn(f'action="/h/w/tasks/{SLUG}/answer"', html)
            self.assertIn(f'name="key" value="{key}"', html)
            self.assertIn('name="words"', html)
            self.assertIn("Help needs your words for the lead", html)
            self.assertIn('name="option" value="help"', html)
            self.assertIn(f'formaction="/h/w/tasks/{SLUG}/park" formmethod="get"', html)
            self.assertIn(f'formaction="/h/w/tasks/{SLUG}/drop" formmethod="get"', html)
            self.assertIn("<span>Drop…</span>", html)
        self.assertIn('name="in" value="waits"', waits)
        mute = self.ctx(*BREAKER, can_act=False)
        self.assertNotIn("/answer", str(pages.waits_page(mute)))

    def test_criterion_6_drops_step_asks_drop_export_notes_with_confirm_and_the_note_the_row_sent(
        self,
    ) -> None:
        key = f"breaker:{SLUG}:1:{stamp(20)}"
        ctx = self.ctx(
            *BREAKER,
            tab="drop",
            query={"key": key, "words": "the export goes another way"},
        )
        html = "".join(str(x) for x in task_pages.drop_step(ctx, ctx.model.tasks[0]))
        self.assertIn(f'<div class="eyebrow">Drop {SLUG}?</div>', html)
        self.assertIn(f'action="/h/w/tasks/{SLUG}/answer"', html)
        for field in (
            f'name="key" value="{key}"',
            'name="option" value="drop"',
            'name="confirm" value="yes"',
            'name="in" value="waits"',
        ):
            self.assertIn(field, html)
        self.assertIn(">the export goes another way</textarea>", html)
        self.assertIn("<span>Confirm</span>", html)
        self.assertIn('data-controller="sheet"', html)
        self.assertIn('id="tb-drop"', str(task_pages.panel(ctx)))
        # an old page's Drop, a drop of a task with no such wait, and a drop on record
        # say so and offer nothing
        old = self.ctx(
            *BREAKER, tab="drop", query={"key": f"breaker:{SLUG}:1:{stamp(5)}"}
        )
        self.assertIn(
            "that is over",
            "".join(str(x) for x in task_pages.drop_step(old, old.model.tasks[0])),
        )
        none = self.ctx(state(0, "building", "task 1 of 2"), OPENED, tab="drop")
        self.assertIn(
            "Nothing to drop from the board",
            "".join(str(x) for x in task_pages.drop_step(none, none.model.tasks[0])),
        )
        made = {
            "key": key,
            "option": "drop",
            "label": "Drop",
            "at": "2026-11-23T15:40:00Z",
            "device": "phone",
        }
        done = self.ctx(*BREAKER, tab="drop", answers={SLUG: {key: made}})
        said = "".join(str(x) for x in task_pages.drop_step(done, done.model.tasks[0]))
        self.assertIn("You picked Drop for breaker 1 at", said)
        self.assertNotIn("/answer", said)

    def test_the_park_step_carries_the_rows_key_and_the_note(self) -> None:
        key = f"breaker:{SLUG}:1:{stamp(20)}"
        ctx = self.ctx(
            *BREAKER, tab="park", query={"key": key, "words": "wait for the reader"}
        )
        html = "".join(str(x) for x in task_pages.park_step(ctx, ctx.model.tasks[0]))
        self.assertIn(f'name="key" value="{key}"', html)
        self.assertIn('value="wait for the reader"', html)

    def test_criterion_6_the_plans_row_offers_build_and_drop(self) -> None:
        html = str(pages.waits_page(self.ctx(*PLAN)))
        self.assertIn('name="option" value="build"', html)
        self.assertIn(f'formaction="/h/w/tasks/{SLUG}/drop"', html)
        self.assertIn("Build the plan, or drop the task?", html)

    def test_criterion_7_the_two_yes_no_rows_offer_yes_and_no_and_the_criterion_under_its_text_with_its_digest(
        self,
    ) -> None:
        skip = str(pages.waits_page(self.ctx(*SKIP)))
        self.assertIn("Skip the persona read?", skip)
        self.assertIn('name="option" value="yes"', skip)
        self.assertIn('name="option" value="no"', skip)
        fast = str(pages.waits_page(self.ctx(*FAST)))
        self.assertIn("Approve this criterion?", fast)
        self.assertIn('name="digest" value="d1g3st"', fast)
        self.assertIn("An empty note writes an empty cell.", fast)
        self.assertIn("No needs your words: what should the criterion say?", fast)
        self.assertNotIn("Read and approve", fast)
        ctx = self.ctx(*FAST, tab="criteria")
        tab = str(task_pages.approve_card(ctx, ctx.model.tasks[0]))
        self.assertIn('name="digest" value="d1g3st"', tab)
        self.assertIn('name="tab" value="criteria"', tab)
        self.assertIn('name="option" value="no"', tab)
        # the standard track's criteria take Yes and No too, with their own
        # question (criteria-change-asks-again)
        std = self.ctx(
            state(0, "held", "the criteria wait for the owner"), OPENED, tab="criteria"
        )
        self.assertEqual(
            cast("dict", bm.answer_row(std.model.tasks[0]))["question"],
            "Approve the criteria?",
        )
        self.assertIn(
            'name="option" value="no"',
            str(task_pages.approve_card(std, std.model.tasks[0])),
        )

    def test_criterion_6_an_answer_on_record_hides_the_row_and_the_overview_says_so_until_the_next_block(
        self,
    ) -> None:
        key = f"breaker:{SLUG}:1:{stamp(20)}"
        made = {
            "key": key,
            "option": "drop",
            "label": "Drop",
            "note": "another way",
            "at": "2026-11-23T15:40:00Z",
            "device": "phone",
        }
        ctx = self.ctx(*BREAKER, answers={SLUG: {key: made}})
        self.assertEqual(bm.waits_of(ctx.model), [])
        overview = "".join(
            str(x) for x in task_pages.overview_tab(ctx, ctx.model.tasks[0]) if x
        )
        self.assertIn(bm.ANSWER_ON_RECORD, overview)
        self.assertIn("You picked Drop for breaker 1 at", overview)
        self.assertNotIn("/answer", overview)
        # the session's next block is another key: the record of the old one holds
        # nothing back
        again = self.ctx(
            *BREAKER,
            state(30, "held", "breaker 1 waits for the owner"),
            answers={SLUG: {key: made}},
        )
        self.assertEqual(
            [w["key"] for w in bm.waits_of(again.model)],
            [f"breaker:{SLUG}:1:{stamp(30)}"],
        )

    def test_the_reader_reads_the_record_of_each_rows_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "tasks" / SLUG
            folder.mkdir(parents=True)
            m = model(*BREAKER)
            key = cast("dict", bm.answer_row(m.tasks[0]))["key"]
            self.assertEqual(bm.answers_look(Path(tmp), m), {})
            lem_answers.record(folder, key, "q", "help", "words", **PHONE)
            self.assertEqual(bm.answers_look(Path(tmp), m)[SLUG][key]["option"], "help")
            m.answers = bm.answers_look(Path(tmp), m)
            self.assertEqual(bm.waits_of(m), [])

    def test_the_activity_says_what_he_picked_on_which_row(self) -> None:
        said = bm.acted_head(
            {
                "event": "board.act",
                "act": "answer",
                "key": f"skip:{SLUG}:{stamp(0)}",
                "option": "yes",
            }
        )
        self.assertEqual(
            said, "You picked Yes on “Skip the persona read?” from the board"
        )
        self.assertEqual(
            bm.acted_head({"event": "board.act", "act": "answer"}), bm.ACTED["answer"]
        )

    def test_the_fast_criterions_line_is_project_pys(self) -> None:
        self.assertEqual(bm.FAST_CRITERION, project.FAST_WAIT)


class BoardAnswer(unittest.TestCase):
    """`board_answer` of `lem project tasks`: the record of the row of the task's newest
    state block, which the task's session reads on its wake (criterion 9: the session's
    decision names it)."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name) / SLUG
        self.folder.mkdir()

    def test_criterion_9_the_answer_of_the_newest_block_is_given_and_no_other(
        self,
    ) -> None:
        block = (START + timedelta(minutes=20)).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.assertIsNone(lem_answers.answer_of_block(self.folder, SLUG, block))
        key = lem_answers.key_of(
            "breaker", SLUG, int((START + timedelta(minutes=20)).timestamp() * 1000), 1
        )
        won, made = lem_answers.record(
            self.folder, key, "Breaker 1", "drop", "another way", **PHONE
        )
        self.assertTrue(won)
        self.assertEqual(lem_answers.answer_of_block(self.folder, SLUG, block), made)
        self.assertIsNone(
            lem_answers.answer_of_block(
                self.folder,
                SLUG,
                (START + timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            )
        )
        self.assertIsNone(lem_answers.answer_of_block(self.folder, "other-task", block))

    def test_criterion_9_lem_project_tasks_gives_board_answer(self) -> None:
        repo = Path(self.tmp.name) / "repo"
        subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)

        def run(*args: str) -> str:
            return subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "src/lem/__main__.py"),
                    "project",
                    "--repo",
                    str(repo),
                    *args,
                ],
                capture_output=True,
                text=True,
                check=True,
            ).stdout

        run("init", "--base", "main")
        run("task-dir", SLUG, "--ask", "Export the notes.")
        run("state", SLUG, "planned", "the owner reads the plan")
        listed = {t["slug"]: t for t in json.loads(run("tasks"))}
        self.assertIsNone(listed[SLUG]["board_answer"])
        events = [
            json.loads(line)
            for line in (repo / ".lem/state/events.jsonl").read_text().splitlines()
        ]
        ts = [e["ts"] for e in events if e["event"] == "task.state"][-1]
        key = f"plan:{SLUG}:{lem_answers.stamp_of(ts)}"
        _, made = lem_answers.record(
            repo / ".lem/state/tasks" / SLUG,
            key,
            "Build the plan, or drop the task?",
            "build",
            "",
            **PHONE,
        )
        self.assertEqual(json.loads(run("tasks"))[0]["board_answer"], made)


if __name__ == "__main__":
    unittest.main()
