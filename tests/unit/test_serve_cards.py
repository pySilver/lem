"""serve.py's answer to a `lem-ask` card of a task's session (the task
board-answers-a-card): which answer the board takes and what it records (`act_card`,
`card_refusal`), the device a request names (`device_of`), agterm's word before it takes
one (`agterm_card_refusal`), the policy of the card's page (`card_policy`), and that the
server holds no call that answers, closes or types into a session. The routes run in
tests/lem-serve.sh and tests/lem-board-act.sh, with a server.

    python3 -B -m unittest discover -s tests/unit
"""

import ast
import base64
import email.message
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast
from unittest import mock

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from lem import board_model as bm
from lem import cards as lem_cards
from lem import serve

START = datetime(2026, 11, 23, 15, 0, tzinfo=UTC)
NOW = int((START + timedelta(hours=1)).timestamp() * 1000)
SLUG, PAGE = "export-notes", "P-1"
IPHONE = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/18.1 Mobile/15E148 Safari/604.1"
)
MAC = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like "
    "Gecko) Version/18.1 Safari/605.1.15"
)
CARD = {
    "page": PAGE,
    "session": "S1",
    "at": "2026-11-23T15:02:00Z",
    "chat": True,
    "questions": [
        {
            "id": "answer",
            "prompt": "Keep the empty cell?",
            "mode": "single",
            "optional": False,
            "options": [
                {"id": "yes", "label": "Yes"},
                {"id": "no", "label": "No, write a dash"},
            ],
        }
    ],
}


