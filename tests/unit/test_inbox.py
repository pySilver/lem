"""lem_inbox.py's rules, each called in this process: which rows of "Waits for you" become things, the form
and the session each goes as, what a look sends and withdraws by the owner's mark and the Inbox's door,
the record that keeps a send single across a restart, and the wake of a task's session for a reply in a
thread whose session is gone. No case runs Plannotator: every call goes to a stand-in in this file,
which keeps each call and answers as the case sets. The server's thread runs in tests/lem-board-act.sh.

    python3 -B -m unittest discover -s tests/unit
"""

import importlib
import json
import subprocess
import sys
import tempfile
import unittest
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING
from unittest import mock

if TYPE_CHECKING:
    import lem_board_model

sys.dont_write_bytecode = True
sys.path.insert(
    0, str(Path(__file__).resolve().parents[2] / "skills" / "lem" / "scripts")
)
inbox = importlib.import_module("lem_inbox")
bm = importlib.import_module("lem_board_model")
land = importlib.import_module("land")

START = datetime(2026, 11, 22, 9, 0, tzinfo=UTC)
NOW = int((START + timedelta(hours=2)).timestamp() * 1000)
RD = "report-dates"
TAILNET = "https://mac.tail0.ts.net:50026/"
AWAY = {
    "ts": "2026-11-22T08:00:00Z",
    "event": "owner",
    "away": True,
    "words": "/lem im-away",
}
BACK = {
    "ts": "2026-11-22T10:30:00Z",
    "event": "owner",
    "away": False,
    "words": "/lem im-back",
}
# whole commits, as landing.json keeps `proposed`; the `proposed` and `merge.review` events keep their first 9 digits (land.py)
FOOTER = "abc1234def567890abc1234def567890abc12345"
FIRST = "aaa1110000000000000000000000000000000001"
SECOND = "bbb2220000000000000000000000000000000002"


