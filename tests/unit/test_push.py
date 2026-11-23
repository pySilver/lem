"""lem_push.py's rules, each called in this process: the ES256 signature in the form a JWS carries, the
VAPID token's claims and life, what is news in a list of what waits, which endpoints are taken, and a
device that its push service no longer knows. No case sends a push: the send is a stand-in, and the
switch LEM_PUSH=record is set for the whole file. The routes run in tests/lem-serve.sh.

    python3 -B -m unittest discover -s tests/unit
"""

import importlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.dont_write_bytecode = True
sys.path.insert(
    0, str(Path(__file__).resolve().parents[2] / "skills" / "lem" / "scripts")
)
push = importlib.import_module("lem_push")
bm = importlib.import_module("lem_board_model")

HAS_OPENSSL = any(os.access(place, os.X_OK) for place in push.OPENSSL_PLACES)
NO_OPENSSL = "no openssl at " + ", ".join(push.OPENSSL_PLACES)
FCM = "https://fcm.googleapis.com/fcm/send/abc:def"
APPLE = "https://web.push.apple.com/QGxlbS10ZXN0"


class InHome(unittest.TestCase):
    """Each case runs with a folder of its own as XDG_CONFIG_HOME, with the record switch on."""

    def setUp(self) -> None:
        self.folder = tempfile.TemporaryDirectory()
        patcher = mock.patch.dict(
            os.environ,
            {"XDG_CONFIG_HOME": self.folder.name, push.SWITCH[0]: push.SWITCH[1]},
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.folder.cleanup)