def ev(minute: float, event: str, **fields: object) -> dict:
    return {
        "ts": (START + timedelta(minutes=minute)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event": event,
        "task": SLUG,
        **fields,
    }


def picked(*ids: str, text: str | None = None, labels: list | None = None) -> dict:
    one: dict[str, object] = {
        "selected": list(ids),
        "labels": labels if labels is not None else list(ids),
    }
    if text is not None:
        one["text"] = text
    return {"status": "answered", "answers": {"answer": one}}


def headers(**given: str) -> email.message.Message:
    message = email.message.Message()
    for key, value in given.items():
        message[key.replace("_", "-")] = value
    return message


class Workspace:
    """The workspace of the server as `act_card` reads it: its state folder, its model,
    and its count of acts."""

    def __init__(self, state: Path, session: str = "S1") -> None:
        self.state = state
        self.acted = 0
        self.session = session

    def model(self) -> "bm.Model":
        m = bm.derive(
            [
                ev(0, "task.state", status="building", text="task 1 of 2", lines=[]),
                ev(1, "session.open", session="S1", name=SLUG),
                ev(2, "card.asked", page=PAGE, prompt="Keep the empty cell?"),
            ],
            [],
            NOW,
        )
        m.sessions = {
            SLUG: {
                "live": True,
                "agent": True,
                "unanswered": False,
                "session": self.session,
            }
        }
        m.cards = bm.cards_look(self.state, m)
        return m


class Answer(unittest.TestCase):
    """`act_card` over a task folder that holds the card, with agterm's word and the log
    of `board.act` stood in for."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state = Path(self.tmp.name) / ".lem" / "state"
        self.folder = self.state / "tasks" / SLUG
        (self.folder / "cards").mkdir(parents=True)
        lem_cards.card_file(self.folder, PAGE).write_text(json.dumps(CARD))
        lem_cards.html_file(self.folder, PAGE).write_text(
            "<!doctype html><title>card</title>"
        )
        self.agterm = None
        self.logged: list = []
        for target, value in (
            (serve, "agterm_card_refusal"),
            (serve, "asked_from"),
            (lem_cards, "log"),
        ):
            patcher = mock.patch.object(
                target,
                value,
                side_effect={
                    "agterm_card_refusal": lambda page: self.agterm,
                    "asked_from": lambda ws, slug, act, via: (
                        self.logged.append((act, via)) or ""
                    ),
                    "log": lambda task, event, fields: self.logged.append(
                        (event, fields)
                    ),
                }[value],
            )
            patcher.start()
            self.addCleanup(patcher.stop)

    def answer(
        self, given: dict, via: str = "door", device: str = "phone", session: str = "S1"
    ) -> tuple[int, str | None]:
        return serve.act_card(
            cast("serve.Workspace", Workspace(self.state, session)),
            SLUG,
            PAGE,
            given,
            via,
            device,
            IPHONE,
        )

    def end(self) -> dict | None:
        return lem_cards.ended(self.folder, PAGE)

    def test_criterion_2_and_9_a_pick_with_a_note_is_on_record_as_the_owners_with_the_card_its_option_note_time_and_device(
        self,
    ) -> None:
        status, said = self.answer(
            picked(
                "no",
                text="a dash, as in the invoice export",
                labels=["what the page says"],
            )
        )
        self.assertEqual((status, said), (200, serve.ON_RECORD))
        end = cast("dict", self.end())
        self.assertEqual(
            {
                key: end[key]
                for key in ("page", "status", "from", "via", "device", "agent")
            },
            {
                "page": PAGE,
                "status": "answered",
                "from": "board",
                "via": "door",
                "device": "phone",
                "agent": IPHONE,
            },
        )
        self.assertEqual(
            end["answer"],
            {
                "status": "answered",
                "answers": {
                    "answer": {
                        "selected": ["no"],
                        "labels": ["No, write a dash"],
                        "text": "a dash, as in the invoice export",
                    }
                },
            },
        )
        self.assertRegex(end["at"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
        self.assertIn(
            (
                "card.answered",
                {"page": PAGE, "from": "board", "via": "door", "device": "phone"},
            ),
            self.logged,
        )
        self.assertIn(("answer", bm.VIA["door"]), self.logged)
        self.assertEqual(
            [
                w["key"]
                for w in bm.waits_of(Workspace(self.state).model())
                if w["kind"] == "card"
            ],
            [],
        )

    def test_criterion_3_a_note_with_no_pick_and_a_wish_to_talk_are_refused_and_the_card_stays(
        self,
    ) -> None:
        for given in (
            picked(text="why not both?"),
            {"status": "chat", "text": "why not both?"},
        ):
            self.assertEqual(self.answer(given), (422, serve.TO_THE_SESSION))
        self.assertIsNone(self.end())
        self.assertEqual(self.logged, [])
        self.assertEqual(
            [w["key"] for w in bm.waits_of(Workspace(self.state).model())],
            [f"card:{SLUG}:{PAGE}"],
        )

    def test_criterion_4_an_answer_after_the_sessions_pick_is_refused_with_what_took_effect(
        self,
    ) -> None:
        lem_cards.end(
            self.folder, PAGE, "answered", "session", picked("yes", labels=["Yes"])
        )
        status, said = self.answer(picked("no"))
        self.assertEqual(status, 409)
        self.assertRegex(
            cast("str", said),
            r"^Yes was taken in the session at \d\d:\d\d: nothing was recorded\.$",
        )
        self.assertEqual(cast("dict", self.end())["from"], "session")

    def test_criterion_4_an_answer_agterm_holds_from_the_mac_counts_first(self) -> None:
        self.agterm = (
            "An answer was given on the card at the Mac: the task’s session takes it, "
            "and nothing was recorded here."
        )
        self.assertEqual(self.answer(picked("no")), (409, self.agterm))
        self.assertIsNone(self.end())

    def test_a_dismissal_of_the_page_records_nothing(self) -> None:
        self.assertEqual(self.answer({"status": "dismissed"}), (204, None))
        self.assertIsNone(self.end())

    def test_a_card_of_a_session_that_no_longer_runs_takes_no_answer(self) -> None:
        status, said = self.answer(picked("no"), session="S2")
        self.assertEqual(status, 409)
        self.assertIn("no longer runs", cast("str", said))
        self.assertIsNone(self.end())

    def read(self, body: str) -> object:
        """The answer as the server's read of a card's body takes it, one frame above
        `act_card`, as `Handler.card_answer` is (`lem_cards.whole` of the decode)."""
        return lem_cards.whole(json.loads(body))

    def test_an_answer_the_read_takes_and_the_end_cannot_walk_is_refused_as_no_json(
        self,
    ) -> None:
        # the deepest answer the read takes, searched down from the interpreter's
        # limit: the end walks it two frames deeper (`lem_cards.end`)
        given: object = None
        depth = sys.getrecursionlimit()
        while given is None and depth > 0:
            body = (
                '{"status": "answered", "answers": {"answer": {"selected": ["no"], '
                f'"extra": {"[" * depth + "]" * depth}}}}}}}'
            )
            try:
                given = self.read(body)
            except RecursionError:
                depth -= 1
        self.assertEqual(
            self.answer(cast("dict", given)), (400, serve.NO_CARD_JSON), depth
        )
        self.assertIsNone(self.end())

    def test_two_answers_of_the_board_at_once_record_one(self) -> None:
        first = self.answer(picked("no"))
        second = self.answer(picked("yes"))
        self.assertEqual(first[0], 200)
        self.assertEqual(second[0], 409)
        self.assertIn(
            "No, write a dash was taken on the board at", cast("str", second[1])
        )


class Refusal(unittest.TestCase):
    """`card_refusal`: the page's own rule of what an answer is (`valid` and `finish`
    in `runtime/ask.js`)."""

    TUNE = {
        "questions": [
            {
                "id": "q1",
                "mode": "tune",
                "optional": False,
                "options": [{"id": "calm", "label": "Calm"}],
            },
            {
                "id": "q2",
                "mode": "multi",
                "optional": True,
                "options": [{"id": "a", "label": "A"}, {"id": "b", "label": "B"}],
            },
            {"id": "q3", "mode": "text", "optional": False, "options": []},
        ]
    }

    def given(self, **answers: object) -> dict:
        return {"status": "answered", "answers": answers}

    def test_a_tune_answer_with_moved_sliders_an_optional_question_left_empty_and_a_text_answer_are_answers(
        self,
    ) -> None:
        self.assertIsNone(
            serve.card_refusal(
                self.TUNE,
                self.given(
                    q1={
                        "selected": [],
                        "labels": [],
                        "values": {"speed": 3},
                        "from": "calm",
                    },
                    q2={"selected": [], "labels": []},
                    q3={"selected": [], "labels": [], "text": "fine"},
                ),
            )
        )

    def test_an_option_or_a_question_the_card_does_not_have_and_an_empty_text_are_refused(
        self,
    ) -> None:
        self.assertIn(
            "an option the card does not have",
            cast("str", serve.card_refusal(CARD, picked("maybe"))),
        )
        self.assertIn(
            "an option the card does not have",
            cast("str", serve.card_refusal(CARD, picked("yes", "no"))),
        )
        self.assertIn(
            "questions the card does not ask",
            cast(
                "str",
                serve.card_refusal(
                    CARD,
                    {"status": "answered", "answers": {"other": {"selected": ["yes"]}}},
                ),
            ),
        )
        self.assertEqual(
            serve.card_refusal(CARD, picked()),
            "Pick an option first: nothing was recorded.",
        )
        self.assertIn(
            "Type an answer first",
            cast(
                "str",
                serve.card_refusal(
                    self.TUNE,
                    self.given(
                        q1={"values": {}},
                        q2={"selected": []},
                        q3={"selected": [], "text": " "},
                    ),
                ),
            ),
        )


class Device(unittest.TestCase):
    def test_criterion_9_a_phone_is_named_by_its_user_agent_or_its_client_hint_and_anything_else_is_a_computer(
        self,
    ) -> None:
        self.assertEqual(serve.device_of(headers(User_Agent=IPHONE)), "phone")
        self.assertEqual(
            serve.device_of(
                headers(User_Agent="Mozilla/5.0 (Linux; Android 15; Pixel 9)")
            ),
            "phone",
        )
        self.assertEqual(
            serve.device_of(headers(User_Agent=MAC, Sec_CH_UA_Mobile="?1")), "phone"
        )
        self.assertEqual(
            serve.device_of(headers(User_Agent=MAC, Sec_CH_UA_Mobile="?0")), "computer"
        )
        self.assertEqual(serve.device_of(headers()), "computer")


class Agterm(unittest.TestCase):
    """`agterm_card_refusal`: one read of agterm's outcome of the card's page, as
    lem-ask's wait reads it."""

    def said(self, stdout: str, returncode: int = 0, stderr: str = "") -> tuple:
        ran = subprocess.CompletedProcess([], returncode, stdout, stderr)
        with (
            mock.patch.object(serve, "agtermctl", return_value="/bin/agtermctl"),
            mock.patch.object(serve.subprocess, "run", return_value=ran) as called,
        ):
            said = serve.agterm_card_refusal(PAGE)
        return said, called.call_args.args[0]

    def test_criterion_4_an_answer_or_a_dismissal_agterm_holds_is_refused_and_an_open_page_is_not(
        self,
    ) -> None:
        def outcome(kind: str) -> str:
            return json.dumps(
                {
                    "ok": True,
                    "result": {"pageOutcome": {"outcome": kind, "value": "{}"}},
                }
            )

        said, argv = self.said(outcome("submitted"))
        self.assertEqual(
            argv,
            [
                "/bin/agtermctl",
                "session",
                "overlay",
                "result",
                "--page",
                PAGE,
                "--json",
            ],
        )
        self.assertIn("An answer was given on the card at the Mac", said)
        self.assertIn("dismissed at the Mac", self.said(outcome("dismissed"))[0])
        self.assertIsNone(
            self.said(json.dumps({"ok": True, "result": {"pageOutcome": {}}}))[0]
        )

    def test_when_agterm_does_not_answer_the_board_says_what_it_said(self) -> None:
        self.assertIn("(no socket)", self.said("", 1, "no socket")[0])
        self.assertIn(
            "(no such page)",
            self.said(json.dumps({"ok": False, "error": "no such page"}))[0],
        )
        with mock.patch.object(serve, "agtermctl", return_value=None):
            self.assertIn(
                "agtermctl is not on this Mac",
                cast("str", serve.agterm_card_refusal(PAGE)),
            )