def ev(minute: float, event: str, task: str = RD, **fields: object) -> dict:
    return {
        "ts": (START + timedelta(minutes=minute)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event": event,
        "task": task,
        **fields,
    }


def state(minute: float, status: str, text: str, *lines: str, task: str = RD) -> dict:
    return ev(minute, "task.state", task, status=status, text=text, lines=list(lines))


def opened(
    minute: float, session: str = "S-1", claude: str = "c-main", task: str = RD
) -> list[dict]:
    return [
        ev(minute, "session.open", task, session=session, name=task, phase="build"),
        ev(
            minute + 0.1,
            "session.transcript",
            task,
            claude=claude,
            transcript=f"/t/{claude}.jsonl",
            source="startup",
        ),
    ]


def breaker(minute: float = 2, number: int = 1, task: str = RD) -> list[dict]:
    return [
        ev(
            minute,
            "decision.breaker",
            task,
            id=number,
            kind="breaker",
            cause="criteria",
            what="The report has no place that keeps the dates",
            document=f"breaker-{number}.md",
        ),
        state(minute, "held", f"breaker {number} waits for the owner", task=task),
    ]


BREAKER = [state(0, "building", "task 1 of 2"), *opened(1), *breaker()]


def model(
    *events: dict, owner: Iterable[dict] = (), sessions: dict | None = None
) -> "lem_board_model.Model":
    m = bm.derive(list(events), list(owner), NOW)
    slugs = {e["task"] for e in events}
    m.sessions = (
        {
            slug: {
                "live": True,
                "agent": True,
                "unanswered": False,
                "session": "S-1",
                "worktree": False,
            }
            for slug in slugs
        }
        if sessions is None
        else sessions
    )
    return m


class Plannotator:
    """A stand-in for `plannotator`: keeps each call, answers `inbox status` with STATUS and each `inbox call`
    with what the case sets, and replays a send of a key it saw, as the Inbox does. A `supersedes` that is no
    list, or that names a message in ANSWERED, it refuses with the words of Plannotator 0.29.0's store
    (`normalizeSupersedes` and `planSupersede`, read in its binary on 2026-11-22)."""

    def __init__(
        self,
        status: tuple[int, dict] = (
            0,
            {
                "running": True,
                "url": "http://plannotator.localhost:50026/",
                "tailnet_url": TAILNET,
            },
        ),
    ) -> None:
        self.status = status
        self.calls: list[dict] = []
        self.keys: dict[str, dict] = {}
        self.fail: str | None = None
        self.answered: set[str] = set()
        self.thread: dict = {"thread": {"messages": []}}

    def __call__(
        self,
        args: list[str],
        input: str | None = None,  # noqa: A002 - subprocess.run's own name, which run_cli passes
        env: dict | None = None,
        cwd: str | None = None,
        **_: object,
    ) -> subprocess.CompletedProcess[str]:
        words = args[1:]
        payload = json.loads(input) if input else None
        session = words[3] if words[:3] == ["inbox", "call", "--session"] else None
        self.calls.append(
            {
                "words": words,
                "payload": payload,
                "session": session,
                "env": env,
                "cwd": cwd,
            }
        )
        if words[:2] == ["inbox", "status"]:
            code, said = self.status
            return subprocess.CompletedProcess(args, code, json.dumps(said), "")
        if self.fail:
            return subprocess.CompletedProcess(args, 1, "", self.fail)
        action = words[-2]
        if action == "read_thread":
            return subprocess.CompletedProcess(args, 0, json.dumps(self.thread), "")
        # every call but `inbox status` has its payload on stdin
        if payload is None:
            raise TypeError(f"`{' '.join(words)}` came with nothing on stdin")
        supersedes = payload.get("supersedes")
        if supersedes is not None and not isinstance(supersedes, list):
            return subprocess.CompletedProcess(
                args,
                1,
                "",
                "invalid_supersedes: supersedes: a list of ids, each `<message id>` or `<message id>/<key>`.\n",
            )
        for ref in supersedes or []:
            if ref in self.answered:
                return subprocess.CompletedProcess(
                    args,
                    1,
                    "",
                    f"invalid_supersedes: supersedes {ref}: that message has no open question. "
                    "Nothing was sent. This thread has no open questions.\n",
                )
        key = payload.get("idempotency_key")
        if key in self.keys:
            return subprocess.CompletedProcess(
                args, 0, json.dumps({**self.keys[key], "replayed": True}), ""
            )
        n = len(self.keys) + 1
        asks = ":::question" in payload.get("body", "")
        result = {
            "message_id": f"msg_{n}",
            "thread_id": f"thr_{payload.get('thread') or 'reply'}",
            "questions": [{"key": f"q-{n}"}] if asks else [],
            "url": f"http://plannotator.localhost:50026/#thread=thr_{n}",
            "replayed": False,
        }
        self.keys[key] = result
        return subprocess.CompletedProcess(args, 0, json.dumps(result), "")

    def sends(self) -> list[dict]:
        return [c for c in self.calls if c["words"][-2:-1] == ["send_message"]]

    def looked(self) -> bool:
        return any(c["words"][:2] == ["inbox", "status"] for c in self.calls)


class InFolder(unittest.TestCase):
    """Each case has a state folder of its own and a stand-in Plannotator on the watcher's PATH."""

    def setUp(self) -> None:
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.state = Path(self.folder.name) / "state"
        (self.state / "tasks" / RD).mkdir(parents=True)
        (self.state / "tasks" / RD / "breaker-1.md").write_text(
            "# The report has no place that keeps the dates\n\n## The case that broke\n",
            encoding="utf-8",
        )
        which = mock.patch.object(
            inbox.shutil,
            "which",
            lambda name: "/standin/plannotator" if name == "plannotator" else None,
        )
        which.start()
        self.addCleanup(which.stop)
        self.plannotator = Plannotator()
        self.woken: list[str] = []
        self.landings: dict[str, dict] = {}
        self.m = None

    def watcher(self, *, wakes: bool = True) -> "inbox.Watcher":
        space = SimpleNamespace(
            name="shop",
            path="/repo/shop",
            state=self.state,
            model=lambda: self.m,
            plan_of=lambda slug: None,
            landing_of=lambda slug: self.landings.get(slug, {}),
        )
        return inbox.Watcher(
            lambda: [space],
            lambda name, slug: f"https://mac.tail0.ts.net:4537/mac/{name}/tasks/{slug}",
            lambda space, slug: self.woken.append(slug) or wakes,
            runner=self.plannotator,
            log=lambda line: None,
        )

    def record(self) -> dict:
        return inbox.read_record(self.state)


class Sends(InFolder):
    def test_criterion_1_a_breaker_while_he_is_away_reaches_the_inbox_once_as_the_tasks_session(
        self,
    ) -> None:
        self.m = model(*BREAKER, owner=[AWAY])
        w = self.watcher()
        self.assertEqual([d["did"] for d in w.look()], ["sent"])
        self.assertEqual(w.look(), [])
        sends = self.plannotator.sends()
        self.assertEqual(len(sends), 1)
        sent = sends[0]
        self.assertEqual(
            (
                sent["session"],
                sent["payload"]["thread"],
                sent["payload"]["project_path"],
                sent["cwd"],
            ),
            ("claude-code:c-main", RD, "/repo/shop", "/repo/shop"),
        )
        body = sent["payload"]["body"]
        self.assertTrue(
            body.startswith("# The report has no place that keeps the dates")
        )
        self.assertIn(
            ":::question\nBreaker 1 of report-dates: help, park or drop?", body
        )
        self.assertIn("- [ ] Help\n- [ ] Park\n- [ ] Drop\n:::", body)
        self.assertIn("Stopped: the build of report-dates stopped at breaker 1", body)
        self.assertIn("https://mac.tail0.ts.net:4537/mac/shop/tasks/report-dates", body)
        self.assertEqual(self.woken, [RD])
        kept = self.record()["sent"]
        self.assertEqual(
            [
                (r["key"], r["form"], r["session"], r["message_id"], r["questions"])
                for r in kept
            ],
            [("breaker:report-dates:1", "question", "c-main", "msg_1", ["q-1"])],
        )
        self.assertNotIn("payload", kept[0])
        self.assertTrue(
            kept[0]["idempotency_key"].startswith("lem-shop-breaker:report-dates:1-")
        )

    def test_criterion_2_every_row_of_waits_for_you_is_a_thing_and_the_merge_review_and_merge_one(
        self,
    ) -> None:
        events = [
            *BREAKER,
            state(
                0,
                "held",
                'the order waits for the owner: "after the export task"',
                task="notes-in-order",
            ),
            *opened(0.5, task="notes-in-order", claude="c-o"),
            state(
                0,
                "blocked",
                "the fixture needs a login the session has not got",
                task="login-fixture",
            ),
            *opened(0.5, task="login-fixture", claude="c-l"),
            state(0, "dropped", "nobody builds it", task="gift-note"),
            state(
                1,
                "queued",
                "it starts after gift-note",
                "after: gift-note",
                task="gift-totals",
            ),
            state(
                0,
                "open",
                "the pull request waits for its merge",
                "pull request: https://github.com/acme/shop/pull/12",
                task="footer",
            ),
            ev(1, "proposed", "footer", green=True, not_green=[], tip=FOOTER[:9]),
            ev(
                2,
                "merge.review",
                "footer",
                verdict="call",
                calls=True,
                why="Verdict: call. It changes the footer of every page.",
                by="claude",
                tip=FOOTER[:9],
            ),
            *opened(0.5, task="footer", claude="c-f"),
            state(0, "building", "task 1 of 3", task="no-session"),
        ]
        sessions: dict[str, dict[str, object]] = {
            slug: {
                "live": True,
                "agent": True,
                "unanswered": False,
                "session": "S-1",
                "worktree": False,
            }
            for slug in (RD, "notes-in-order", "login-fixture", "footer")
        }
        sessions["no-session"] = {
            "live": False,
            "agent": False,
            "unanswered": False,
            "session": None,
            "worktree": False,
        }
        m = model(*events, owner=[AWAY], sessions=sessions)
        rows = bm.waits_of(m)
        self.assertIn("review:footer", [r["key"] for r in rows])
        self.landings = {"footer": {"proposed": FOOTER}}
        things = inbox.things_of(
            rows, m, bm, lambda slug: self.landings.get(slug, {}).get("proposed")
        )
        self.assertEqual(
            sorted((t["key"], t["form"]) for t in things.values()),
            [
                ("after_dropped:gift-totals", "note"),
                ("blocked:login-fixture", "question"),
                ("breaker:report-dates:1", "question"),
                ("held:notes-in-order", "question"),
                ("merge:footer", "question"),
                ("session:no-session", "note"),
            ],
        )
        self.assertEqual(things["merge:footer"]["tip"], FOOTER)
        self.m = m
        self.watcher().look()
        bodies = {c["payload"]["thread"]: c for c in self.plannotator.sends()}
        self.assertEqual(
            set(bodies),
            {
                RD,
                "notes-in-order",
                "login-fixture",
                "gift-totals",
                "footer",
                "no-session",
            },
        )
        merge = bodies["footer"]["payload"]["body"]
        self.assertIn(f"Merge pull request #12 of footer at commit {FOOTER}?", merge)
        self.assertIn("It changes the footer of every page", merge)
        self.assertIn("- [ ] Merge\n- [ ] Not now", merge)
        self.assertIn(
            "Your order: “after the export task”",
            bodies["notes-in-order"]["payload"]["body"],
        )
        self.assertIn("“no order”", bodies["notes-in-order"]["payload"]["body"])
        self.assertIn(
            ":::question-text\nlogin-fixture stopped",
            bodies["login-fixture"]["payload"]["body"],
        )
        after = bodies["gift-totals"]
        self.assertIsNone(after["session"])
        self.assertIn("start gift-totals now", after["payload"]["body"])
        self.assertNotIn(":::question", after["payload"]["body"])

    def test_criterion_3_a_thing_that_waits_when_the_mark_comes_is_sent_then(
        self,
    ) -> None:
        self.m = model(*BREAKER)
        w = self.watcher()
        self.assertEqual(w.look(), [])
        self.assertEqual(self.plannotator.calls, [])
        self.m = model(*BREAKER, owner=[AWAY])
        self.assertEqual(
            [(d["did"], d["key"]) for d in w.look()],
            [("sent", "breaker:report-dates:1")],
        )

    def test_criterion_4_with_no_away_mark_nothing_goes_to_the_inbox_and_nothing_is_asked(
        self,
    ) -> None:
        self.m = model(*BREAKER, owner=[AWAY, BACK])
        self.assertEqual(self.watcher().look(), [])
        self.assertEqual(self.plannotator.calls, [])
        self.assertFalse((self.state / inbox.RECORD).exists())

    def test_a_demo_and_a_workspace_whose_sessions_are_not_known_yet_send_nothing(
        self,
    ) -> None:
        self.m = model(*BREAKER, owner=[AWAY])
        self.m.meta["demo"] = True
        self.assertEqual(self.watcher().look(), [])
        self.m = model(*BREAKER, owner=[AWAY])
        self.m.sessions = None
        self.assertEqual(self.watcher().look(), [])
        self.assertEqual(self.plannotator.calls, [])

    def test_criterion_8_a_task_with_no_session_gets_a_note_with_no_question_and_the_boards_link(
        self,
    ) -> None:
        events = [state(0, "building", "task 1 of 2"), *breaker()]
        self.m = model(
            *events,
            owner=[AWAY],
            sessions={
                RD: {
                    "live": False,
                    "agent": False,
                    "unanswered": False,
                    "session": None,
                    "worktree": False,
                }
            },
        )
        self.watcher().look()
        sends = self.plannotator.sends()
        self.assertEqual(
            len(sends), 1, "the session's own note stands for the task: one message"
        )
        sent = sends[0]
        self.assertIsNone(sent["session"])
        self.assertEqual(
            sent["payload"]["body"],
            "report-dates has no session; open it on the board: "
            "[report-dates on the board](https://mac.tail0.ts.net:4537/mac/shop/tasks/report-dates)",
        )
        self.assertEqual(self.record()["sent"][0]["form"], "note")
        self.assertEqual(self.woken, [])

    def test_a_fork_is_not_the_tasks_session_and_a_session_that_does_not_answer_gets_a_note(
        self,
    ) -> None:
        events = [
            *BREAKER,
            ev(
                3,
                "session.transcript",
                RD,
                claude="c-fork",
                transcript="/t/f.jsonl",
                source="fork",
            ),
        ]
        m = model(*events, owner=[AWAY])
        self.assertEqual(inbox.claude_of(m.tasks[0]), "c-main")
        thing = inbox.things_of(bm.waits_of(m), m, bm)["breaker:report-dates:1"]
        self.assertEqual((thing["form"], thing["session"]), ("question", "c-main"))
        deaf = model(
            *BREAKER,
            owner=[AWAY],
            sessions={
                RD: {
                    "live": True,
                    "agent": True,
                    "unanswered": True,
                    "session": "S-1",
                    "worktree": False,
                }
            },
        )
        self.assertEqual(
            [
                (t["key"], t["form"])
                for t in inbox.things_of(bm.waits_of(deaf), deaf, bm).values()
            ],
            [("deaf:report-dates", "note")],
        )

    def test_the_calls_keep_the_data_folder_and_drop_the_variables_that_name_a_session(
        self,
    ) -> None:
        env = {
            "HOME": "/Users/o",
            "PATH": "/bin",
            "XDG_DATA_HOME": "/d",
            "PLANNOTATOR_DATA_DIR": "/p",
            "PLANNOTATOR_SESSION_TAG": "claude-code:x",
            "CLAUDECODE": "1",
            "CODEX_THREAD_ID": "t",
            "T3CODE_THREAD_ID": "t3",
            "QWEN_CODE_SESSION_ID": "q",
            "DSH_SHELL": "1",
        }
        self.assertEqual(
            inbox.environment(env),
            {
                "HOME": "/Users/o",
                "PATH": "/bin",
                "XDG_DATA_HOME": "/d",
                "PLANNOTATOR_DATA_DIR": "/p",
            },
        )
        self.m = model(*BREAKER, owner=[AWAY])
        with mock.patch.dict(
            inbox.os.environ,
            {
                "PLANNOTATOR_SESSION_TAG": "claude-code:the-servers-own",
                "CLAUDECODE": "1",
            },
        ):
            self.watcher().look()
        self.assertTrue(
            all(
                "PLANNOTATOR_SESSION_TAG" not in c["env"]
                and "CLAUDECODE" not in c["env"]
                for c in self.plannotator.calls
            )
        )


class Door(InFolder):
    def test_criterion_7_no_inbox_or_no_tailnet_address_sends_nothing_and_keeps_why(
        self,
    ) -> None:
        self.m = model(*BREAKER, owner=[AWAY])
        for status, why in (
            ((1, {"running": False, "url": None}), inbox.NOT_RUNNING),
            ((2, {}), inbox.NOT_ANSWERING),
            (
                (
                    0,
                    {
                        "running": True,
                        "url": "http://plannotator.localhost:50026/",
                        "tailnet_url": None,
                    },
                ),
                inbox.NO_TAILNET,
            ),
        ):
            with self.subTest(why=why):
                self.plannotator.status = status
                self.assertEqual(self.watcher().look(), [])
                self.assertEqual(self.plannotator.sends(), [])
                self.assertEqual(self.record()["why"], why)
        with mock.patch.object(inbox.shutil, "which", lambda name: None):
            self.assertEqual(self.watcher().look(), [])
        self.assertEqual(
            (self.record()["why"], self.record()["running"]),
            (inbox.NOT_INSTALLED, False),
        )

    def test_a_failed_call_is_kept_as_the_problem_and_the_next_look_sends_the_same_key_once(
        self,
    ) -> None:
        self.m = model(*BREAKER, owner=[AWAY])
        lines = []
        w = self.watcher()
        w.log = lines.append
        self.plannotator.fail = "inbox_unreachable: the Inbox did not answer"
        self.assertEqual(w.look(), [])
        record = self.record()
        self.assertIn("inbox_unreachable", record["problem"])
        self.assertEqual(len(lines), 1)
        pending = record["sent"][0]
        self.assertIsNone(pending.get("message_id"))
        self.assertEqual(
            pending["payload"]["idempotency_key"], pending["idempotency_key"]
        )
        self.plannotator.fail = None
        w.look()
        keys = [c["payload"]["idempotency_key"] for c in self.plannotator.sends()]
        self.assertEqual(keys, [pending["idempotency_key"]] * 2)
        record = self.record()
        self.assertEqual(
            (record["problem"], record["sent"][0]["message_id"], len(record["sent"])),
            (None, "msg_1", 1),
        )


class Withdraws(InFolder):
    def sent_breaker(self) -> "inbox.Watcher":
        self.m = model(*BREAKER, owner=[AWAY])
        w = self.watcher()
        w.look()
        return w

    def test_criterion_5_an_answer_at_the_mac_withdraws_the_question_as_the_same_session(
        self,
    ) -> None:
        w = self.sent_breaker()
        # he answered at the Mac: the breaker is helped, and its row leaves the list
        self.m = model(
            *BREAKER,
            ev(
                4,
                "decision.taken",
                id=2,
                what="Where the dates go",
                chose="A",
                why="his word",
                by="owner",
                breaker=1,
            ),
            state(4, "building", "task 1 of 2: the build goes on"),
            owner=[AWAY],
        )
        self.assertEqual([d["did"] for d in w.look()], ["withdrew"])
        withdrawal = self.plannotator.sends()[-1]
        self.assertEqual(withdrawal["session"], "claude-code:c-main")
        self.assertEqual(
            {k: withdrawal["payload"][k] for k in ("body", "reply_to", "supersedes")},
            {"body": inbox.WITHDRAWN, "reply_to": "msg_1", "supersedes": ["msg_1"]},
        )
        self.assertEqual(self.record()["sent"], [])
        self.assertEqual(w.look(), [])

    def test_a_question_he_answered_in_the_inbox_gets_nothing_and_leaves_the_record(
        self,
    ) -> None:
        w = self.sent_breaker()
        self.plannotator.answered.add("msg_1")
        self.m = model(
            *BREAKER,
            state(4, "parked", "the owner parked it from the Inbox"),
            owner=[AWAY],
        )
        self.assertEqual([d["did"] for d in w.look()], ["answered"])
        self.assertEqual((self.record()["sent"], self.record()["problem"]), ([], None))

    def test_criterion_9_at_im_back_the_open_question_stays_and_a_new_session_gets_nothing_new(
        self,
    ) -> None:
        w = self.sent_breaker()
        self.m = model(*BREAKER, owner=[AWAY, BACK])
        self.assertEqual(w.look(), [])
        # the task's session changes after his /lem im-back: the question stays where it is
        self.m = model(
            *BREAKER, *opened(40, session="S-2", claude="c-new"), owner=[AWAY, BACK]
        )
        self.assertEqual(w.look(), [])
        self.assertEqual(len(self.plannotator.sends()), 1)
        self.assertEqual(self.record()["sent"][0]["session"], "c-main")
        # his reply in the thread of the gone session wakes the task's live session, once
        self.plannotator.thread = {
            "thread": {
                "messages": [
                    {"id": "msg_1", "author": {"kind": "agent"}},
                    {"id": "msg_his", "author": {"kind": "person"}},
                ]
            }
        }
        self.assertEqual([d["did"] for d in w.look()], ["woke"])
        self.assertEqual(w.look(), [])
        self.assertEqual(self.woken, [RD, RD])
        reads = [
            c for c in self.plannotator.calls if c["words"][-2:-1] == ["read_thread"]
        ]
        self.assertTrue(reads and all(c["session"] is None for c in reads))
        self.assertEqual(self.record()["sent"][0]["woke"], ["msg_his"])

    def test_while_away_a_new_session_a_newer_block_and_a_new_tip_each_withdraw_and_send_again(
        self,
    ) -> None:
        w = self.sent_breaker()
        self.m = model(
            *BREAKER, *opened(40, session="S-2", claude="c-new"), owner=[AWAY]
        )
        self.assertEqual([d["did"] for d in w.look()], ["withdrew", "sent"])
        self.assertEqual(
            [c["session"] for c in self.plannotator.sends()],
            ["claude-code:c-main", "claude-code:c-main", "claude-code:c-new"],
        )
        first, last = (
            self.plannotator.sends()[0]["payload"]["idempotency_key"],
            self.plannotator.sends()[-1]["payload"]["idempotency_key"],
        )
        self.assertNotEqual(first, last)
        # decision 5: a blocked task that stops again for a new reason keeps its row key and time, and its new block is a new thing
        blocked = [
            state(0, "building", "task 1 of 2"),
            *opened(1),
            state(5, "blocked", "the fixture needs a login"),
        ]
        self.m = model(*blocked, owner=[AWAY])
        w.look()
        before = len(self.plannotator.sends())
        self.m = model(
            *blocked,
            state(6, "blocked", "the fixture needs a second login"),
            owner=[AWAY],
        )
        self.assertEqual([d["did"] for d in w.look()], ["withdrew", "sent"])
        self.assertIn("a second login", self.plannotator.sends()[-1]["payload"]["body"])
        self.assertEqual(len(self.plannotator.sends()), before + 2)

    def test_a_new_proposal_is_a_new_merge_question_and_a_refused_merge_a_note(
        self,
    ) -> None:
        footer = [
            *opened(0),
            state(
                1,
                "open",
                "the pull request waits",
                "pull request: https://github.com/acme/shop/pull/12",
                task=RD,
            ),
            ev(1, "proposed", green=True, not_green=[], tip=FIRST[:9]),
            ev(
                2,
                "merge.review",
                verdict="call",
                calls=True,
                why="Verdict: call. It is wide.",
                tip=FIRST[:9],
            ),
        ]
        self.landings = {RD: {"proposed": FIRST}}
        self.m = model(*footer, owner=[AWAY])
        w = self.watcher()
        w.look()
        self.assertIn(
            f"at commit {FIRST}?", self.plannotator.sends()[-1]["payload"]["body"]
        )
        again = [
            *footer,
            ev(3, "proposed", green=True, not_green=[], tip=SECOND[:9]),
            ev(
                4,
                "merge.review",
                verdict="call",
                calls=True,
                why="Verdict: call. Still wide.",
                tip=SECOND[:9],
            ),
        ]
        self.landings = {RD: {"proposed": SECOND}}
        self.m = model(*again, owner=[AWAY])
        self.assertEqual([d["did"] for d in w.look()], ["withdrew", "sent"])
        self.assertIn(
            f"at commit {SECOND}?", self.plannotator.sends()[-1]["payload"]["body"]
        )
        self.assertEqual(self.record()["sent"][0]["tip"], SECOND)
        refused = [
            *again,
            ev(
                5,
                "merge.refused",
                said="the base branch needs a review",
                by="owner",
                tip=SECOND[:9],
                **{"from": "github"},
            ),
        ]
        self.m = model(*refused, owner=[AWAY])
        self.assertEqual([d["did"] for d in w.look()], ["withdrew", "sent"])
        note = self.plannotator.sends()[-1]
        self.assertIsNone(note["session"])
        self.assertIn(
            "did not go through: the base branch needs a review",
            note["payload"]["body"],
        )
        self.assertNotIn(":::question", note["payload"]["body"])

    def test_after_im_back_a_question_its_row_no_longer_asks_is_withdrawn_and_nothing_new_is_sent(
        self,
    ) -> None:
        footer = [
            *opened(0),
            state(
                1,
                "open",
                "the pull request waits",
                "pull request: https://github.com/acme/shop/pull/12",
                task=RD,
            ),
            ev(1, "proposed", green=True, not_green=[], tip=FIRST[:9]),
            ev(
                2,
                "merge.review",
                verdict="call",
                calls=True,
                why="Verdict: call.",
                tip=FIRST[:9],
            ),
        ]
        self.landings = {RD: {"proposed": FIRST}}
        self.m = model(*footer, owner=[AWAY])
        w = self.watcher()
        w.look()
        self.m = model(
            *footer,
            ev(
                5,
                "merge.refused",
                said="a review is required",
                by="owner",
                tip=FIRST[:9],
                **{"from": "github"},
            ),
            owner=[AWAY, BACK],
        )
        self.assertEqual([d["did"] for d in w.look()], ["withdrew"])
        self.assertEqual(
            (len(self.plannotator.sends()), self.record()["sent"]), (2, [])
        )


class ReviewOne(InFolder):
    """The findings of the first review of away-questions-reach-phone, each on the input it named."""

    def test_a_failed_send_goes_again_only_while_he_is_away_for_the_same_thing_and_wakes_the_session(
        self,
    ) -> None:
        # finding 1: after /lem im-back, a send that failed is forgotten, not posted and withdrawn
        self.m = model(*BREAKER, owner=[AWAY])
        w = self.watcher()
        self.plannotator.fail = "inbox_unreachable: the Inbox did not answer"
        w.look()
        self.plannotator.fail = None
        self.m = model(*BREAKER, owner=[AWAY, BACK])
        self.assertEqual([d["did"] for d in w.look()], ["forgot"])
        self.assertEqual(
            (len(self.plannotator.sends()), self.record()["sent"]), (1, [])
        )
        calls = len(self.plannotator.calls)
        self.assertEqual(w.look(), [])
        self.assertEqual(
            len(self.plannotator.calls),
            calls,
            "with nothing in the record and no mark, no look asks the Inbox",
        )
        # a refusal that never clears is forgotten once the row left, and the row's next thing is sent
        self.m = model(*BREAKER, owner=[AWAY])
        self.plannotator.fail = "invalid_request: the body is too long"
        w.look()
        self.m = model(
            *BREAKER,
            ev(
                4,
                "decision.taken",
                id=2,
                what="Where the dates go",
                chose="A",
                why="his word",
                by="owner",
                breaker=1,
            ),
            state(4, "building", "task 1 of 2: the build goes on"),
            *breaker(6, 2),
            owner=[AWAY],
        )
        self.plannotator.fail = None
        self.assertEqual(
            [(d["did"], d["key"]) for d in w.look()],
            [("forgot", "breaker:report-dates:1"), ("sent", "breaker:report-dates:2")],
        )
        # finding 6: a question that a later look sends again wakes the task's session
        self.woken.clear()
        self.m = model(*BREAKER, *breaker(8, 3), owner=[AWAY])
        self.plannotator.fail = "inbox_unreachable: the Inbox did not answer"
        w.look()
        self.plannotator.fail = None
        self.assertIn(
            ("sent", "breaker:report-dates:3"), [(d["did"], d["key"]) for d in w.look()]
        )
        self.assertEqual(self.woken, [RD])

    def test_the_merge_question_names_the_whole_commit_that_lem_land_merge_takes(
        self,
    ) -> None:
        # finding 2: the `proposed` event keeps 9 digits; the question names the 40 of landing.json
        footer = [
            *opened(0),
            state(
                1,
                "open",
                "the pull request waits",
                "pull request: https://github.com/acme/shop/pull/12",
            ),
            ev(1, "proposed", green=True, not_green=[], tip=FOOTER[:9]),
            ev(
                2,
                "merge.review",
                verdict="call",
                calls=True,
                why="Verdict: call.",
                tip=FOOTER[:9],
            ),
        ]
        self.landings = {RD: {"proposed": FOOTER}}
        self.m = model(*footer, owner=[AWAY])
        self.watcher().look()
        body = self.plannotator.sends()[-1]["payload"]["body"]
        named = body.split("at commit ", 1)[1].split("?", 1)[0]
        self.assertIsNone(land.expected_refusal(named, FOOTER, RD))
        self.assertEqual(self.record()["sent"][0]["tip"], FOOTER)
        # a landing record of another proposal, or none, names no commit: a note, and no merge question
        for landing in ({"proposed": SECOND}, {}):
            with self.subTest(landing=landing):
                m = model(*footer, owner=[AWAY])
                thing = inbox.things_of(
                    bm.waits_of(m),
                    m,
                    bm,
                    lambda slug, landing=landing: landing.get("proposed"),
                )[f"merge:{RD}"]
                self.assertEqual((thing["form"], thing["asks"]), ("note", False))

    def test_after_im_back_a_session_that_ends_leaves_the_open_question(self) -> None:
        # finding 3: the session's own row stands for the task, and the breaker behind it still waits
        w = self.watcher()
        self.m = model(*BREAKER, owner=[AWAY])
        w.look()
        gone = {
            RD: {
                "live": False,
                "agent": False,
                "unanswered": False,
                "session": None,
                "worktree": True,
            }
        }
        self.m = model(*BREAKER, owner=[AWAY, BACK], sessions=gone)
        self.assertIn("breaker:report-dates:1", [r["key"] for r in bm.waits_of(self.m)])
        self.assertEqual(w.look(), [])
        self.assertEqual(
            [(r["key"], r["message_id"]) for r in self.record()["sent"]],
            [("breaker:report-dates:1", "msg_1")],
        )
        self.assertEqual(len(self.plannotator.sends()), 1)

    def test_a_withdrawal_says_where_the_wait_went_without_naming_the_mac(self) -> None:
        # finding 4: a row that left says it was settled outside the thread; a changed thing, that a newer message follows
        w = self.watcher()
        self.m = model(*BREAKER, owner=[AWAY])
        w.look()
        self.m = model(
            *BREAKER, *opened(40, session="S-2", claude="c-new"), owner=[AWAY]
        )
        w.look()
        self.assertEqual(self.plannotator.sends()[1]["payload"]["body"], inbox.REPLACED)
        self.m = model(
            *BREAKER,
            *opened(40, session="S-2", claude="c-new"),
            state(41, "parked", "the owner parked it from the board"),
            owner=[AWAY],
        )
        w.look()
        self.assertEqual(
            self.plannotator.sends()[-1]["payload"]["body"], inbox.WITHDRAWN
        )
        self.assertNotIn("Mac", inbox.WITHDRAWN + inbox.REPLACED)

    def test_a_session_that_has_not_logged_its_claude_session_yet_gets_nothing_until_it_does(
        self,
    ) -> None:
        # finding 7: a new session.open with no session.transcript yet, within the board's grace, is no note
        fresh = [
            state(0, "building", "task 1 of 2"),
            *opened(1),
            *breaker(),
            ev(119, "session.open", session="S-2", name=RD, phase="build"),
        ]
        self.m = model(*fresh, owner=[AWAY])
        self.assertEqual(self.watcher().look(), [])
        self.assertEqual(self.plannotator.sends(), [])
        # past the grace, a live session with no Claude Code session on record gets the note
        late = [
            state(0, "building", "task 1 of 2"),
            *opened(1),
            *breaker(),
            ev(100, "session.open", session="S-2", name=RD, phase="build"),
        ]
        self.m = model(*late, owner=[AWAY])
        self.watcher().look()
        self.assertEqual([c["session"] for c in self.plannotator.sends()], [None])


class ReviewTwo(InFolder):
    """The findings of the second review of away-questions-reach-phone and of its merge review, each on the
    input it named."""

    def test_a_refusal_of_the_withdrawals_shape_is_a_problem_and_never_his_answer(
        self,
    ) -> None:
        # finding 1: only a refusal that the message has no open question is "he answered it"
        w = self.watcher()
        self.m = model(*BREAKER, owner=[AWAY])
        w.look()
        self.m = model(
            *BREAKER,
            state(4, "parked", "the owner parked it from the board"),
            owner=[AWAY],
        )
        self.plannotator.fail = "invalid_supersedes: supersedes msg_1 is in another thread (thr_x): only questions of the thread this message lands in can be superseded."
        self.assertEqual(w.look(), [])
        record = self.record()
        self.assertEqual([r["key"] for r in record["sent"]], ["breaker:report-dates:1"])
        self.assertIn("invalid_supersedes", record["problem"])
        self.plannotator.fail = None
        self.assertEqual([d["did"] for d in w.look()], ["withdrew"])
        self.assertEqual(
            self.plannotator.sends()[-1]["payload"]["supersedes"], ["msg_1"]
        )

    def test_while_away_with_no_tailnet_address_a_new_session_keeps_the_question_until_one_can_follow(
        self,
    ) -> None:
        # finding 2: no withdrawal says "settled" of a breaker that still waits
        w = self.watcher()
        self.m = model(*BREAKER, owner=[AWAY])
        w.look()
        self.plannotator.status = (
            0,
            {
                "running": True,
                "url": "http://plannotator.localhost:50026/",
                "tailnet_url": None,
            },
        )
        self.m = model(
            *BREAKER, *opened(40, session="S-2", claude="c-new"), owner=[AWAY]
        )
        self.assertEqual(w.look(), [])
        self.assertEqual(len(self.plannotator.sends()), 1)
        self.assertEqual(
            [(r["key"], r["session"]) for r in self.record()["sent"]],
            [("breaker:report-dates:1", "c-main")],
        )
        # its session row while the door is closed: the question behind it stays too
        gone = {
            RD: {
                "live": False,
                "agent": False,
                "unanswered": False,
                "session": None,
                "worktree": True,
            }
        }
        self.m = model(*BREAKER, owner=[AWAY], sessions=gone)
        self.assertEqual(w.look(), [])
        self.assertEqual(len(self.plannotator.sends()), 1)
        # the tailnet address back: the question is replaced by the one of the new session
        self.plannotator.status = (
            0,
            {
                "running": True,
                "url": "http://plannotator.localhost:50026/",
                "tailnet_url": TAILNET,
            },
        )
        self.m = model(
            *BREAKER, *opened(40, session="S-2", claude="c-new"), owner=[AWAY]
        )
        self.assertEqual([d["did"] for d in w.look()], ["withdrew", "sent"])
        self.assertEqual(self.plannotator.sends()[1]["payload"]["body"], inbox.REPLACED)
        self.assertEqual(self.plannotator.sends()[-1]["session"], "claude-code:c-new")

    def test_a_task_whose_session_stopped_gets_a_note_that_asks_nothing(self) -> None:
        # the merge review's finding 3: the row "stopped" of the guard of a stopped session asks nothing, as "session"
        stuck = [
            state(0, "building", "task 1 of 2"),
            *opened(1),
            ev(60, "session.stopped", session="S-1"),
        ]
        self.m = model(*stuck, owner=[AWAY])
        self.assertEqual([r["kind"] for r in bm.waits_of(self.m)], ["stopped"])
        self.assertEqual([d["did"] for d in self.watcher().look()], ["sent"])
        sent = self.plannotator.sends()[0]
        self.assertIsNone(sent["session"])
        self.assertEqual(
            sent["payload"]["body"],
            "The session of report-dates stopped, and so did the fresh one that took its place. Open a fresh one on the board: "
            "[report-dates on the board](https://mac.tail0.ts.net:4537/mac/shop/tasks/report-dates)",
        )
        self.assertEqual(self.woken, [])
        kept = self.record()
        self.assertEqual(
            [(r["form"], r["asks"]) for r in kept["sent"]], [("note", False)]
        )
        self.m.inbox = kept
        said = bm.inbox_of(self.m.tasks[0], self.m)
        self.assertEqual((said["asks"], said["gone"]), (False, True))

    def test_the_note_of_a_stop_lem_cannot_read_says_so_and_names_no_fresh_session_that_took_its_place(
        self,
    ) -> None:
        stuck = [
            state(0, "building", "task 1 of 2"),
            *opened(1),
            ev(46, "session.wake", session="S-1", why="status", unread=True),
            ev(56, "session.stopped", session="S-1", unread=True),
        ]
        self.m = model(*stuck, owner=[AWAY])
        self.assertEqual([r["kind"] for r in bm.waits_of(self.m)], ["stopped"])
        self.assertEqual([d["did"] for d in self.watcher().look()], ["sent"])
        sent = self.plannotator.sends()[0]
        self.assertEqual(
            sent["payload"]["body"],
            "The session of report-dates stopped, and Lem cannot read it: no event of the task came after the status message. "
            "Lem opens no second session by itself. Open a fresh one on the board: "
            "[report-dates on the board](https://mac.tail0.ts.net:4537/mac/shop/tasks/report-dates)",
        )
        self.assertEqual(self.woken, [])


class HeldBack(InFolder):
    """A row that the task's working session holds back keeps its sent thing as it stands (decision 5 of
    waits-for-you-only-when-it-waits): the Inbox's own wake starts the session's turn on the question, and
    neither that turn nor its end sends, withdraws or forgets anything. The held task is a breaker's: while
    the owner is away, Lem settles an interview and criteria without him (`goes_on_of`), and they are no row."""

    def turn(
        self, turn: str | None, owner: Iterable[dict] = (AWAY,)
    ) -> "lem_board_model.Model":
        m = bm.derive(list(BREAKER), list(owner), NOW)
        bm.put_sessions(
            m,
            {
                RD: {
                    "live": True,
                    "agent": True,
                    "unanswered": False,
                    "session": "S-1",
                    "worktree": False,
                    "turn": turn,
                }
            },
        )
        return m

    def test_the_question_stays_open_while_the_woken_turn_runs_and_nothing_is_sent_when_it_ends(
        self,
    ) -> None:
        self.m = self.turn(None)
        w = self.watcher()
        self.assertEqual([d["did"] for d in w.look()], ["sent"])
        self.assertEqual(self.woken, [RD])
        before = self.record()["sent"]
        self.assertEqual(
            [(r["key"], r["form"], r["message_id"]) for r in before],
            [(f"breaker:{RD}:1", "question", "msg_1")],
        )
        # the wake started the session's turn on his help: no row, and the question stays open as it was sent
        self.m = self.turn("runs")
        self.assertEqual(
            (bm.waits_of(self.m), bm.held_back(self.m)), ([], {f"breaker:{RD}:1"})
        )
        self.assertEqual(w.look(), [])
        self.assertEqual(self.record()["sent"], before)
        # the turn ends with the same block: the row is the same thing, and nothing goes again
        self.m = self.turn("ended")
        self.assertEqual(w.look(), [])
        self.assertEqual(
            (len(self.plannotator.sends()), self.woken, self.record()["sent"]),
            (1, [RD], before),
        )

    def test_a_held_back_thing_is_neither_withdrawn_forgotten_nor_sent_away_or_not(
        self,
    ) -> None:
        asked = {
            "key": "held:a",
            "task": "a",
            "kind": "held",
            "form": "question",
            "asks": True,
            "session": "c",
            "tip": None,
            "block": 1,
            "message_id": "m1",
        }
        noted = {**asked, "key": "held:b", "task": "b", "form": "note", "session": None}
        unsent = {
            **asked,
            "key": "held:c",
            "task": "c",
            "message_id": None,
            "payload": {"body": "x"},
        }
        none = {
            "withdraw": [],
            "replaced": set(),
            "forget": [],
            "retry": [],
            "send": [],
        }
        for away in (True, False):
            with self.subTest(away=away):
                self.assertEqual(
                    inbox.plan(
                        {},
                        [asked, noted, unsent],
                        away=away,
                        door=True,
                        held={"held:a", "held:b", "held:c"},
                    ),
                    none,
                )
        # the same record with no row held back: the question is withdrawn, the note and the unsent one forgotten
        steps = inbox.plan({}, [asked, noted, unsent], away=True, door=True)
        self.assertEqual(
            (
                [r["key"] for r in steps["withdraw"]],
                [r["key"] for r in steps["forget"]],
            ),
            (["held:a"], ["held:b", "held:c"]),
        )


if __name__ == "__main__":
    unittest.main()