@unittest.skipUnless(HAS_OPENSSL, NO_OPENSSL)
class Signature(InHome):
    def test_a_signature_as_raw_r_and_s_verifies_with_openssl_after_the_way_back(
        self,
    ) -> None:
        path, public = push.machine_key()
        self.assertEqual(oct(path.stat().st_mode & 0o777), "0o600")
        self.assertEqual(len(push.unb64url(public)), 65)
        data = b"header.claims"
        raw = push.sign(path, data)
        self.assertEqual(len(raw), 64)
        work = Path(self.folder.name)
        (work / "sig.der").write_bytes(push.raw_to_der(raw))
        (work / "data").write_bytes(data)
        subprocess.run(
            [
                push.openssl(),
                "ec",
                "-in",
                str(path),
                "-pubout",
                "-out",
                str(work / "pub.pem"),
            ],
            capture_output=True,
            check=True,
        )
        checked = subprocess.run(
            [
                push.openssl(),
                "dgst",
                "-sha256",
                "-verify",
                str(work / "pub.pem"),
                "-signature",
                str(work / "sig.der"),
                str(work / "data"),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertIn("Verified OK", checked.stdout)

    def test_the_token_names_the_push_services_origin_and_ends_within_a_day(
        self,
    ) -> None:
        path, _ = push.machine_key()
        jwt = push.token(push.audience(FCM), 1_000_000, path)
        head = json.loads(push.unb64url(jwt.split(".")[0]))
        claims = push.claims_of(jwt)
        self.assertEqual(head, {"typ": "JWT", "alg": "ES256"})
        self.assertEqual(claims["aud"], "https://fcm.googleapis.com")
        self.assertTrue(claims["sub"].startswith("mailto:"))
        self.assertLessEqual(claims["exp"] - 1_000_000, 24 * 3600)
        self.assertGreater(claims["exp"] - 1_000_000, push.TOKEN_REUSE)


class Der(unittest.TestCase):
    def test_short_and_padded_numbers_become_32_bytes_each(self) -> None:
        r, s = b"\x00" + b"\x80" + b"\x01" * 31, b"\x05"
        der = (
            b"\x30"
            + bytes([4 + len(r) + len(s)])
            + b"\x02"
            + bytes([len(r)])
            + r
            + b"\x02\x01"
            + s
        )
        raw = push.der_to_raw(der)
        self.assertEqual(raw, b"\x80" + b"\x01" * 31 + b"\x00" * 31 + b"\x05")
        self.assertEqual(push.der_to_raw(push.raw_to_der(raw)), raw)
        with self.assertRaises(push.PushError):
            push.der_to_raw(der + b"\x00")


class News(unittest.TestCase):
    def test_the_first_look_sends_nothing_and_a_gained_row_is_news_once(self) -> None:
        news, memory = push.gained(None, ["merge:a"], 0)
        self.assertEqual(news, [])
        news, memory = push.gained(memory, ["merge:a", "breaker:b:1"], 10)
        self.assertEqual(news, ["breaker:b:1"])
        news, memory = push.gained(memory, ["merge:a", "breaker:b:1"], 20)
        self.assertEqual(news, [])

    def test_a_row_that_leaves_and_comes_back_soon_is_not_news_and_later_it_is(
        self,
    ) -> None:
        _, memory = push.gained(None, ["held:a"], 0)
        _, memory = push.gained(memory, [], 10)
        news, memory = push.gained(memory, ["held:a"], 10 + push.FLAP_SECONDS - 1)
        self.assertEqual(news, [])
        _, memory = push.gained(memory, [], 400)
        news, _ = push.gained(memory, ["held:a"], 400 + push.FLAP_SECONDS + 1)
        self.assertEqual(news, ["held:a"])


class Endpoints(unittest.TestCase):
    def test_only_https_at_a_push_service_a_browser_uses(self) -> None:
        for taken in (
            FCM,
            APPLE,
            "https://updates.push.services.mozilla.com/wpush/v2/x",
            "https://wns2-par02p.notify.windows.com/w/?token=x",
            "https://fcm.googleapis.com:443/fcm/send/x",
        ):
            self.assertIsNone(push.refusal(taken), taken)
        for refused in (
            "http://fcm.googleapis.com/fcm/send/x",
            "https://fcm.googleapis.com:8443/x",
            "https://127.0.0.1/x",
            "https://[::1]/x",
            "https://fcm.googleapis.com.evil.example/x",
            "https://push.apple.com/x",
            "https://evil.example/x",
            "https://u:p@fcm.googleapis.com/x",
            None,
            "",
            "https://fcm.googleapis.com/" + "x" * 2100,
        ):
            self.assertIsNotNone(push.refusal(refused), refused)


@unittest.skipUnless(HAS_OPENSSL, NO_OPENSSL)
class Sending(InHome):
    def test_a_device_its_service_no_longer_knows_goes_and_the_token_is_used_again(
        self,
    ) -> None:
        for endpoint in (FCM, APPLE, FCM + "-gone"):
            push.subscribe(
                {"endpoint": endpoint, "keys": {"p256dh": "k", "auth": "a"}},
                "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0) AppleWebKit/605 Safari/604",
            )
        sent = []

        def stand_in(endpoint, headers):
            sent.append((endpoint, headers))
            return (410, "gone") if endpoint.endswith("-gone") else (201, "")

        pusher = push.Pusher(send=stand_in)
        results = pusher.send(
            push.read_state()["devices"], {"title": "T", "body": "B", "url": "/x"}
        )
        pusher.send(push.read_state()["devices"])
        self.assertEqual([r["status"] for r in results], [201, 201, 410])
        self.assertEqual(
            [d["endpoint"] for d in push.read_state()["devices"]], [FCM, APPLE]
        )
        self.assertEqual(push.read_state()["devices"][0]["device"], "iPhone · Safari")
        self.assertEqual(push.latest()["title"], "T")
        headers = sent[0][1]
        self.assertEqual(
            (headers["TTL"], headers["Urgency"], headers["Topic"]),
            (str(push.TTL_SECONDS), "high", push.TOPIC),
        )
        self.assertRegex(
            headers["Authorization"], r"^vapid t=[\w-]+\.[\w-]+\.[\w-]+, k=[\w-]+$"
        )
        self.assertEqual(sent[0][1]["Authorization"], sent[3][1]["Authorization"])

    def test_a_row_gained_while_the_owner_is_away_is_sent_and_a_demo_sends_nothing(
        self,
    ) -> None:
        push.subscribe({"endpoint": FCM}, "")
        sent = []
        pusher = push.Pusher(
            send=lambda endpoint, headers: sent.append(endpoint) or (201, "")
        )
        rows = {"now": []}
        task = SimpleNamespace(title="Footer terms typo", slug="footer-terms-typo")
        model = SimpleNamespace(meta={}, away=None)
        demo = SimpleNamespace(meta={"demo": True}, away=None)
        clock = {"now": 1000.0}
        watcher = push.Watcher(
            lambda: [
                ("shop", "/repo/shop", lambda: model),
                ("demo", "/repo/demo", lambda: demo),
            ],
            "mac",
            pusher,
            log=lambda line: None,
            now=lambda: clock["now"],
        )
        with (
            mock.patch.object(bm, "waits_of", lambda m: rows["now"]),
            mock.patch.object(
                bm,
                "wait_say",
                lambda w: {"verb": "Merge the pull request #41", "to": "overview"},
            ),
        ):
            watcher.look()
            rows["now"] = [{"key": "merge:footer-terms-typo", "t": task}]
            model.away = {"since": 0, "words": ""}
            clock["now"] += 10
            self.assertEqual(len(watcher.look()), 1)
            rows["now"] = [
                {"key": "merge:footer-terms-typo", "t": task},
                {"key": "breaker:footer-terms-typo:1", "t": task},
            ]
            model.away = None
            clock["now"] += 10
            done = watcher.look()
        self.assertEqual(len(done), 1)
        self.assertEqual(sent, [FCM, FCM])
        self.assertEqual(push.latest()["url"], "/mac/shop/tasks/footer-terms-typo")
        self.assertNotIn("/repo/demo", push.read_state()["seen"])

    def test_no_push_goes_for_a_held_task_while_its_session_works_and_one_when_its_turn_ended(
        self,
    ) -> None:
        # waits-for-you-only-when-it-waits, criteria 1 and 2: the push follows the rows of Waits for you
        push.subscribe({"endpoint": FCM}, "")
        sent = []
        pusher = push.Pusher(
            send=lambda endpoint, headers: sent.append(endpoint) or (201, "")
        )
        building = [
            {
                "ts": "2026-11-23T11:00:00Z",
                "event": "task.state",
                "task": "gift-note",
                "status": "building",
                "text": "task 1 of 2",
                "lines": [],
            }
        ]
        stopped = [
            *building,
            {
                "ts": "2026-11-23T11:20:00Z",
                "event": "decision.breaker",
                "task": "gift-note",
                "id": 1,
                "kind": "breaker",
                "cause": "criteria",
                "what": "The gift note has no place",
                "document": "breaker.md",
            },
            {
                "ts": "2026-11-23T11:20:00Z",
                "event": "task.state",
                "task": "gift-note",
                "status": "held",
                "text": "breaker 1 waits for the owner",
                "lines": [],
            },
        ]

        def model(events, turn):
            m = bm.derive(events, [], bm.at("2026-11-23T11:30:00Z"))
            bm.put_sessions(
                m,
                {
                    "gift-note": {
                        "live": True,
                        "agent": True,
                        "unanswered": False,
                        "session": "S1",
                        "worktree": False,
                        "turn": turn,
                    }
                },
            )
            return m

        now = {"model": model(building, "runs")}
        clock = {"now": 1000.0}
        watcher = push.Watcher(
            lambda: [("shop", "/repo/shop", lambda: now["model"])],
            "mac",
            pusher,
            log=lambda line: None,
            now=lambda: clock["now"],
        )
        self.assertEqual(watcher.look(), [])
        for turn, pushes in (("runs", 0), ("ended", 1)):
            now["model"] = model(stopped, turn)
            clock["now"] += 10
            watcher.look()
            self.assertEqual(len(sent), pushes, turn)


if __name__ == "__main__":
    unittest.main()