class Policy(unittest.TestCase):
    """`card_policy` over a page as `lem-ask render` builds it from a template, whose
    spec holds a script of its own."""

    def test_criterion_1_the_page_runs_its_runtime_by_hash_and_no_script_form_or_base_of_its_spec(
        self,
    ) -> None:
        spec = {
            **json.loads(
                (ROOT / "skills" / "lem-ask" / "templates" / "pick.json").read_text()
            ),
            "script": "fetch('/merge', {method: 'POST'})",
            "context": [
                {
                    "html": (
                        "<form action='/x/merge' "
                        "method='post'><button>go</button></form><img src=x "
                        "onerror=alert(1)><script>alert(2)</script>"
                    )
                },
                {"js": "fetch('/x/merge', {method: 'POST'})"},
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "spec.json").write_text(json.dumps(spec))
            subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "src" / "lem" / "__main__.py"),
                    "lem-ask",
                    "render",
                    str(Path(tmp) / "spec.json"),
                    "-o",
                    str(Path(tmp) / "page.html"),
                ],
                check=True,
                capture_output=True,
            )
            policy = serve.card_policy((Path(tmp) / "page.html").read_bytes())
        runtime = (ROOT / "skills" / "lem-ask" / "runtime" / "ask.js").read_text(
            encoding="utf-8"
        )
        digest = base64.b64encode(
            hashlib.sha256(runtime.encode("utf-8")).digest()
        ).decode()
        parts = dict(part.strip().split(" ", 1) for part in policy.split(";"))
        self.assertEqual(parts["script-src"], f"'sha256-{digest}'")
        self.assertEqual(
            {
                key: parts[key]
                for key in (
                    "form-action",
                    "base-uri",
                    "object-src",
                    "frame-src",
                    "frame-ancestors",
                )
            },
            {
                "form-action": "'none'",
                "base-uri": "'none'",
                "object-src": "'none'",
                "frame-src": "'none'",
                "frame-ancestors": "'self'",
            },
        )
        for loose in ("unsafe-eval", "unsafe-inline", "unsafe-hashes"):
            self.assertNotIn(loose, policy)


class NoTyping(unittest.TestCase):
    """Criterion 8: the server holds no call that answers, closes or types into a
    session or its overlay."""

    REFUSED = {"submit", "close", "type", "paste", "restart", "send", "send-keys"}

    def test_criterion_8_no_call_of_the_server_answers_closes_or_types_into_a_session(
        self,
    ) -> None:
        tree = ast.parse(
            (ROOT / "src" / "lem" / "serve.py").read_text(encoding="utf-8")
        )
        texts = [
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        ]
        for text in texts:
            self.assertNotRegex(
                text,
                r"overlay[ .](submit|close)|session[ .](type|paste|close|restart)\b",
                text[:80],
            )
        calls = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.List, ast.Tuple)):
                words = [
                    x.value
                    for x in node.elts
                    if isinstance(x, ast.Constant) and isinstance(x.value, str)
                ]
                if "session" in words or "overlay" in words or "msg" in words:
                    calls.append(words)
        self.assertTrue(calls, "the server's calls of agtermctl were not found")
        for words in calls:
            self.assertFalse(self.REFUSED & set(words), words)
        self.assertIn(["session", "overlay", "result", "--page", "--json"], calls)


if __name__ == "__main__":
    unittest.main()
