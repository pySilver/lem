"""serve.py's rules, each called in this process: who the tailnet door lets in, who may
ask the main listener for an act, the note of a merge that runs, whether a page's stream
gets a refresh as it opens, and its ping, the machine's names in an address, which duty
the server owes the tasks, when it runs `lem project prune`, and the number of
`state.keep_days` a page says. The routes, the stream and the start on demand run in
tests/lem-serve.sh, with a server.

    python3 -B -m unittest discover -s tests/unit
"""

import email.message
import json
import subprocess
import sys
import unittest
from datetime import UTC, datetime
from pathlib import Path
from typing import IO, TYPE_CHECKING, cast
from unittest import mock

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from lem import board_model as bm
from lem import paths, serve

if TYPE_CHECKING:
    from collections.abc import Callable

OWNER = "owner@example.com"
SERVED = "mac-mini.tail1234.ts.net"
PORT = 4537


def headers(*pairs: tuple[str, str], **given: str) -> email.message.Message:
    """Request headers as the server's handler has them, each name once for each time it
    came; `_` in a keyword's name is `-`."""
    message = email.message.Message()
    for name, value in [
        *pairs,
        *((key.replace("_", "-"), value) for key, value in given.items()),
    ]:
        message[name] = value
    return message


def door(method: str = "GET", **given: str) -> str | None:
    return serve.door_refusal(headers(**given), method, OWNER, SERVED, PORT)


class Door(unittest.TestCase):
    def test_the_owners_login_for_the_macs_own_name_is_let_in(self) -> None:
        self.assertIsNone(door(Host=f"{SERVED}:{PORT}", Tailscale_User_Login=OWNER))
        self.assertIsNone(door(Host=SERVED.upper(), Tailscale_User_Login=OWNER.upper()))

    def test_another_login_and_no_login_are_refused(self) -> None:
        self.assertEqual(
            door(Host=SERVED, Tailscale_User_Login="guest@example.com"),
            serve.NOT_THE_OWNER,
        )
        self.assertIn("carries none", door(Host=SERVED) or "")
        self.assertEqual(
            serve.door_refusal(
                headers(
                    ("Host", SERVED),
                    ("Tailscale-User-Login", OWNER),
                    ("Tailscale-User-Login", OWNER),
                ),
                "GET",
                OWNER,
                SERVED,
                PORT,
            ),
            serve.NOT_THE_OWNER,
        )

    def test_a_request_through_funnel_is_refused_whatever_its_login(self) -> None:
        self.assertIn(
            "Funnel",
            door(Host=SERVED, Tailscale_User_Login=OWNER, Tailscale_Funnel_Request="?1")
            or "",
        )

    def test_another_host_name_is_refused(self) -> None:
        self.assertIn(
            "not the board's name",
            door(Host="evil.example.com", Tailscale_User_Login=OWNER) or "",
        )
        self.assertIn(
            "not the board's name",
            door(Host=f"{SERVED}:443", Tailscale_User_Login=OWNER) or "",
        )

    def test_a_post_from_another_site_is_refused_and_one_from_the_board_is_let_in(
        self,
    ) -> None:
        own = f"https://{SERVED}:{PORT}"
        self.assertIsNone(
            door(
                "POST",
                Host=SERVED,
                Tailscale_User_Login=OWNER,
                Origin=own,
                Sec_Fetch_Site="same-origin",
            )
        )
        self.assertIn(
            "another site",
            door(
                "POST",
                Host=SERVED,
                Tailscale_User_Login=OWNER,
                Origin=own,
                Sec_Fetch_Site="cross-site",
            )
            or "",
        )
        self.assertIn(
            "another origin",
            door(
                "POST",
                Host=SERVED,
                Tailscale_User_Login=OWNER,
                Origin="https://evil.example.com",
            )
            or "",
        )


class Actions(unittest.TestCase):
    """The main listener's acts (of agterm, of the board on a task): only a page of the
    board on this Mac asks them."""

    def refusal(self, client: str = "127.0.0.1", **given: str) -> str | None:
        return serve.action_refusal(client, headers(**given), 4536)

    def test_the_boards_own_page_on_this_mac_is_let_in(self) -> None:
        self.assertIsNone(
            self.refusal(
                Host="127.0.0.1:4536",
                Origin="http://127.0.0.1:4536",
                Sec_Fetch_Site="same-origin",
            )
        )
        self.assertIsNone(
            self.refusal("::1", Host="localhost:4536", Origin="http://localhost:4536")
        )

    def test_another_machine_another_site_and_a_name_that_points_here_are_refused(
        self,
    ) -> None:
        self.assertIn(
            "on this Mac",
            self.refusal(
                "100.64.0.2", Host="127.0.0.1:4536", Origin="http://127.0.0.1:4536"
            )
            or "",
        )
        self.assertIn(
            "another site",
            self.refusal(
                Host="127.0.0.1:4536",
                Origin="http://127.0.0.1:4536",
                Sec_Fetch_Site="cross-site",
            )
            or "",
        )
        self.assertIn(
            "another origin",
            self.refusal(Host="127.0.0.1:4536", Origin="http://evil.example.com") or "",
        )
        self.assertIn("or none", self.refusal(Host="127.0.0.1:4536") or "")
        # a form of a page whose policy sends no referrer posts `Origin: null`: still
        # refused, so the board's pages send `Referrer-Policy: same-origin`
        # (`Handler.send`)
        self.assertIn(
            "or none",
            self.refusal(
                Host="127.0.0.1:4536", Origin="null", Sec_Fetch_Site="same-origin"
            )
            or "",
        )
        # a name of another site that resolves to 127.0.0.1 carries that name in Host
        self.assertIn(
            "not the board's own",
            self.refusal(
                Host="evil.example.com:4536", Origin="http://evil.example.com:4536"
            )
            or "",
        )


class StartBehind(unittest.TestCase):
    """The board starts no task for a project whose sessions load a Lem older than the
    board's release before (lem_release.BEFORE): its new task's mark would be that
    release, and every act of the board on it would stop at once. One release behind
    starts, with that release as its mark."""

    def behind(self, listed: dict) -> str | None:
        workspace = serve.Workspace.__new__(serve.Workspace)
        workspace.path = "/lem-unit/shop"
        with (
            mock.patch.object(serve.lem_release, "running", lambda: "0.3.0"),
            mock.patch.object(serve.lem_release, "BEFORE", "0.2.0"),
            mock.patch.object(serve.lem_release, "installs", lambda: listed),
        ):
            return serve.release_behind(workspace)

    def test_a_project_two_releases_behind_the_board_is_refused_with_the_update(
        self,
    ) -> None:
        said = self.behind(
            {
                "plugins": {
                    "lem@lem": [
                        {
                            "scope": "project",
                            "projectPath": "/lem-unit/shop",
                            "version": "0.1.6",
                        }
                    ]
                }
            }
        )
        self.assertIn(
            (
                "The Lem this project's sessions load is 0.1.6, "
                "and this board runs Lem 0.3.0"
            ),
            said or "",
        )
        self.assertIn("/plugin marketplace update lem", said or "")

    def test_a_project_one_release_behind_or_with_none_of_its_own_starts(self) -> None:
        self.assertIsNone(
            self.behind(
                {
                    "plugins": {
                        "lem@lem": [
                            {
                                "scope": "project",
                                "projectPath": "/lem-unit/shop",
                                "version": "0.2.0",
                            }
                        ]
                    }
                }
            )
        )
        self.assertIsNone(
            self.behind(
                {"plugins": {"lem@lem": [{"scope": "user", "version": "0.3.0"}]}}
            )
        )


class Reads(unittest.TestCase):
    """The main listener reads a request only for a `Host` of its own: a name of another
    site that points at this machine (DNS rebinding) reads nothing."""

    def test_its_own_names_are_read_and_another_is_refused(self) -> None:
        for host in (
            "127.0.0.1:4536",
            "localhost:4536",
            "[::1]:4536",
            "127.0.0.1",
            "LOCALHOST:4536",
        ):
            self.assertIsNone(serve.host_refusal(headers(Host=host), 4536), host)
        for given in (
            headers(Host="evil.example.com:4536"),
            headers(),
            headers(("Host", "127.0.0.1:4536"), ("Host", "evil.example.com")),
        ):
            self.assertIn(
                "not the board's own", cast("str", serve.host_refusal(given, 4536))
            )
        self.assertIsNone(
            serve.host_refusal(headers(Host="10.0.0.5:4536"), 4536, "10.0.0.5")
        )
        self.assertIsNotNone(serve.host_refusal(headers(Host="10.0.0.5:4536"), 4536))


class Notes(unittest.TestCase):
    def test_a_second_press_of_a_merge_that_runs_gets_the_first_ones_note(self) -> None:
        notes = serve.Notes()
        first, new = notes.start_merge(
            ("shop", "gift-note"), task="gift-note", state="running", said="merging"
        )
        again, second = notes.start_merge(
            ("shop", "gift-note"), task="gift-note", state="running", said="merging"
        )
        self.assertEqual(
            (again, new, second, notes.running("shop")),
            (first, True, False, {"gift-note"}),
        )
        notes.change(first, state="done", said="merged")
        self.assertEqual(
            (cast("dict", notes.get(first))["state"], notes.get("no-such-token")),
            ("done", None),
        )


class StreamOpen(unittest.TestCase):
    """Whether a page's stream gets a refresh the moment it opens
    (`opens_with_refresh`)."""

    def test_a_first_open_gets_one_only_when_the_log_is_no_longer_at_its_render(
        self,
    ) -> None:
        self.assertFalse(serve.opens_with_refresh("8812-142", None, None, "8812-142"))
        self.assertTrue(serve.opens_with_refresh("8812-141", None, None, "8812-142"))
        # the same count on a log that `lem project prune` replaced, and a shorter one,
        # are behind too
        self.assertTrue(serve.opens_with_refresh("8812-142", None, None, "9301-142"))
        self.assertTrue(serve.opens_with_refresh("8812-143", None, None, "9301-142"))

    def test_an_open_again_gets_one_whatever_the_log(self) -> None:
        self.assertTrue(serve.opens_with_refresh(None, "8812-142", None, "8812-142"))
        self.assertTrue(serve.opens_with_refresh(None, "8812-150", None, "8812-142"))

    def test_the_browsers_own_reconnect_gets_one_also_on_a_first_opens_address(
        self,
    ) -> None:
        self.assertTrue(
            serve.opens_with_refresh("8812-142", None, "8812-142", "8812-142")
        )

    def test_an_open_that_names_no_id_gets_none(self) -> None:
        self.assertFalse(serve.opens_with_refresh(None, None, None, "8812-142"))
        self.assertFalse(serve.opens_with_refresh("", None, "", "8812-142"))

    def test_the_ping_is_an_event_of_its_own_with_the_logs_id(self) -> None:
        self.assertEqual(
            serve.ping("8812-142"), b"id: 8812-142\nevent: ping\ndata: 8812-142\n\n"
        )


class Names(unittest.TestCase):
    def test_the_tailnet_name_is_the_address_and_the_host_name_its_alias(self) -> None:
        # A label made from the host's own short name, so that no host's short name is
        # the label.
        tailnet_name = f"Office-{serve.SHORT_NAME}.tail1234.ts.net"
        self.assertEqual(
            serve.names_of(tailnet_name),
            (f"office-{serve.SHORT_NAME}", (serve.SHORT_NAME,)),
        )

    def test_with_no_tailnet_the_short_host_name_alone(self) -> None:
        self.assertEqual(serve.names_of(None), (serve.SHORT_NAME, ()))
        self.assertEqual(
            serve.names_of(f"{serve.SHORT_NAME}.tail1234.ts.net"),
            (serve.SHORT_NAME, ()),
        )

    def test_a_name_is_a_word_of_an_address(self) -> None:
        self.assertEqual(serve.host_word("Mac mini (Office)"), "mac-mini-office")


class Duties(unittest.TestCase):
    """What the server owes the tasks, read from the files and the forge's last
    look alone."""

    PR = "pull request https://github.com/acme/shop/pull/41"

    @staticmethod
    def ev(
        minute: float, event: str, task: str = "gift-note", **fields: object
    ) -> dict:
        return {
            "ts": f"2026-11-20T09:{minute:02d}:00Z",
            "event": event,
            "task": task,
            **fields,
        }

    def state(
        self,
        minute: float,
        status: str,
        text: str,
        *lines: str,
        task: str = "gift-note",
    ) -> dict:
        return self.ev(
            minute, "task.state", task, status=status, text=text, lines=list(lines)
        )

    def model(
        self, *events: dict, sessions: dict | None = None, demo: bool = False
    ) -> bm.Model:
        m = bm.derive(
            list(events), [], 1_800_000_000_000, meta={"demo": True} if demo else {}
        )
        m.sessions = sessions
        return m

    def test_a_merge_wakes_the_tasks_session_once_while_its_worktree_stays(
        self,
    ) -> None:
        merged = (
            self.state(0, "open", self.PR),
            self.state(
                5,
                "landed",
                "main: pull request https://github.com/acme/shop/pull/41 is merged",
            ),
        )
        self.assertEqual(
            serve.duties(self.model(*merged), {}, {"gift-note"}),
            [("wake", "gift-note", "merged")],
        )
        self.assertEqual(serve.duties(self.model(*merged), {}, set()), [])
        woken = (*merged, self.ev(6, "session.wake", session="S1", why="merged"))
        self.assertEqual(serve.duties(self.model(*woken), {}, {"gift-note"}), [])
        closed = (
            self.state(0, "open", self.PR),
            self.state(
                5,
                "dropped",
                "the pull request was closed on the forge",
                "pull request ... is closed",
            ),
        )
        self.assertEqual(
            serve.duties(self.model(*closed), {}, {"gift-note"}),
            [("wake", "gift-note", "merged")],
        )
        by_word = (
            self.state(0, "building", "task 1 of 2"),
            self.state(5, "dropped", "the owner dropped it"),
        )
        self.assertEqual(serve.duties(self.model(*by_word), {}, {"gift-note"}), [])

    def test_a_conflict_wakes_the_session_once_for_each_head(self) -> None:
        events = (
            self.ev(0, "proposed", green=True, not_green=[], tip="abc123456"),
            self.state(1, "open", self.PR),
        )
        seen = {"gift-note": {"mergeable": "CONFLICTING", "head": "abc123456789"}}
        self.assertEqual(
            serve.duties(self.model(*events), seen, set()),
            [("wake", "gift-note", "conflict")],
        )
        self.assertEqual(
            serve.duties(
                self.model(*events),
                {"gift-note": {"mergeable": "MERGEABLE", "head": "abc123456789"}},
                set(),
            ),
            [],
        )
        self.assertEqual(
            serve.duties(
                self.model(*events),
                {"gift-note": {"mergeable": "CONFLICTING", "head": "fff000"}},
                set(),
            ),
            [],
        )
        woken = (*events, self.ev(2, "session.wake", session="S1", why="conflict"))
        self.assertEqual(serve.duties(self.model(*woken), seen, set()), [])
        again = (
            *woken,
            self.ev(3, "proposed", green=True, not_green=[], tip="def456789"),
            self.state(4, "open", self.PR),
        )
        self.assertEqual(
            serve.duties(
                self.model(*again),
                {"gift-note": {"mergeable": "CONFLICTING", "head": "def456789aaa"}},
                set(),
            ),
            [("wake", "gift-note", "conflict")],
        )

    def test_a_queued_task_gets_its_session_when_its_task_ended(self) -> None:
        landed = (
            self.state(0, "landed", "main: pull request ... is merged", task="coupon"),
        )
        queued = (self.state(1, "queued", "it starts after coupon", "after: coupon"),)
        self.assertEqual(
            serve.duties(self.model(*landed, *queued, sessions={}), {}, set()),
            [("open", "gift-note", "queue")],
        )
        self.assertEqual(
            serve.duties(self.model(*landed, *queued, sessions=None), {}, set()), []
        )
        opened = (
            *landed,
            *queued,
            self.ev(2, "session.open", session="S2", why="queue"),
        )
        self.assertEqual(serve.duties(self.model(*opened, sessions={}), {}, set()), [])
        waiting = (self.state(0, "open", self.PR, task="coupon"), *queued)
        self.assertEqual(serve.duties(self.model(*waiting, sessions={}), {}, set()), [])

    def test_a_queued_task_whose_session_lives_is_woken_once_when_its_task_ended(
        self,
    ) -> None:
        # the session the ask was typed in, opened before the queue, which the owner
        # keeps selected
        typed = (
            self.ev(0, "session.open", session="S1", why="new"),
            self.state(1, "landed", "main: pull request ... is merged", task="coupon"),
        )
        queued = (
            self.state(
                2,
                "queued",
                'the owner\'s order: "After coupon: unit cases"',
                "after: coupon",
                "then: the interview",
            ),
        )
        live = {"gift-note": {"live": True, "agent": True}}
        self.assertEqual(
            serve.duties(self.model(*typed, *queued, sessions=live), {}, set()),
            [("wake", "gift-note", "queue")],
        )
        woken = (*typed, *queued, self.ev(3, "session.wake", session="S1", why="queue"))
        self.assertEqual(serve.duties(self.model(*woken, sessions=live), {}, set()), [])
        reopened = (
            *typed,
            *queued,
            self.ev(3, "session.open", session="S2", why="queue"),
        )
        self.assertEqual(
            serve.duties(self.model(*reopened, sessions=live), {}, set()), []
        )
        # a wake from before the queue does not count for it
        before = (
            self.ev(0, "session.open", session="S1", why="new"),
            self.ev(1, "session.wake", session="S1", why="owner"),
            self.state(1, "landed", "main: pull request ... is merged", task="coupon"),
            *queued,
        )
        self.assertEqual(
            serve.duties(self.model(*before, sessions=live), {}, set()),
            [("wake", "gift-note", "queue")],
        )
        # while its task has not ended, nothing
        waiting = (
            self.ev(0, "session.open", session="S1", why="new"),
            self.state(1, "open", self.PR, task="coupon"),
            *queued,
        )
        self.assertEqual(
            serve.duties(self.model(*waiting, sessions=live), {}, set()), []
        )

    def test_a_task_queued_again_behind_a_second_task_gets_its_turn_when_that_one_ends(
        self,
    ) -> None:
        # its first wait ended, its session read the need again and queued it
        # behind card-foot
        first = (
            self.state(0, "landed", "main: pull request ... is merged", task="coupon"),
            self.state(1, "open", self.PR, task="card-foot"),
            self.state(
                2,
                "queued",
                'the owner\'s order: "After coupon: x"',
                "after: coupon",
                "then: the interview",
            ),
        )
        again = (
            self.state(
                4,
                "queued",
                "needs the card foot",
                "after: card-foot",
                "then: the interview",
            ),
        )
        landed = (
            self.state(
                6, "landed", "main: pull request ... is merged", task="card-foot"
            ),
        )
        opened = (
            *first,
            self.ev(3, "session.open", session="S2", why="queue"),
            *again,
            self.ev(5, "session.close", session="S2"),
        )
        self.assertEqual(serve.duties(self.model(*opened, sessions={}), {}, set()), [])
        self.assertEqual(
            serve.duties(self.model(*opened, *landed, sessions={}), {}, set()),
            [("open", "gift-note", "queue")],
        )
        # the same, with the session woken for the first wait and still live
        live = {"gift-note": {"live": True, "agent": True}}
        woken = (
            *first,
            self.ev(3, "session.wake", session="S1", why="queue"),
            *again,
            *landed,
        )
        self.assertEqual(
            serve.duties(self.model(*woken, sessions=live), {}, set()),
            [("wake", "gift-note", "queue")],
        )
        # a queued block written again behind the same task keeps the one turn it had
        same = (
            *first,
            self.ev(3, "session.wake", session="S1", why="queue"),
            self.state(
                4,
                "queued",
                'the owner\'s order: "After coupon: x"',
                "after: coupon",
                "then: the interview",
                "the agent sees no need",
            ),
        )
        self.assertEqual(serve.duties(self.model(*same, sessions=live), {}, set()), [])

    def test_the_merge_agents_merge_of_the_proposed_tip_is_the_servers(self) -> None:
        proposed = (
            self.ev(0, "proposed", green=True, not_green=[], tip="abc123456"),
            self.state(1, "open", self.PR),
        )
        merge = (
            *proposed,
            self.ev(
                2,
                "merge.review",
                verdict="merge",
                calls=False,
                by="claude/opus:high",
                tip="abc123456",
            ),
        )
        self.assertEqual(
            serve.duties(self.model(*merge), {}, set()),
            [("merge", "gift-note", "merger")],
        )
        # one that runs in this process is not started twice
        self.assertEqual(serve.duties(self.model(*merge), {}, set(), {"gift-note"}), [])
        call = (
            *proposed,
            self.ev(
                2,
                "merge.review",
                verdict="call",
                calls=True,
                by="claude/opus:high",
                tip="abc123456",
            ),
        )
        self.assertEqual(serve.duties(self.model(*call), {}, set()), [])
        overruled = (
            *proposed,
            self.ev(
                2,
                "merge.review",
                verdict="merge",
                calls=True,
                by="claude/opus:high",
                tip="abc123456",
            ),
        )
        self.assertEqual(serve.duties(self.model(*overruled), {}, set()), [])
        other_tip = (
            *proposed,
            self.ev(
                2,
                "merge.review",
                verdict="merge",
                calls=False,
                by="claude/opus:high",
                tip="fff000111",
            ),
        )
        self.assertEqual(serve.duties(self.model(*other_tip), {}, set()), [])
        # a refused try is not tried again on that tip, and the task's session is woken
        # once for it
        refused = (
            *merge,
            self.ev(
                3,
                "merge.refused",
                by="merger",
                via="server",
                said="main moved after the checks ran",
                tip="abc123456",
            ),
        )
        self.assertEqual(
            serve.duties(self.model(*refused), {}, set()),
            [("wake", "gift-note", "refused")],
        )
        self.assertEqual(
            serve.duties(
                self.model(
                    *refused, self.ev(4, "session.wake", session="S1", why="refused")
                ),
                {},
                set(),
            ),
            [],
        )
        # a new proposal and its new review make a new try
        again = (
            *refused,
            self.ev(5, "proposed", green=True, not_green=[], tip="def456789"),
            self.state(6, "open", self.PR),
            self.ev(
                7,
                "merge.review",
                verdict="merge",
                calls=False,
                by="claude/opus:high",
                tip="def456789",
            ),
        )
        self.assertEqual(
            serve.duties(self.model(*again), {}, set()),
            [("merge", "gift-note", "merger")],
        )
        merged = (
            *merge,
            self.state(
                3,
                "landed",
                "main: pull request https://github.com/acme/shop/pull/41 is merged",
            ),
        )
        self.assertEqual(serve.duties(self.model(*merged), {}, set()), [])
        self.assertEqual(serve.duties(self.model(*merge, demo=True), {}, set()), [])

    def test_after_a_moved_base_the_session_lands_it_again_and_the_server_merges_the_new_tip(
        self,
    ) -> None:
        proposed = (
            self.ev(0, "proposed", green=True, not_green=[], tip="abc123456"),
            self.state(1, "open", self.PR),
        )
        # the owner's merge from the board met a moved base: Lem kept it, and the task's
        # session is woken once
        base = (
            *proposed,
            self.ev(
                2,
                "merge.refused",
                by="owner",
                via="server",
                kind="base",
                said="origin/main moved after the checks ran",
                tip="abc123456",
                **{"from": "lem"},
            ),
        )
        self.assertEqual(
            serve.duties(self.model(*base), {}, set()),
            [("wake", "gift-note", "refused")],
        )
        self.assertEqual(
            serve.duties(
                self.model(
                    *base, self.ev(3, "session.wake", session="S1", why="refused")
                ),
                {},
                set(),
            ),
            [],
        )
        # GitHub's refusal of his merge is his to read, and wakes nobody
        github = (
            *proposed,
            self.ev(
                2,
                "merge.refused",
                by="owner",
                via="server",
                said="Required status check is expected",
                tip="abc123456",
                **{"from": "github"},
            ),
        )
        self.assertEqual(serve.duties(self.model(*github), {}, set()), [])
        # the new landing's proposal carried the merge agent's review, and his merge
        # stands for its tip
        again = (
            *base,
            self.ev(4, "proposed", green=True, not_green=[], tip="def456789"),
            self.state(5, "open", self.PR),
        )
        carried = self.ev(
            6,
            "merge.review",
            verdict="merge",
            calls=False,
            by="claude/opus:high",
            tip="def456789",
            carried="abc123456",
        )
        self.assertEqual(
            serve.duties(self.model(*again, carried), {}, set()),
            [("merge", "gift-note", "merger")],
        )
        stands = self.ev(
            7, "merge.stands", by="owner", tip="def456789", **{"from": "abc123456"}
        )
        self.assertEqual(
            serve.duties(self.model(*again, carried, stands), {}, set()),
            [("merge", "gift-note", "owner")],
        )
        self.assertEqual(
            serve.duties(self.model(*again, stands), {}, set(), {"gift-note"}), []
        )
        conflicting = {
            "gift-note": {"mergeable": "CONFLICTING", "head": "def456789aaa"}
        }
        self.assertEqual(
            serve.duties(
                self.model(
                    *again,
                    stands,
                    self.ev(8, "session.wake", session="S1", why="conflict"),
                ),
                conflicting,
                set(),
            ),
            [],
        )
        self.assertEqual(
            serve.merge_args(
                {"history": "squash", "title": "fix: x"},
                "gift-note",
                "owner",
                "def456789" + "0" * 31,
                standing=True,
            ),
            [
                "merge",
                "gift-note",
                "--by",
                "owner",
                "--via",
                "server",
                "--tip",
                "def456789" + "0" * 31,
                "--standing",
                "--message",
                "fix: x",
            ],
        )

    def test_a_press_after_a_moved_base_is_refused_as_lem_lands_it_again(self) -> None:
        # the page offers no Merge while Lem lands it again; a press sent anyway is
        # refused for that, not for a conflict
        class Space:
            name = "shop"

            def __init__(self, m: bm.Model) -> None:
                self.m = m

            def model(self) -> bm.Model:
                return self.m

            def landing_of(self, slug: str) -> dict:
                # no proposed tip: a press that got past the acts is refused at the tip,
                # and nothing merges
                return {}

        # the merge agent's read of the moved base asked for another round, and the
        # refusal it keeps waits for the new landing
        base = (
            self.ev(0, "proposed", green=True, not_green=[], tip="abc123456"),
            self.state(1, "open", self.PR),
            self.ev(
                2,
                "merge.review",
                verdict="merge",
                calls=False,
                by="claude",
                tip="abc123456",
                base="m2m2m2m2m",
                base_call="another round",
                base_why=(
                    "B changed skills/lem/scripts/land.py, which the change edits too"
                ),
            ),
            self.ev(
                2,
                "merge.refused",
                by="owner",
                via="server",
                kind="base",
                said="the merge agent asks for another round of the checks",
                tip="abc123456",
                **{"from": "lem"},
            ),
        )
        note = cast(
            "dict",
            serve.NOTES.get(
                serve.act_merge(
                    cast("serve.Workspace", Space(self.model(*base))),
                    "gift-note",
                    {"confirm": "yes", "tip": "abc123456"},
                    "board",
                )
            ),
        )
        self.assertEqual(note["state"], "refused")
        self.assertIn("Lem lands it again", note["said"])
        self.assertNotIn("conflicting", note["said"])

    def test_his_merge_that_a_moved_base_refused_stands_and_its_note_says_so(
        self,
    ) -> None:
        # guard-sees-unreadable-sessions, 2026-11-23 10:38: his merge of #60 met a moved
        # base; land.py kept it (`owner_tap`), and the server ran it after the merge
        # agent's safe read at 10:41. Meanwhile his note said "Not done." over land.py's
        # line: his merge stood, and nothing of it was refused for good
        tip = "abc123456" + "0" * 31
        said = (
            "land.py: origin/main moved after the checks ran, by files "
            "(docs/rulings/rulings.md); the read of ea54c2a2c said safe, and it covers "
            "no later base. A fresh merge agent reads what moved: "
            "`lem land merge-review gift-note` writes its brief, with the commits and "
            "the files that moved since the checks, and the answer names its base "
            "(`--base`); the owner's merge stands, and goes through after a read that "
            "says `Base: safe.`; on `Base: another round.` the task lands again"
        )
        landing: dict = {
            "proposed": tip,
            "pr": {"number": 41, "url": "https://github.com/acme/shop/pull/41"},
            "base": "main",
        }
        # the events of the task, which the server's model reads again after
        # land.py exits
        events = [
            self.ev(0, "proposed", green=True, not_green=[], tip=tip[:9]),
            self.state(1, "open", self.PR),
            self.ev(
                2,
                "merge.review",
                verdict="call",
                calls=True,
                why="a careful request is merged by the owner",
                by="claude",
                tip=tip[:9],
                base="ea54c2a2c",
            ),
        ]
        model = self.model

        class Space:
            name, acted = "shop", 0

            def landing_of(self, slug: str) -> dict:
                return landing

            def model(self) -> bm.Model:
                return model(*events)

        def refused(workspace: object, *args: str) -> subprocess.CompletedProcess:
            # what land.py's cmd_merge keeps for his merge that the moved base refused,
            # and the refusal it logs
            landing.update(
                merge_refused={
                    "tip": tip,
                    "by": "owner",
                    "via": "server",
                    "from": "lem",
                    "kind": "base",
                    "said": said[len("land.py: ") :],
                },
                owner_tap={
                    "tip": tip,
                    "not_green": [],
                    "via": "server",
                    "at": "2026-11-23T10:38:03Z",
                },
            )
            events.append(
                self.ev(
                    3,
                    "merge.refused",
                    by="owner",
                    via="server",
                    kind="base",
                    said=said[len("land.py: ") :],
                    tip=tip[:9],
                    **{"from": "lem"},
                )
            )
            return subprocess.CompletedProcess(args, 1, "", said + "\n")

        class Now:
            def __init__(
                self,
                target: Callable[[], None],
                name: str | None = None,
                daemon: object = None,
            ) -> None:
                self.target = target

            def start(self) -> None:
                self.target()

        with (
            mock.patch.object(serve, "merge_apart", refused),
            mock.patch.object(serve.threading, "Thread", Now),
        ):
            note = cast(
                "dict",
                serve.NOTES.get(
                    serve.merge_in_thread(
                        cast("serve.Workspace", Space()),
                        "gift-note",
                        landing,
                        "owner",
                        tip,
                    )
                ),
            )
        self.assertNotEqual(note["state"], "refused", note["said"])
        self.assertIn("stands", note["said"])
        self.assertEqual(
            note["said"],
            (
                "Your merge stands. It goes through when the merge agent’s read of "
                "the new base says safe."
            ),
        )

    def test_his_standing_merge_that_the_base_refuses_again_still_stands_in_its_note(
        self,
    ) -> None:
        # docs/backlog/a-second-press-during-the-server-s-standing-merge-gets-not-done-
        # when-the-base.md: the safe read logged merge.stands and the server runs his
        # merge with --standing; a press from an old page gets that merge's token; main
        # moves again, land.py refuses it with kind base and keeps his merge for
        # another read, so the note says that it stands, not "Not done."
        tip = "faac6eb3b" + "0" * 31
        landing = {"proposed": tip, "pr": {"number": 60}, "base": "main"}
        events = [
            *self.standing(tip),
            self.ev(
                9,
                "merge.review",
                verdict="call",
                calls=True,
                why="a careful request is merged by the owner",
                by="claude",
                tip=tip[:9],
                base="d48c6a9bd",
                base_call="safe",
                base_why="docs only",
            ),
            self.ev(10, "merge.stands", by="owner", tip=tip[:9], base="d48c6a9bd"),
            self.ev(
                11,
                "merge.start",
                by="owner",
                via="server",
                after="a read of the moved base",
                base="d48c6a9bd",
            ),
        ]
        model = self.model
        ran = []

        class Space:
            name, acted = "shop", 0

            def landing_of(self, slug: str) -> dict:
                return landing

            def model(self) -> bm.Model:
                return model(*events)

        def refused(workspace: object, *args: str) -> subprocess.CompletedProcess:
            ran.append(args)
            events.append(
                self.ev(
                    12,
                    "merge.refused",
                    by="owner",
                    via="server",
                    kind="base",
                    said="origin/main moved after the checks ran",
                    tip=tip[:9],
                    **{"from": "lem"},
                )
            )
            return subprocess.CompletedProcess(
                args, 1, "", "land.py: origin/main moved after the checks ran\n"
            )

        class Now:
            def __init__(
                self,
                target: Callable[[], None],
                name: str | None = None,
                daemon: object = None,
            ) -> None:
                self.target = target

            def start(self) -> None:
                self.target()

        self.addCleanup(serve.NOTES.merging.pop, ("shop", "gift-note"), None)
        with (
            mock.patch.object(serve, "merge_apart", refused),
            mock.patch.object(serve.threading, "Thread", Now),
        ):
            note = cast(
                "dict",
                serve.NOTES.get(
                    serve.merge_in_thread(
                        cast("serve.Workspace", Space()),
                        "gift-note",
                        landing,
                        "owner",
                        tip,
                        standing=True,
                    )
                ),
            )
        self.assertEqual(len(ran), 1)
        self.assertIn("--standing", ran[0])
        self.assertEqual(
            (note["state"], note["said"]),
            (
                "stands",
                (
                    "Your merge stands. It goes through when the merge agent’s read of "
                    "the new base says safe."
                ),
            ),
        )

    def standing_exit_before_start(self, line: str) -> dict:
        """The note of the server's standing merge of his, run after the safe read's
        `merge.stands`, when land.py exits 1 with LINE before it logs `merge.start`:
        nothing of this run refused his merge for a moved base."""
        tip = "faac6eb3b" + "0" * 31
        landing = {"proposed": tip, "pr": {"number": 60}, "base": "main"}
        events = [
            *self.standing(tip),
            self.ev(
                9,
                "merge.review",
                verdict="call",
                calls=True,
                why="a careful request is merged by the owner",
                by="claude",
                tip=tip[:9],
                base="d48c6a9bd",
                base_call="safe",
                base_why="docs only",
            ),
            self.ev(10, "merge.stands", by="owner", tip=tip[:9], base="d48c6a9bd"),
        ]
        model = self.model
        ran, failed = [], []

        class Space:
            name, acted = "shop", 0

            def landing_of(self, slug: str) -> dict:
                return landing

            def model(self) -> bm.Model:
                return model(*events)

        def refused(workspace: object, *args: str) -> subprocess.CompletedProcess:
            ran.append(args)
            return subprocess.CompletedProcess(args, 1, "", f"land.py: {line}\n")

        class Now:
            def __init__(
                self,
                target: Callable[[], None],
                name: str | None = None,
                daemon: object = None,
            ) -> None:
                self.target = target

            def start(self) -> None:
                self.target()

        self.addCleanup(serve.NOTES.merging.pop, ("shop", "gift-note"), None)
        with (
            mock.patch.object(serve, "merge_apart", refused),
            mock.patch.object(serve.threading, "Thread", Now),
        ):
            note = serve.NOTES.get(
                serve.merge_in_thread(
                    cast("serve.Workspace", Space()),
                    "gift-note",
                    landing,
                    "owner",
                    tip,
                    failed=lambda: failed.append(True),
                    standing=True,
                )
            )
        self.assertEqual((len(ran), failed), (1, [True]))
        return cast("dict", note)

    def test_his_standing_merge_whose_step_lock_is_held_is_refused_with_land_s_line(
        self,
    ) -> None:
        # the step lock is held by `lem land merge-review`: land.py exits 1 before its
        # merge.start, and the note keeps its line
        line = (
            "another step of gift-note runs now and holds its lock (step.lock in its "
            "task directory); it ends first, then this step runs again"
        )
        note = self.standing_exit_before_start(line)
        self.assertEqual((note["state"], note["said"]), ("refused", f"land.py: {line}"))

    def test_his_standing_merge_whose_merge_lock_cannot_open_is_refused_with_the_fix(
        self,
    ) -> None:
        # the merge lock cannot be opened: land.py's line holds the fix, an `rm -r` of
        # the lock, and the note keeps it
        line = (
            "the merge lock /shop/.lem/state/merge.lock cannot be opened (Is a "
            "directory); it holds no state, so remove it (`rm -r "
            "/shop/.lem/state/merge.lock`) and run `lem land merge gift-note` again"
        )
        note = self.standing_exit_before_start(line)
        self.assertEqual((note["state"], note["said"]), ("refused", f"land.py: {line}"))

    def standing(self, tip: str) -> tuple:
        # #60 at 10:38:03: the merge agent's read called him, his merge met a moved
        # base, and Lem keeps it
        return (
            self.ev(0, "proposed", green=True, not_green=[], tip=tip[:9]),
            self.state(1, "open", self.PR),
            self.ev(
                2,
                "merge.review",
                verdict="call",
                calls=True,
                why="a careful request is merged by the owner",
                by="claude",
                tip=tip[:9],
                base="ea54c2a2c",
            ),
            self.ev(
                8,
                "merge.refused",
                by="owner",
                via="server",
                kind="base",
                said="origin/main moved after the checks ran",
                tip=tip[:9],
                **{"from": "lem"},
            ),
        )

    def space(self, m: bm.Model, landing: dict) -> object:
        class Space:
            name, acted = "shop", 0

            def model(self) -> bm.Model:
                return m

            def landing_of(self, slug: str) -> dict:
                return landing

        return Space()

    def test_a_second_press_while_his_merge_stands_starts_nothing_and_says_it_stands(
        self,
    ) -> None:
        tip = "faac6eb3b" + "0" * 31
        landing = {"proposed": tip, "pr": {"number": 60}, "base": "main"}
        ran, threads = [], []
        space = self.space(self.model(*self.standing(tip)), landing)
        # a merge this test starts by mistake leaves no task in NOTES.merging for the
        # tests after it
        self.addCleanup(serve.NOTES.merging.pop, ("shop", "gift-note"), None)
        with (
            mock.patch.object(serve, "merge_apart", lambda *args: ran.append(args)),
            mock.patch.object(
                serve.threading, "Thread", lambda *a, **k: threads.append(k)
            ),
        ):
            note = cast(
                "dict",
                serve.NOTES.get(
                    serve.act_merge(
                        cast("serve.Workspace", space),
                        "gift-note",
                        {"confirm": "yes", "tip": tip},
                        "local",
                    )
                ),
            )
            self.assertEqual(
                (note["state"], note["said"]),
                (
                    "stands",
                    (
                        "Your merge stands. It goes through when the merge agent’s "
                        "read of the new base says safe."
                    ),
                ),
            )
            self.assertTrue(bm.same_tip(note["tip"], tip))
            self.assertEqual((ran, threads), ([], []))
            # a press while the server's merge of it runs gets that merge's token
            serve.NOTES.merging[("shop", "gift-note")] = "t0k3n"
            self.assertEqual(
                serve.act_merge(
                    cast("serve.Workspace", space),
                    "gift-note",
                    {"confirm": "yes", "tip": tip},
                    "local",
                ),
                "t0k3n",
            )
            serve.NOTES.merging.pop(("shop", "gift-note"), None)
            # while the forge calls the pull request conflicting, the answer is the
            # conflict's text
            conflicting = self.model(*self.standing(tip))
            conflicting.seen = {
                "gift-note": {"mergeable": "CONFLICTING", "head": tip[:12]}
            }
            note = cast(
                "dict",
                serve.NOTES.get(
                    serve.act_merge(
                        cast("serve.Workspace", self.space(conflicting, landing)),
                        "gift-note",
                        {"confirm": "yes", "tip": tip},
                        "local",
                    )
                ),
            )
            self.assertEqual(note["state"], "refused")
            self.assertIn("conflicting", note["said"])
            self.assertNotIn("stands", note["said"])
        self.assertEqual((ran, threads), ([], []))

    def test_a_press_whose_request_read_the_model_before_his_refusal_runs_no_second_merge(
        self,
    ) -> None:
        # the press's request read the model before the first merge's refusal was
        # logged, and reached the worker after it: the worker reads the task again, and
        # land.py does not run
        tip = "faac6eb3b" + "0" * 31
        landing = {"proposed": tip, "pr": {"number": 60}, "base": "main"}
        ran = []
        self.addCleanup(serve.NOTES.merging.pop, ("shop", "gift-note"), None)

        class Now:
            def __init__(
                self,
                target: Callable[[], None],
                name: str | None = None,
                daemon: object = None,
            ) -> None:
                self.target = target

            def start(self) -> None:
                self.target()

        with (
            mock.patch.object(serve, "merge_apart", lambda *args: ran.append(args)),
            mock.patch.object(serve.threading, "Thread", Now),
        ):
            note = cast(
                "dict",
                serve.NOTES.get(
                    serve.merge_in_thread(
                        cast(
                            "serve.Workspace",
                            self.space(self.model(*self.standing(tip)), landing),
                        ),
                        "gift-note",
                        landing,
                        "owner",
                        tip,
                    )
                ),
            )
        self.assertEqual(ran, [])
        self.assertEqual(
            (note["state"], note["said"]),
            (
                "stands",
                (
                    "Your merge stands. It goes through when the merge agent’s read of "
                    "the new base says safe."
                ),
            ),
        )
        self.assertNotIn(("shop", "gift-note"), serve.NOTES.merging)

    def test_the_servers_merge_takes_the_tip_that_was_read(self) -> None:
        # the merge agent's merge is of the tip its review read, the owner's that stood
        # of the tip he merged
        landing = {
            "proposed": "c" * 40,
            "merge_review": {"tip": "a" * 40, "verdict": "merge"},
            "owner_tap": {"tip": "b" * 40},
        }
        self.assertEqual(serve.merge_tip_of(landing, "merger"), "a" * 40)
        self.assertEqual(serve.merge_tip_of(landing, "owner"), "b" * 40)
        self.assertEqual(serve.merge_tip_of({"proposed": "c" * 40}, "merger"), "")

    def test_a_failed_bookkeeping_of_a_merged_pull_request_is_tried_again(self) -> None:
        key = ("gift-note", 41)
        self.assertTrue(serve.merged_due(key, set(), {}, 1000.0))
        self.assertFalse(serve.merged_due(key, {key}, {}, 1000.0))
        failed = {key: (1000.0, "`lem land merged gift-note` failed")}
        self.assertFalse(
            serve.merged_due(key, set(), failed, 1000.0 + serve.DUTY_RETRY - 1)
        )
        self.assertTrue(serve.merged_due(key, set(), failed, 1000.0 + serve.DUTY_RETRY))

    def test_a_demo_workspace_owes_nothing(self) -> None:
        merged = (self.state(0, "landed", "main: pull request ... is merged"),)
        self.assertEqual(
            serve.duties(self.model(*merged, demo=True), {}, {"gift-note"}), []
        )

    def test_the_list_of_sessions_reads_by_task(self) -> None:
        listed = serve.session_entries(
            '[{"task": "gift-note", "session": "S1", "live": true, "agent": '
            'false, "unanswered": false, "phase": "build", "sign": '
            '"2026-11-22T10:15:42Z", "shell": true, "signs": true, "turn": "runs"}]'
        )
        # the session's signs of work go on to the model, which the guard of a stopped
        # session and the rows of a held task read
        self.assertEqual(
            listed,
            {
                "gift-note": {
                    "live": True,
                    "agent": False,
                    "unanswered": False,
                    "unheard": None,
                    "session": "S1",
                    "name": None,
                    "sign": "2026-11-22T10:15:42Z",
                    "shell": True,
                    "signs": True,
                    "turn": "runs",
                }
            },
        )
        self.assertEqual(serve.session_entries('{"sessions": []}'), {})
        with self.assertRaises(ValueError):
            serve.session_entries('{"said": "no"}')


class MovedBaseRead(unittest.TestCase):
    """The merge agent's read of a moved base answers Lem's refusal of the merge when it
    says `safe`, and answers nothing when it says `another round` (criteria 1 and 4 of
    docs/plans/2026-11-22-moved-base-merge-agent-call.md, and its plan talk's questions
    3 and 6)."""

    PR = Duties.PR
    ev = staticmethod(Duties.ev)

    def model(self, *events: dict) -> bm.Model:
        return bm.derive(list(events), [], 1_800_000_000_000, meta={})

    def proposed(self) -> tuple:
        return (
            self.ev(0, "proposed", green=True, not_green=[], tip="abc123456"),
            self.state(1, "open", self.PR),
        )

    def state(self, minute: float, status: str, text: str) -> dict:
        return self.ev(minute, "task.state", status=status, text=text, lines=[])

    def refused(
        self,
        minute: float,
        by: str = "merger",
        kind: str = "base",
        said: str = "origin/main moved after the checks ran",
    ) -> dict:
        return self.ev(
            minute,
            "merge.refused",
            by=by,
            via="server",
            kind=kind,
            said=said,
            tip="abc123456",
            **{"from": "lem"},
        )

    def read(
        self,
        minute: float,
        call: str,
        verdict: str = "merge",
        *,
        calls: bool = False,
        base: str = "m2m2m2m2m",
    ) -> dict:
        return self.ev(
            minute,
            "merge.review",
            verdict=verdict,
            calls=calls,
            by="claude/opus:high",
            tip="abc123456",
            base=base,
            base_call=call,
            base_why="B changed only docs/board.md, which the change does not read",
        )

    def owed(self, *events: dict) -> list:
        return serve.duties(self.model(*events), {}, set())

    def test_a_safe_read_answers_lems_base_refusal_and_the_server_merges(self) -> None:
        first = (
            *self.proposed(),
            self.ev(
                2,
                "merge.review",
                verdict="merge",
                calls=False,
                by="claude/opus:high",
                tip="abc123456",
            ),
        )
        refused = (*first, self.refused(3))
        self.assertEqual(self.owed(*refused), [("wake", "gift-note", "refused")])
        safe = (
            *refused,
            self.ev(4, "session.wake", session="S1", why="refused"),
            self.read(5, "safe"),
        )
        t = self.model(*safe).tasks[0]
        self.assertIsNone(t.refused)
        self.assertTrue(serve.merge_due(t, {}, set()))
        self.assertEqual(self.owed(*safe), [("merge", "gift-note", "merger")])
        # the first read already saw the move, and no refusal came first
        self.assertEqual(
            self.owed(*self.proposed(), self.read(2, "safe")),
            [("merge", "gift-note", "merger")],
        )

    def test_the_owners_merge_a_moved_base_refused_goes_through_on_a_safe_read(
        self,
    ) -> None:
        refused = (
            *self.proposed(),
            self.ev(
                2,
                "merge.review",
                verdict="call",
                calls=True,
                why="it is careful",
                by="claude/opus:high",
                tip="abc123456",
            ),
            self.refused(3, by="owner"),
        )
        self.assertEqual(self.owed(*refused), [("wake", "gift-note", "refused")])
        # a careful change still gets `Verdict: call.`: the merge agent merges nothing,
        # and his merge stands
        safe = (
            *refused,
            self.ev(4, "session.wake", session="S1", why="refused"),
            self.read(5, "safe", verdict="call", calls=True),
            self.ev(
                5, "merge.stands", by="owner", tip="abc123456", **{"from": "abc123456"}
            ),
        )
        t = self.model(*safe).tasks[0]
        self.assertTrue(serve.stands_due(t, {}, set()))
        self.assertFalse(serve.merge_due(t, {}, set()))
        self.assertEqual(self.owed(*safe), [("merge", "gift-note", "owner")])

    def test_another_round_merges_nothing_and_the_session_lands_it_again(self) -> None:
        refused = (
            *self.proposed(),
            self.ev(
                2,
                "merge.review",
                verdict="merge",
                calls=False,
                by="claude/opus:high",
                tip="abc123456",
            ),
            self.refused(3),
        )
        woken = (*refused, self.ev(4, "session.wake", session="S1", why="refused"))
        # the record of an another-round read keeps a base refusal of its tip, with the
        # read's why
        again = (
            *woken,
            self.read(5, "another round"),
            self.refused(
                5,
                said=(
                    "the merge agent asks for another round of the checks: "
                    "B renamed a function the change calls"
                ),
            ),
        )
        t = self.model(*again).tasks[0]
        self.assertIsNotNone(t.refused)
        self.assertFalse(serve.merge_due(t, {}, set()))
        self.assertEqual(self.owed(*again), [("wake", "gift-note", "refused")])
        # a later read that says `safe` does not answer the refusal an another-round
        # read keeps: only the new landing does
        later = (
            *again,
            self.ev(6, "session.wake", session="S1", why="refused"),
            self.read(7, "safe"),
        )
        self.assertIsNotNone(self.model(*later).tasks[0].refused)
        self.assertEqual(self.owed(*later), [])
        # the new landing's proposal makes a new try
        landed = (
            *later,
            self.ev(8, "proposed", green=True, not_green=[], tip="def456789"),
            self.state(9, "open", self.PR),
            self.ev(
                9,
                "merge.review",
                verdict="merge",
                calls=False,
                by="claude/opus:high",
                tip="def456789",
                carried="abc123456",
            ),
        )
        self.assertEqual(self.owed(*landed), [("merge", "gift-note", "merger")])

    def test_a_read_on_the_checks_base_after_a_revert_answers_lems_base_refusal(
        self,
    ) -> None:
        # main went back to the checks' tree after the refusal: the brief named the
        # checks' own base, and its read, with no call on a move, answers the refusal,
        # so the server merges, the owner's merge too
        first = (
            *self.proposed(),
            self.ev(
                2,
                "merge.review",
                verdict="merge",
                calls=False,
                by="claude/opus:high",
                tip="abc123456",
            ),
        )
        back = (
            *first,
            self.refused(3),
            self.ev(4, "session.wake", session="S1", why="refused"),
            self.ev(
                5,
                "merge.review",
                verdict="merge",
                calls=False,
                by="claude/opus:high",
                tip="abc123456",
                base="m1m1m1m1m",
            ),
        )
        self.assertEqual(self.owed(*back), [("merge", "gift-note", "merger")])
        his = (
            *self.proposed(),
            self.refused(3, by="owner"),
            self.ev(4, "session.wake", session="S1", why="refused"),
            self.ev(
                5,
                "merge.review",
                verdict="call",
                calls=True,
                why="it is careful",
                by="claude/opus:high",
                tip="abc123456",
                base="m1m1m1m1m",
            ),
            self.ev(
                5,
                "merge.stands",
                by="owner",
                tip="abc123456",
                after="a read of the base back on the checks' tree",
                base="m1m1m1m1m",
            ),
        )
        self.assertEqual(self.owed(*his), [("merge", "gift-note", "owner")])

    def test_another_round_with_no_refusal_before_it_starts_no_merge(self) -> None:
        again = (*self.proposed(), self.read(2, "another round"))
        t = self.model(*again).tasks[0]
        self.assertFalse(serve.merge_due(t, {}, set()))
        stands = (
            *again,
            self.ev(
                3, "merge.stands", by="owner", tip="abc123456", **{"from": "abc123456"}
            ),
        )
        self.assertFalse(serve.stands_due(self.model(*stands).tasks[0], {}, set()))
        self.assertEqual(self.owed(*stands), [])

    def test_no_read_answers_githubs_refusal_or_a_rules(self) -> None:
        merge = (
            *self.proposed(),
            self.ev(
                2,
                "merge.review",
                verdict="merge",
                calls=False,
                by="claude/opus:high",
                tip="abc123456",
            ),
        )
        github = (
            *merge,
            self.ev(
                3,
                "merge.refused",
                by="merger",
                via="server",
                said="Required status check is expected",
                tip="abc123456",
                **{"from": "github"},
            ),
            self.read(4, "safe"),
        )
        self.assertIsNotNone(self.model(*github).tasks[0].refused)
        self.assertNotIn(("merge", "gift-note", "merger"), self.owed(*github))
        rule = (
            *merge,
            self.refused(3, kind="rule", said="the request is not green"),
            self.read(4, "safe"),
        )
        self.assertIsNotNone(self.model(*rule).tasks[0].refused)
        self.assertNotIn(("merge", "gift-note", "merger"), self.owed(*rule))

    def test_a_read_of_m2_does_not_cover_m3(self) -> None:
        safe = (*self.proposed(), self.read(2, "safe", base="m2m2m2m2m"))
        # the merge on m3 is refused for a new read: nothing merges until it says safe
        m3 = (
            *safe,
            self.refused(3, said="origin/main moved since the read of m2m2m2m2m"),
        )
        self.assertEqual(self.owed(*m3), [("wake", "gift-note", "refused")])
        self.assertEqual(
            self.owed(*m3, self.ev(4, "session.wake", session="S1", why="refused")), []
        )
        read = (
            *m3,
            self.ev(4, "session.wake", session="S1", why="refused"),
            self.read(5, "safe", base="m3m3m3m3m"),
        )
        self.assertEqual(self.owed(*read), [("merge", "gift-note", "merger")])


class StoppedSession(unittest.TestCase):
    """A task in its phase whose session stopped: live in agterm, an agent in its pane,
    and no sign of work for hours. The case of 2026-11-22 (merge-leaves-board-lock,
    #37): its checks ended at 10:54, the conversation had gone on in a background
    process of Claude Code that carried another task's pane, and that process stopped;
    at 15:37 the task still stood in `landing` and nothing woke it. The server owes it
    the status message at 11:39, the restart at 11:49 and, when the fresh session stops
    too, the stop (`bm.stop_due`, whose cases are in test_board_model.py)."""

    @staticmethod
    def ev(hhmm: str, event: str, **fields: object) -> dict:
        return {
            "ts": f"2026-11-22T{hhmm}{'' if hhmm.count(':') == 2 else ':00'}Z",
            "event": event,
            "task": "gift-note",
            **fields,
        }

    @staticmethod
    def now(hhmm: str) -> int:
        text = f"2026-11-22T{hhmm}{'' if hhmm.count(':') == 2 else ':00'}Z"
        return int(
            datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ")
            .replace(tzinfo=UTC)
            .timestamp()
            * 1000
        )

    @staticmethod
    def live(
        session: str = "S1",
        sign: str | None = "2026-11-22T10:15:42Z",
        *,
        shell: bool = False,
        signs: bool = True,
    ) -> dict:
        return {
            "gift-note": {
                "live": True,
                "agent": True,
                "unanswered": False,
                "session": session,
                "name": "gift-note",
                "sign": sign,
                "shell": shell,
                "signs": signs,
            }
        }

    @classmethod
    def landing(cls) -> tuple:
        return (
            cls.ev(
                "01:33",
                "session.open",
                session="S1",
                name="gift-note",
                phase="land",
                why="handoff",
            ),
            cls.ev(
                "10:15",
                "task.state",
                status="landing",
                text="the base moved: the checks run again",
                lines=[],
            ),
            cls.ev("10:18", "gate.start", tip="5ccc53d36", commands=1),
            cls.ev(
                "10:22",
                "gate",
                command="bash tests/all.sh",
                exit=0,
                last="all suites passed",
                tip="5ccc53d36",
            ),
            cls.ev("10:54", "gate.end", result="passed", seconds=2156, tip="5ccc53d36"),
        )

    def model(self, *events: dict, at: str, sessions: dict | None = None) -> bm.Model:
        m = bm.derive(list(events), [], self.now(at))
        m.sessions = self.live() if sessions is None else sessions
        return m

    def owed(self, *events: dict, at: str, sessions: dict | None = None) -> list:
        return [
            d
            for d in serve.duties(
                self.model(*events, at=at, sessions=sessions), {}, set()
            )
            if d[1] == "gift-note"
        ]

    def test_a_landing_with_no_event_for_hours_is_woken(self) -> None:
        self.assertEqual(self.owed(*self.landing(), at="11:38"), [])
        self.assertEqual(
            self.owed(*self.landing(), at="11:39"), [("wake", "gift-note", "status")]
        )
        self.assertEqual(
            self.owed(*self.landing(), at="15:37"), [("wake", "gift-note", "status")]
        )

    def test_a_session_that_still_works_is_not_woken(self) -> None:
        working = (*self.landing(), self.ev("15:35", "gate.wait", load=48.0, start=40))
        self.assertEqual(self.owed(*working, at="15:37"), [])
        # the checks run for 50 minutes with no event: their shell command is the sign
        # of work
        self.assertEqual(
            self.owed(*self.landing()[:3], at="11:08", sessions=self.live(shell=True)),
            [],
        )

    def test_ten_minutes_after_the_message_the_task_is_restarted_then_its_stop_logged(
        self,
    ) -> None:
        woken = (
            *self.landing(),
            self.ev("11:39", "session.wake", session="S1", why="status"),
        )
        self.assertEqual(self.owed(*woken, at="11:48"), [])
        self.assertEqual(
            self.owed(
                *woken, at="11:49", sessions=self.live(sign="2026-11-22T11:42:00Z")
            ),
            [],
        )
        self.assertEqual(
            self.owed(*woken, at="11:49"), [("open", "gift-note", "stopped")]
        )
        fresh = (
            *woken,
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
        self.assertEqual(
            self.owed(*fresh, at="11:49:20", sessions=self.live("S2", None)), []
        )
        self.assertEqual(
            self.owed(*fresh, at="12:34", sessions=self.live("S2", None)),
            [("wake", "gift-note", "status")],
        )
        again = (*fresh, self.ev("12:34", "session.wake", session="S2", why="status"))
        self.assertEqual(
            self.owed(*again, at="12:44", sessions=self.live("S2", None)),
            [("stopped", "gift-note", "stopped")],
        )
        logged = (*again, self.ev("12:44", "session.stopped", session="S2"))
        self.assertEqual(
            self.owed(*logged, at="12:44:20", sessions=self.live("S2", None)), []
        )

    def test_a_session_whose_signs_do_not_read_gets_the_message_then_its_stop_and_never_a_restart(
        self,
    ) -> None:
        # #37 as `lem session list` gave it all day: "signs": false
        unread = self.live(sign=None, signs=False)
        self.assertEqual(self.owed(*self.landing(), at="11:38", sessions=unread), [])
        self.assertEqual(
            self.owed(*self.landing(), at="11:39", sessions=unread),
            [("wake", "gift-note", "status")],
        )
        woken = (
            *self.landing(),
            self.ev("11:39", "session.wake", session="S1", why="status", unread=True),
        )
        self.assertEqual(self.owed(*woken, at="11:48", sessions=unread), [])
        self.assertEqual(
            self.owed(*woken, at="11:49", sessions=unread),
            [("stopped", "gift-note", "stopped")],
        )
        self.assertEqual(
            serve.duty_args(
                "stopped",
                "gift-note",
                "stopped",
                {},
                self.model(*woken, at="11:49", sessions=unread),
            ),
            ["stopped", "gift-note", "--session", "S1"],
        )
        logged = (
            *woken,
            self.ev("11:49", "session.stopped", session="S1", unread=True),
        )
        self.assertEqual(self.owed(*logged, at="11:50", sessions=unread), [])
        # the signs read again at 11:50: the logged stop waits for the owner's click, so
        # no `open … stopped`
        self.assertEqual(self.owed(*logged, at="11:50"), [])

    # the writer of the record, which the release after this one turns on
    @mock.patch("lem.board_model.WRITES_WORKED", True)
    def test_a_turn_read_after_an_unread_stop_is_logged_once_by_lem_session_worked(
        self,
    ) -> None:
        # the session takes a turn at 11:55 with no state block, and the signs read
        logged = (
            *self.landing(),
            self.ev("11:39", "session.wake", session="S1", why="status", unread=True),
            self.ev("11:49", "session.stopped", session="S1", unread=True),
        )
        turned = self.live(sign="2026-11-22T11:55:00Z")
        self.assertEqual(
            self.owed(*logged, at="11:56", sessions=turned),
            [("worked", "gift-note", "worked")],
        )
        self.assertEqual(
            serve.duty_args(
                "worked",
                "gift-note",
                "worked",
                {},
                self.model(*logged, at="11:56", sessions=turned),
            ),
            ["worked", "gift-note", "--session", "S1"],
        )
        worked = (
            *logged,
            self.ev(
                "11:56", "session.worked", session="S1", turn="2026-11-22T11:55:00Z"
            ),
        )
        self.assertEqual(self.owed(*worked, at="11:57", sessions=turned), [])

    def test_a_task_that_waits_for_the_owner_or_is_out_of_its_phase_is_not_woken(
        self,
    ) -> None:
        for status, text in (
            ("held", "the criteria wait for the owner"),
            ("queued", "after: other-task"),
            ("planned", "the plan waits for the owner"),
            ("blocked", "a builder ended two times with no report"),
            ("parked", "the owner parked it"),
            ("answered", "the report answers it"),
            ("dropped", "the owner dropped it"),
            ("open", "PR #12 opened"),
            ("landed", "merged as #12"),
        ):
            held = (
                self.ev(
                    "01:33",
                    "session.open",
                    session="S1",
                    name="gift-note",
                    phase="shape",
                    why="new",
                ),
                self.ev("10:15", "task.state", status=status, text=text, lines=[]),
            )
            self.assertEqual(
                [
                    d
                    for d in self.owed(*held, at="15:37")
                    if d[2] in ("status", "stopped")
                ],
                [],
                status,
            )

    def test_a_task_two_releases_back_is_not_woken_and_its_pull_request_is_still_watched(
        self,
    ) -> None:
        say = (
            "gift-note began on Lem 0.1.6, and Lem 0.3.0 reads only tasks begun "
            "on 0.2.0 or 0.3.0. ..."
        )
        stopped = (
            *self.landing(),
            self.ev(
                "10:56",
                "release.stop",
                began="0.1.6",
                running="0.3.0",
                branch="feat/gift-note",
                say=say,
            ),
        )
        self.assertEqual(
            self.owed(*self.landing(), at="15:37"), [("wake", "gift-note", "status")]
        )
        # its session would wake every 45 minutes into the same stop
        self.assertEqual(
            [
                d
                for d in self.owed(*stopped, at="15:37")
                if d[2] in ("status", "stopped")
            ],
            [],
        )
        opened = (
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
                status="open",
                text="pull request https://github.com/acme/shop/pull/41",
                lines=["green"],
            ),
            self.ev(
                "10:56",
                "release.stop",
                began="0.1.6",
                running="0.3.0",
                branch="feat/gift-note",
                say=say,
            ),
        )
        m = self.model(*opened, at="15:37")
        self.assertEqual(
            (m.tasks[0].status, m.tasks[0].info["label"]), ("open", "Blocked")
        )
        # a merge on GitHub is still recorded: `lem land merged` passes the guard
        self.assertEqual(
            serve.open_prs(m),
            [
                {
                    "task": "gift-note",
                    "n": 41,
                    "url": "https://github.com/acme/shop/pull/41",
                }
            ],
        )

    def test_a_step_that_acted_on_nothing_says_why_in_the_servers_log(self) -> None:
        import subprocess

        refused = subprocess.CompletedProcess(
            [],
            0,
            (
                '{"task": "gift-note", "acted": false, "why": "working", "say": '
                '"Lem did nothing for gift-note: ..."}'
            ),
            "",
        )
        self.assertEqual(serve.not_acted(refused), "Lem did nothing for gift-note: ...")
        self.assertEqual(
            serve.not_acted(
                subprocess.CompletedProcess(
                    [], 0, '{"task": "gift-note", "acted": true}', ""
                )
            ),
            "",
        )
        self.assertEqual(
            serve.not_acted(
                subprocess.CompletedProcess(
                    [], 0, '{"task": "gift-note", "woke": true}', ""
                )
            ),
            "",
        )

    def test_the_step_names_the_session_it_is_for(self) -> None:
        m = self.model(*self.landing(), at="15:37")
        self.assertEqual(
            serve.duty_args("wake", "gift-note", "status", {}, m),
            ["wake", "gift-note", "--why", "status", "--session", "S1"],
        )
        self.assertEqual(
            serve.duty_args("open", "gift-note", "stopped", {}, m),
            ["open", "gift-note", "--why", "stopped", "--session", "S1"],
        )
        self.assertEqual(
            serve.duty_args("stopped", "gift-note", "stopped", {}, m),
            ["stopped", "gift-note", "--session", "S1"],
        )
        self.assertEqual(
            serve.duty_args(
                "wake", "gift-note", "conflict", {"gift-note": {"head": "abc"}}, m
            ),
            ["wake", "gift-note", "--why", "conflict", "--head", "abc"],
        )
        self.assertEqual(
            serve.duty_args("open", "gift-note", "queue", {}, m),
            ["open", "gift-note", "--why", "queue"],
        )


class StoppedOpen(unittest.TestCase):
    """The owner's "Open a session" on a task whose stop the guard logged (criterion 5):
    `lem session open SLUG --why stopped` beside its live session, and when the look
    once more finds work, the owner's words and no session; a stopped session that is
    gone takes the open of a task with none."""

    class Space:
        name = "shop"

        def __init__(self, m: bm.Model) -> None:
            self.m, self.looked = m, 0

        def model(self) -> bm.Model:
            return self.m

        def look_sessions(self) -> None:
            self.looked += 1

    def stopped(self, *, live: bool = True) -> StoppedOpen.Space:
        s = StoppedSession
        events = (
            *s.landing(),
            s.ev("11:39", "session.wake", session="S1", why="status"),
            s.ev(
                "11:49",
                "session.open",
                session="S2",
                name="gift-note",
                phase="land",
                why="stopped",
            ),
            s.ev("12:34", "session.wake", session="S2", why="status"),
            s.ev("12:44", "session.stopped", session="S2"),
        )
        m = bm.derive(list(events), [], s.now("13:00"))
        m.sessions = {
            "gift-note": {
                "live": live,
                "agent": live,
                "unanswered": False,
                "session": "S2",
                "name": "gift-note",
                "sign": None,
                "shell": False,
                "signs": live,
            }
        }
        return self.Space(m)

    def act(self, space: StoppedOpen.Space, printed: dict) -> tuple[dict, list, list]:
        asked = []
        ran = mock.Mock(
            side_effect=lambda workspace, *args: (
                asked.append(args)
                or subprocess.CompletedProcess(args, 0, json.dumps(printed), "")
            )
        )
        logged = mock.Mock(return_value="")
        with (
            mock.patch.object(serve, "session_run", ran),
            mock.patch.object(serve, "asked_from", logged),
        ):
            said = serve.act_session(
                cast("serve.Workspace", space), "gift-note", {}, "board"
            )
        return said, asked, logged.call_args_list

    def test_the_button_opens_beside_the_stopped_session(self) -> None:
        said, asked, logged = self.act(
            self.stopped(),
            {
                "task": "gift-note",
                "session": "S3",
                "name": "gift-note",
                "already": False,
                "acted": True,
            },
        )
        self.assertEqual(asked, [("open", "gift-note", "--why", "stopped")])
        self.assertTrue(said["ok"])
        self.assertIn("beside the one that stopped", said["said"])
        self.assertEqual(len(logged), 1)

    def test_an_open_that_finds_work_says_so_and_opens_nothing(self) -> None:
        space = self.stopped()
        said, _, logged = self.act(
            space,
            {
                "task": "gift-note",
                "session": "S2",
                "acted": False,
                "why": "working",
                "say": "Lem did nothing for gift-note: ...",
            },
        )
        self.assertEqual(
            said,
            {"ok": False, "said": "Its session works again, so no session was opened."},
        )
        # no record of an open he did not get, and the board looks at the sessions again
        self.assertEqual((logged, space.looked), ([], 1))
        for why in ("gone", "status", "unread"):
            said, _, _ = self.act(
                self.stopped(), {"task": "gift-note", "acted": False, "why": why}
            )
            self.assertEqual(
                said, {"ok": False, "said": serve.NOT_OPENED[why] + "."}, why
            )

    def test_a_stopped_session_that_is_gone_takes_the_open_of_a_task_with_none(
        self,
    ) -> None:
        _, asked, _ = self.act(
            self.stopped(live=False),
            {
                "task": "gift-note",
                "session": "S3",
                "name": "gift-note",
                "already": False,
            },
        )
        self.assertEqual(asked, [("open", "gift-note", "--why", "dead")])


class DutyKey(unittest.TestCase):
    def test_a_failed_merge_waits_for_its_own_tip_only(self) -> None:
        old = serve.duty_key("merge", "gift-note", "merger", {"proposed": "aaa111"})
        new = serve.duty_key("merge", "gift-note", "merger", {"proposed": "bbb222"})
        self.assertNotEqual(
            old, new
        )  # the task landed again: the new tip is merged at the next look
        self.assertEqual(
            old, serve.duty_key("merge", "gift-note", "merger", {"proposed": "aaa111"})
        )
        self.assertEqual(
            serve.duty_key("wake", "gift-note", "merged", {}),
            ("wake", "gift-note", "merged"),
        )

    def test_a_failed_merge_waits_for_its_own_read_only(self) -> None:
        # a refused merge waits DUTY_RETRY for the read it ran on; a new read of the
        # moved base makes a new key
        tip = "a" * 40
        first = serve.duty_key(
            "merge",
            "gift-note",
            "merger",
            {
                "proposed": tip,
                "merge_review": {"tip": tip, "at": "2026-11-22T10:00:00Z"},
            },
        )
        second = serve.duty_key(
            "merge",
            "gift-note",
            "merger",
            {
                "proposed": tip,
                "merge_review": {"tip": tip, "at": "2026-11-22T10:04:00Z"},
            },
        )
        self.assertNotEqual(first, second)
        self.assertEqual(
            first,
            serve.duty_key(
                "merge",
                "gift-note",
                "merger",
                {
                    "proposed": tip,
                    "merge_review": {"tip": tip, "at": "2026-11-22T10:00:00Z"},
                },
            ),
        )
        # a review of another tip is no read of this one
        self.assertEqual(
            serve.duty_key(
                "merge",
                "gift-note",
                "owner",
                {
                    "proposed": tip,
                    "merge_review": {"tip": "b" * 40, "at": "2026-11-22T10:00:00Z"},
                },
            ),
            serve.duty_key("merge", "gift-note", "owner", {"proposed": tip}),
        )

    def test_the_merge_after_a_new_safe_read_runs_at_the_next_look(self) -> None:
        from types import SimpleNamespace
        from unittest import mock

        tip = "abc123456" + "0" * 31
        ev = Duties.ev
        events = [
            ev(0, "proposed", green=True, not_green=[], tip=tip[:9]),
            ev(1, "task.state", status="open", text=Duties.PR, lines=[]),
            ev(
                2,
                "merge.review",
                verdict="merge",
                calls=False,
                by="claude",
                tip=tip[:9],
                base="m2m2m2m2m",
                base_call="safe",
                base_why="docs only",
            ),
        ]
        landing = {
            "proposed": tip,
            "merge_review": {
                "tip": tip,
                "verdict": "merge",
                "at": "2026-11-22T10:00:00Z",
            },
        }
        w = SimpleNamespace(
            name="shop",
            forge={},
            kept=set(),
            failed={},
            model=lambda: bm.derive(list(events), [], 1_800_000_000_000, meta={}),
            landing_of=lambda slug: landing,
        )
        started = []
        with (
            mock.patch.object(
                serve,
                "merge_in_thread",
                lambda workspace, slug, landing, by, tip, failed, standing=False: (
                    started.append(by),
                    failed(),
                ),
            ),
            mock.patch.object(serve.time, "monotonic", lambda: 1000.0),
        ):
            serve.run_duties(cast("serve.Workspace", w), now=1000.0)
            # the merge on m2 failed for the read of m2: the next look waits DUTY_RETRY
            # for that read
            serve.run_duties(cast("serve.Workspace", w), now=1010.0)
            self.assertEqual(started, ["merger"])
            # a new read of the moved base said safe: its merge runs at the server's
            # next look
            events[-1] = {**events[-1], "base": "m3m3m3m3m"}
            landing["merge_review"] = {
                **landing["merge_review"],
                "at": "2026-11-22T10:04:00Z",
            }
            serve.run_duties(cast("serve.Workspace", w), now=1020.0)
        self.assertEqual(started, ["merger", "merger"])


class ForgeLookBesideAMerge(unittest.TestCase):
    """The look at the forge leaves a task whose merge this server runs to that merge,
    also when the merge ends during the look: no `lem land merged` for it, and no line
    on the status bar that it failed. GitHub, land.py's look and the bookkeeping are
    stand-ins; one call of `forge_once` each."""

    class Place:
        def __init__(self) -> None:
            self.name, self.path, self.acted = "shop", "/lem-unit/shop", 0
            self.state = Path("/lem-unit/shop/.lem/state")
            self.forge: dict = {"looked": None, "problem": None, "done": set()}

        def model(self) -> object:
            return type("Model", (), {"meta": {}})()

        def settings(self) -> dict:
            return {"main": self.path, "branch": {"base": "main"}}

    def test_a_task_whose_merge_runs_gets_no_merged_and_no_problem_line_and_another_still_gets_its_line(
        self,
    ) -> None:
        import subprocess
        from unittest import mock

        prs = [
            {"task": "gift-note", "n": 1, "url": "https://github.com/acme/shop/pull/1"},
            {"task": "tax-line", "n": 2, "url": "https://github.com/acme/shop/pull/2"},
        ]
        land = type(
            "Land",
            (),
            {
                "LandError": type("LandError", (Exception,), {}),
                "forge_look": staticmethod(
                    lambda main, base, due: {
                        1: {"state": "MERGED"},
                        2: {"state": "MERGED"},
                    }
                ),
            },
        )
        ran = []

        def run(name: str, repo: Path, *args: str) -> subprocess.CompletedProcess:
            ran.append(args)
            return subprocess.CompletedProcess(
                [],
                1,
                "",
                "land.py: another step of the task runs; run it again when it ends\n",
            )

        place = self.Place()
        with (
            mock.patch.object(serve, "open_prs", lambda model: prs),
            mock.patch.object(serve, "has_forge", lambda w, m: True),
            mock.patch.object(serve.shutil, "which", lambda name: "/lem-unit/bin/gh"),
            mock.patch("lem.land", land, create=True),
            mock.patch.object(serve.lem_sibling, "run", run),
            mock.patch.object(serve, "keep_forge_look", lambda *a: None),
            mock.patch.dict(serve.NOTES.merging, {("shop", "gift-note"): "token"}),
        ):
            looked = serve.forge_once(cast("serve.Workspace", place), now=1000)
        self.assertEqual(
            ran, [("merged", "tax-line")], "no `merged` for gift-note, whose merge runs"
        )
        self.assertEqual([x["task"] for x in looked], ["tax-line"])
        self.assertNotIn("gift-note", place.forge["problem"])
        self.assertEqual(
            place.forge["problem"],
            (
                "`lem land merged tax-line` failed after GitHub called pull request 2 "
                "merged: land.py: another step of the task runs; run it again when it "
                "ends; the board tries it again in a few minutes"
            ),
        )
        self.assertEqual(list(place.forge["failed"]), [("tax-line", 2)])

    def test_a_merge_that_ends_during_the_look_at_github_gets_no_merged_and_no_problem_line(
        self,
    ) -> None:
        import subprocess
        from unittest import mock

        prs = [
            {"task": "gift-note", "n": 1, "url": "https://github.com/acme/shop/pull/1"}
        ]

        def look(main: Path, base: str, due: list[int]) -> dict:
            # the merge's process ends while `gh` answers: its thread takes the task
            # off NOTES.merging
            serve.NOTES.merging.pop(("shop", "gift-note"))
            return {1: {"state": "MERGED"}}

        land = type(
            "Land",
            (),
            {
                "LandError": type("LandError", (Exception,), {}),
                "forge_look": staticmethod(look),
            },
        )
        ran = []

        def run(name: str, repo: Path, *args: str) -> subprocess.CompletedProcess:
            ran.append(args)
            return subprocess.CompletedProcess(
                [],
                1,
                "",
                (
                    "land.py: the task is 'landed' and has a pull request; "
                    "it is merged already\n"
                ),
            )

        place = self.Place()
        with (
            mock.patch.object(serve, "open_prs", lambda model: prs),
            mock.patch.object(serve, "has_forge", lambda w, m: True),
            mock.patch.object(serve.shutil, "which", lambda name: "/lem-unit/bin/gh"),
            mock.patch("lem.land", land, create=True),
            mock.patch.object(serve.lem_sibling, "run", run),
            mock.patch.object(serve, "keep_forge_look", lambda *a: None),
            mock.patch.dict(serve.NOTES.merging, {("shop", "gift-note"): "token"}),
        ):
            looked = serve.forge_once(cast("serve.Workspace", place), now=1000)
        self.assertEqual(
            ran, [], "no `merged` for gift-note, whose merge ran when the look began"
        )
        self.assertEqual(looked, [])
        self.assertIsNone(place.forge["problem"])


class Prune(unittest.TestCase):
    """The keeping of the state folder, a duty of the server across tasks:
    `lem project prune` at the first look and each PRUNE_SECONDS after, never for
    example tasks, and one log line when it did something."""

    class Place:
        def __init__(self, *, demo: bool = False) -> None:
            self.name, self.path, self.pruned, self.demo = (
                "shop",
                "/lem-unit/shop",
                None,
                demo,
            )

        def model(self) -> object:
            return type("Model", (), {"meta": {"demo": True} if self.demo else {}})()

        def settings(self) -> dict:
            return {"root": self.path}

    def test_it_runs_at_the_first_look_then_each_period_and_never_for_example_tasks(
        self,
    ) -> None:
        import subprocess
        from unittest import mock

        ran = []
        said = (
            '{"said": "removed 3 files", "files": 3, "bytes": 120, "skipped": '
            '[], "failed": []}'
        )

        def run(
            workspace: object, file: str, *args: str
        ) -> subprocess.CompletedProcess:
            ran.append((file, *args))
            return subprocess.CompletedProcess([], 0, said, "")

        place = self.Place()
        with mock.patch.object(serve, "lem_run", run):
            first = cast(
                "dict", serve.prune_once(cast("serve.Workspace", place), now=1000.0)
            )
            self.assertIsNone(
                serve.prune_once(
                    cast("serve.Workspace", place), now=1000.0 + serve.PRUNE_SECONDS - 1
                )
            )
            again = cast(
                "dict",
                serve.prune_once(
                    cast("serve.Workspace", place), now=1000.0 + serve.PRUNE_SECONDS
                ),
            )
            self.assertIsNone(
                serve.prune_once(
                    cast("serve.Workspace", self.Place(demo=True)), now=1000.0
                )
            )
        self.assertEqual(ran, [("project.py", "prune"), ("project.py", "prune")])
        self.assertEqual(
            (first["exit"], first["said"], first["files"], again["bytes"]),
            (0, "removed 3 files", 3, 120),
        )

    def test_the_log_says_what_it_removed_skipped_and_failed_and_nothing_else(
        self,
    ) -> None:
        quiet = {
            "exit": 0,
            "said": "removed 0 files",
            "files": 0,
            "folders": 0,
            "bytes": 0,
            "events": 0,
            "skipped": [],
            "failed": [],
        }
        self.assertIsNone(serve.prune_line("shop", quiet))
        line = serve.prune_line(
            "shop",
            {
                **quiet,
                "exit": 1,
                "skipped": [{"path": "tasks/x", "why": "its state.md does not read"}],
                "failed": [{"path": "tasks/y/a.log", "error": "Permission denied"}],
            },
        )
        self.assertEqual(
            line,
            (
                "serve.py: shop: `lem project prune` exited 1: removed 0 files; "
                "skipped tasks/x: its state.md does not read; failed tasks/y/a.log: "
                "Permission denied\n"
            ),
        )

    def test_the_log_names_a_run_that_removed_only_an_empty_file(self) -> None:
        import subprocess
        from unittest import mock

        said = (
            '{"said": "removed 1 files of 1 ended tasks", "tasks": [{"task": '
            '"x", "files": ["empty.txt"], "bytes": 0}], "files": 1, "folders": '
            '[], "bytes": 0, "events": 0, "skipped": [], "failed": []}'
        )
        with mock.patch.object(
            serve, "lem_run", return_value=subprocess.CompletedProcess([], 0, said, "")
        ):
            ran = cast(
                "dict",
                serve.prune_once(cast("serve.Workspace", self.Place()), now=1000.0),
            )
        self.assertEqual((ran["files"], ran["bytes"], ran["events"]), (1, 0, 0))
        self.assertEqual(
            serve.prune_line("shop", ran),
            (
                "serve.py: shop: `lem project prune` exited 0: "
                "removed 1 files of 1 ended tasks\n"
            ),
        )
        empty_folder = {
            **ran,
            "files": 0,
            "folders": 1,
            "said": "removed 0 files, and removed 1 old folders and copies, 0.0 MB",
        }
        self.assertEqual(
            serve.prune_line("shop", empty_folder),
            (
                "serve.py: shop: `lem project prune` exited 0: removed 0 files, and "
                "removed 1 old folders and copies, 0.0 MB\n"
            ),
        )

    def test_the_log_names_the_events_a_prune_summarized(self) -> None:
        import subprocess
        from unittest import mock

        said = (
            '{"said": "removed 0 files, replaced the 60 events of 1 such tasks", '
            '"files": 0, "bytes": 0, "events": 60, "skipped": [], "failed": []}'
        )
        with mock.patch.object(
            serve, "lem_run", return_value=subprocess.CompletedProcess([], 0, said, "")
        ):
            ran = serve.prune_once(cast("serve.Workspace", self.Place()), now=1000.0)
        self.assertEqual(
            serve.prune_line("shop", cast("dict", ran)),
            (
                "serve.py: shop: `lem project prune` exited 0: removed 0 files, "
                "replaced the 60 events of 1 such tasks\n"
            ),
        )


class KeepDays(unittest.TestCase):
    """The number of `state.keep_days` the page of a pruned task says: the settings' as
    they read now, and none while they do not read, even with an older read on hand."""

    @staticmethod
    def reader(settings: object, problems: dict | None = None) -> bm.Reader:
        # a stand-in with the two facts keep_days_of reads
        return cast(
            "bm.Reader",
            type("Reader", (), {"settings": settings, "problems": problems or {}})(),
        )

    def test_the_page_gets_the_settings_number_of_now(self) -> None:
        self.assertEqual(
            serve.keep_days_of(
                self.reader({"state": {"keep_days": 30, "from": "default"}})
            ),
            30,
        )
        self.assertEqual(
            serve.keep_days_of(
                self.reader(
                    {"state": {"keep_days": 7, "from": ".lem/project.local.toml"}}
                )
            ),
            7,
        )

    def test_settings_that_do_not_read_give_no_number(self) -> None:
        old = {"state": {"keep_days": 30, "from": "default"}}
        self.assertIsNone(
            serve.keep_days_of(
                self.reader(old, {"settings": "the settings do not read: bad TOML"})
            )
        )
        self.assertIsNone(serve.keep_days_of(self.reader(None)))


class WorkingSession(unittest.TestCase):
    """A held task whose session works on the owner's answer, as the server's look at
    the task sessions sees it on the model it keeps (waits-for-you-only-when-it-waits,
    criteria 1 and 2): the rows of a page and of the server's count follow each look,
    and an open page gets a refresh when the turn starts or ends."""

    EVENTS = [
        {
            "ts": "2026-11-23T09:53:42Z",
            "event": "session.open",
            "task": "gift-note",
            "session": "S1",
            "name": "gift-note",
            "phase": "shape",
            "why": "new",
        },
        {
            "ts": "2026-11-23T11:39:31Z",
            "event": "task.state",
            "task": "gift-note",
            "status": "held",
            "text": "the criteria wait for the owner",
            "lines": [],
        },
    ]

    def test_each_look_at_the_sessions_puts_the_turn_on_the_kept_model(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as folder:
            space = serve.Workspace("shop", folder)
            kept = bm.derive(
                list(self.EVENTS), [], cast("int", bm.at("2026-11-23T11:43:00Z"))
            )
            space.reader.current = lambda board, now=None: kept
            space.settings = lambda: {"root": folder}

            def look(turn: str) -> list:
                said = json.dumps(
                    [
                        {
                            "task": "gift-note",
                            "session": "S1",
                            "live": True,
                            "agent": True,
                            "unanswered": False,
                            "turn": turn,
                        }
                    ]
                )
                with mock.patch.object(
                    serve,
                    "session_run",
                    return_value=subprocess.CompletedProcess(["list"], 0, said, ""),
                ):
                    space.look_sessions()
                return [w["key"] for w in bm.waits_of(space.model())]

            self.assertEqual(
                (look("ended"), space.acted),
                (["criterion:gift-note:20261123T113931Z"], 0),
            )
            self.assertEqual((look("runs"), space.acted), ([], 1))
            self.assertEqual((look("runs"), space.acted), ([], 1))
            self.assertEqual(
                (look("ended"), space.acted),
                (["criterion:gift-note:20261123T113931Z"], 2),
            )


class Look(unittest.TestCase):
    """The command's look for the server (`lem.__main__`): its pid file, and whether that
    process lives."""

    def test_a_server_lives_only_where_its_pid_file_names_a_live_process(self) -> None:
        import os
        import subprocess
        import tempfile

        from lem import __main__ as command

        with tempfile.TemporaryDirectory() as folder:
            self.assertFalse(command.server_lives(folder), "no pid file")
            pid_file = Path(folder) / command.PID_FILE
            pid_file.write_text(f"{os.getpid()} 4536\n")
            self.assertTrue(command.server_lives(folder))
            ended = subprocess.run(
                [sys.executable, "-c", "import os; print(os.getpid())"],
                capture_output=True,
                text=True,
                check=True,
            )
            pid_file.write_text(f"{ended.stdout.strip()} 4536\n")
            self.assertFalse(command.server_lives(folder), "a process that ended")
            pid_file.write_text("0 4536\n")
            self.assertFalse(command.server_lives(folder), "0 names a process group")

    def test_the_look_starts_the_server_under_the_commands_own_python(self) -> None:
        import os
        import tempfile
        from unittest import mock

        from lem import __main__ as command

        started = []
        with tempfile.TemporaryDirectory() as folder:
            outside = {
                key: value for key, value in os.environ.items() if key != "LEM_SERVE"
            }
            with (
                mock.patch.dict(
                    os.environ, {**outside, "XDG_CONFIG_HOME": folder}, clear=True
                ),
                mock.patch.object(
                    command.subprocess, "Popen", lambda args, **_: started.append(args)
                ),
            ):
                command.look_for_server()
                os.environ["LEM_SERVE"] = "off"
                command.look_for_server()
        self.assertEqual(
            len(started), 1, "one start with no LEM_SERVE, none with LEM_SERVE=off"
        )
        self.assertEqual(
            started[0],
            [sys.executable, "-B", str(paths.MAIN), "serve", "--ensure"],
        )


class LogLook(unittest.TestCase):
    """The stream's look at the event log after `lem project prune` replaced it
    (criterion 4 of the task old-task-events-summarized): a change is told also when the
    count of lines is the same, and a page that reconnects with the id from before the
    rewrite is told at once."""

    def test_three_old_events_that_become_one_while_two_new_ones_come_are_a_change(
        self,
    ) -> None:
        import json
        import tempfile

        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder)
            log = state / serve.EVENT_LOG
            old = [
                {
                    "ts": f"2026-10-01T09:0{n}:00Z",
                    "event": "gate",
                    "task": "report-dates",
                }
                for n in range(3)
            ]
            log.write_text(
                "".join(
                    json.dumps(e) + "\n"
                    for e in [
                        *old,
                        {
                            "ts": "2026-11-20T09:00:00Z",
                            "event": "task.state",
                            "task": "gift-note",
                        },
                    ]
                )
            )
            look = serve.Look(state, {})
            version, changed = look.changes()
            self.assertEqual(version, bm.log_version(log.stat().st_ino, 4))
            self.assertEqual(look.changes(), (version, None))
            new = state / "events.new"
            new.write_text(
                "".join(
                    json.dumps(e) + "\n"
                    for e in [
                        {
                            "ts": "2026-10-01T09:02:00Z",
                            "event": "task.summary",
                            "task": "report-dates",
                        },
                        {
                            "ts": "2026-11-20T09:00:00Z",
                            "event": "task.state",
                            "task": "gift-note",
                        },
                        {
                            "ts": "2026-11-20T09:05:00Z",
                            "event": "task.state",
                            "task": "gift-note",
                        },
                        {
                            "ts": "2026-11-20T09:06:00Z",
                            "event": "session.transcript",
                            "task": "gift-note",
                        },
                    ]
                )
            )
            new.replace(log)
            now, changed = look.changes()
            self.assertIsNotNone(
                changed, "the same count of lines on a new log is a change"
            )
            self.assertEqual(now, bm.log_version(log.stat().st_ino, 4))
            self.assertNotEqual(now, version)
            # a page that reconnects with the id it saw before the rewrite is behind;
            # one with the id now, or none, is not
            self.assertTrue(serve.behind(version, now))
            self.assertFalse(serve.behind(now, now))
            self.assertFalse(serve.behind(None, now))
            self.assertFalse(serve.behind("", now))
            self.assertEqual(
                serve.refresh(now),
                (
                    f"id: {now}\ndata: <turbo-stream "
                    'action="refresh"></turbo-stream>\n\n'
                ).encode(),
            )

    def test_a_log_replaced_between_the_look_at_its_name_and_its_open_is_counted_from_its_start(
        self,
    ) -> None:
        import tempfile
        from unittest import mock

        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder)
            log = state / serve.EVENT_LOG
            log.write_bytes(b"{}\n" * 10)
            look = serve.Look(state, {})
            self.assertEqual(look.count(), 10)
            with log.open("ab") as out:
                out.write(b"{}\n")
            new = state / "events.new"
            new.write_bytes(b"{}\n" * 3)
            real_open = Path.open

            def open_after_replace(path: Path, mode: str = "r") -> IO:
                if path == log and new.exists():
                    new.replace(log)
                return real_open(path, mode)

            with mock.patch.object(Path, "open", open_after_replace):
                self.assertEqual(look.count(), 3)
            self.assertEqual(look.version(), bm.log_version(log.stat().st_ino, 3))


class Configure(unittest.TestCase):
    """`lem serve --port N` (`configure`): what the machine's file holds decides whether
    it stops the running board, and it never stops one when the write that follows would
    be refused. Each case has a home folder of its own as XDG_CONFIG_HOME; the server it
    would stop and the one it starts are stand-ins."""

    def setUp(self) -> None:
        import os
        import tempfile

        self.folder = tempfile.TemporaryDirectory()
        self.home = mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": self.folder.name})
        self.home.start()
        self.file = serve.lem_state.machine_file()
        self.file.parent.mkdir(parents=True)

    def tearDown(self) -> None:
        self.home.stop()
        self.folder.cleanup()

    def configure(self, port: int) -> tuple[object, mock.Mock, mock.Mock, mock.Mock]:
        import argparse

        args = argparse.Namespace(
            port=port, tailscale_port=None, tailscale=False, tailscale_off=False
        )
        with (
            mock.patch.object(serve, "ask", return_value={"pid": 1}) as asked,
            mock.patch.object(serve, "stop_server") as stopped,
            mock.patch.object(
                serve, "ensure_held", return_value={"running": True}
            ) as started,
        ):
            try:
                return serve.configure(args), asked, stopped, started
            except serve.lem_state.StateError as error:
                return error, asked, stopped, started

    def test_another_table_of_the_wrong_type_is_refused_before_the_board_stops(
        self,
    ) -> None:
        text = '[load]\nstart = "fast"\n\n[serve]\nport = 8800\n'
        self.file.write_text(text, encoding="utf-8")
        said, _, stopped, started = self.configure(8801)
        self.assertIsInstance(said, serve.lem_state.StateError)
        self.assertIn("load.start", str(said))
        stopped.assert_not_called()
        started.assert_not_called()
        self.assertEqual(self.file.read_text(encoding="utf-8"), text)

    def test_a_dotted_serve_key_is_written_after_the_stop_and_the_board_starts_again(
        self,
    ) -> None:
        # the review of a-write-of-machine-toml-drops-the-comments, 2026-11-24: the
        # write after the stop refused the dotted form, and no server started again
        self.file.write_text("serve.tailscale_port = 4540\n", encoding="utf-8")
        said, asked, stopped, started = self.configure(4600)
        self.assertNotIsInstance(said, Exception)
        asked.assert_called_once_with(serve.PORT)
        stopped.assert_called_once()
        started.assert_called_once()
        self.assertEqual(
            serve.lem_state.machine_tables(),
            {"serve": {"tailscale": False, "port": 4600, "tailscale_port": 4540}},
        )

    def test_a_serve_table_its_own_fix_names_is_written_again_from_the_flags(
        self,
    ) -> None:
        for text in ('[serve]\nport = "8800"\n', "[serve]\nport = 8800\nhost = 1\n"):
            with self.subTest(text=text):
                self.file.write_text("[load]\nstart = 4\n\n" + text, encoding="utf-8")
                said, asked, _, started = self.configure(8801)
                self.assertNotIsInstance(said, Exception)
                asked.assert_called_once_with(serve.PORT)
                started.assert_called_once()
                self.assertEqual(
                    serve.lem_state.machine_tables(),
                    {
                        "load": {"start": 4},
                        "serve": {
                            "tailscale": False,
                            "port": 8801,
                            "tailscale_port": serve.TAILNET_PORT,
                        },
                    },
                )


class SwitcherCount(unittest.TestCase):
    """docs/backlog/the-switcher-s-count-of-this-board-lags-the-sidebar-for-up-to-5-
    seconds.md: the page's row of "this board" in the switcher and its sidebar's "Waits
    for you" count the same model, also within REFRESH_SECONDS of a change."""

    @staticmethod
    def held(slug: str, minute: int) -> str:
        return json.dumps(
            {
                "ts": f"2026-11-22T10:{minute:02d}:00Z",
                "event": "task.state",
                "task": slug,
                "status": "held",
                "text": "the interview waits for the owner",
                "lines": [],
            }
        )

    def test_this_board_s_row_counts_what_the_sidebar_counts_right_after_a_change(
        self,
    ) -> None:
        import tempfile

        class Peers:
            trouble = None

            def states(self) -> list:
                return []

        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder) / ".lem" / "state"
            state.mkdir(parents=True)
            log = state / serve.EVENT_LOG
            log.write_text(self.held("gift-note", 0) + "\n", encoding="utf-8")
            handler = serve.Handler.__new__(serve.Handler)
            handler.headers = email.message.Message()
            handler.client_address = ("127.0.0.1", 0)
            handler.machine = serve.Machine()
            handler.peers = cast("serve.lem_peers.Peers", Peers())
            with mock.patch.object(
                serve.lem_state, "workspaces", return_value=[folder]
            ):
                workspace = handler.machine.workspaces()[0]

                def counts() -> tuple[int, int]:
                    ctx = handler.context(workspace, "")
                    here = next(s for s in ctx.spaces if serve.pages.is_here(ctx, s))
                    sidebar = len(bm.wait_stacks(bm.waits_of(ctx.model)))
                    return here["waits"], sidebar

                self.assertEqual(counts(), (1, 1))
                # a second task waits now, a second after the first page
                with log.open("a", encoding="utf-8") as file:
                    file.write(self.held("refund-rounding", 1) + "\n")
                self.assertEqual(counts(), (2, 2))


class PeersTrouble(unittest.TestCase):
    """A `[peers]` table with a line that does not read: a page of the board says
    why among its problems, instead of a list with no other machine and no word."""

    def test_a_page_says_why_the_machines_joined_do_not_read(self) -> None:
        import tempfile

        said = "peers.broken in machine.toml is no machine's name; delete the line"

        class Peers:
            trouble: str | None = None

            def states(self) -> list:
                self.trouble = said
                return []

        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / ".lem" / "state").mkdir(parents=True)
            handler = serve.Handler.__new__(serve.Handler)
            handler.headers = email.message.Message()
            handler.client_address = ("127.0.0.1", 0)
            handler.machine = serve.Machine()
            handler.peers = cast("serve.lem_peers.Peers", Peers())
            with mock.patch.object(
                serve.lem_state, "workspaces", return_value=[folder]
            ):
                workspace = handler.machine.workspaces()[0]
                ctx = handler.context(workspace, "")
        self.assertTrue(any(said in problem for problem in ctx.problems))

    def test_a_page_another_machine_passed_shows_no_reason_kept_from_before(
        self,
    ) -> None:
        import tempfile

        # the reason a direct request kept, before the owner repaired the table
        said = "peers.broken in machine.toml is no machine's name; delete the line"

        class Peers:
            trouble: str | None = said

            def states(self) -> list:
                raise AssertionError("a passed request looks at no [peers] table")

        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / ".lem" / "state").mkdir(parents=True)
            handler = serve.Handler.__new__(serve.Handler)
            handler.headers = email.message.Message()
            handler.headers[serve.lem_peers.HOP] = "other-mac"
            handler.client_address = ("127.0.0.1", 0)
            handler.machine = serve.Machine()
            handler.peers = cast("serve.lem_peers.Peers", Peers())
            with mock.patch.object(
                serve.lem_state, "workspaces", return_value=[folder]
            ):
                workspace = handler.machine.workspaces()[0]
                ctx = handler.context(workspace, "")
        self.assertFalse(any(said in problem for problem in ctx.problems))


def nested(depth: int) -> str:
    """A JSON list nested DEPTH levels deep."""
    return "[" * depth + "]" * depth


class DeepBody(unittest.TestCase):
    """A request's JSON nested as deep as the interpreter's recursion limit: under 3.11
    the decode raises RecursionError, from 3.12 a walk of it can. Each reader answers
    with an HTTP status, and a card's answer is refused as no JSON before the act."""

    def setUp(self) -> None:
        import io
        import tempfile

        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        (Path(folder.name) / ".lem" / "state").mkdir(parents=True)
        self.handler = serve.Handler.__new__(serve.Handler)
        self.handler.door = None
        self.handler.client_address = ("127.0.0.1", 0)
        self.handler.machine = serve.Machine()
        self.sent: list[tuple[int, dict]] = []
        self.acted: list[str] = []

        def send(status: int, data: bytes, kind: str, **_: object) -> None:
            self.sent.append((status, json.loads(data or b"{}")))

        self.io = io
        for where, name, value in (
            (self.handler, "send", send),
            (self.handler, "listen_port", lambda: 0),
            (serve, "action_refusal", lambda *_: None),
            (serve, "act_card", lambda *_: self.acted.append("card") or (200, "x")),
            (serve, "agterm_act", lambda *_: self.acted.append("agterm") or "typed"),
        ):
            patched = mock.patch.object(where, name, value)
            patched.start()
            self.addCleanup(patched.stop)
        listed = mock.patch.object(
            serve.lem_state, "workspaces", return_value=[folder.name]
        )
        listed.start()
        self.addCleanup(listed.stop)
        self.name = self.handler.machine.workspaces()[0].name

    def post(self, body: str) -> None:
        data = body.encode("utf-8")
        self.handler.headers = email.message.Message()
        self.handler.headers["Content-Length"] = str(len(data))
        self.handler.rfile = self.io.BytesIO(data)

    def test_a_cards_answer_nested_past_the_limit_is_refused_as_no_json(self) -> None:
        deep = nested(sys.getrecursionlimit())
        self.post(
            '{"status": "answered", "answers": {"answer": '
            f'{{"selected": [], "extra": {deep}}}}}}}'
        )
        self.handler.card_answer(self.name, "refund-rounding", "C-1")
        self.assertEqual([status for status, _ in self.sent], [400])
        self.assertIn("no JSON object", self.sent[0][1]["said"])
        self.assertEqual(self.acted, [])

    def test_an_act_of_agterm_and_of_the_notifications_answer_with_a_status(
        self,
    ) -> None:
        deep = f'{{"x": {nested(sys.getrecursionlimit())}}}'
        self.post(deep)
        self.handler.agterm(self.name, "type")
        self.post(deep)
        with mock.patch.object(
            serve.lem_push, "subscribe", return_value={"devices": 1}
        ):
            self.handler.push_act("subscribe")
        self.assertEqual(len(self.sent), 2)
        self.assertTrue(all(isinstance(status, int) for status, _ in self.sent))

    def test_a_cookie_nested_past_the_limit_is_no_preference(self) -> None:
        deep = nested(sys.getrecursionlimit())
        self.assertEqual(
            serve.prefs_of(f"{serve.PREFS_COOKIE}={deep}"),
            serve.prefs_of(None),
        )


class CodeStamp(unittest.TestCase):
    """The stamp `lem serve --ensure` compares with the running server's: the newest
    change time of the Python in a folder of Lem, of either layout."""

    @staticmethod
    def write(root: Path, place: str, ns: int) -> None:
        import os

        file = root / place
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text("", encoding="utf-8")
        os.utime(file, ns=(ns, ns))

    def test_an_edit_in_the_package_moves_the_stamp(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.write(root, "src/lem/serve.py", 2_000)
            self.write(root, "skills/lem/scripts/picker.py", 3_000)
            self.assertEqual(serve.code_stamp(root), 2_000)
            self.write(root, "src/lem/land.py", 5_000)
            self.assertEqual(serve.code_stamp(root), 5_000)

    def test_a_folder_of_the_old_layout_stamps_from_its_scripts(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.write(root, "skills/lem/scripts/serve.py", 4_000)
            self.write(root, "skills/lem/scripts/lem_state.py", 7_000)
            self.assertEqual(serve.code_stamp(root), 7_000)

    def test_a_newer_package_replaces_a_server_of_the_old_layout_not_back(
        self,
    ) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as old, tempfile.TemporaryDirectory() as new:
            self.write(Path(old), "skills/lem/scripts/serve.py", 4_000)
            self.write(Path(new), "src/lem/serve.py", 9_000)
            self.write(Path(new), "skills/lem/scripts/picker.py", 1_000)
            codes = {
                root: {
                    "version": f"files {serve.code_stamp(Path(root))}",
                    "stamp": serve.code_stamp(Path(root)),
                }
                for root in (old, new)
            }
            for mine, theirs, replaces in ((new, old, True), (old, new, False)):
                with (
                    mock.patch.object(
                        serve, "code_stamp", return_value=codes[mine]["stamp"]
                    ),
                    mock.patch.object(
                        serve, "code_version", return_value=codes[mine]["version"]
                    ),
                ):
                    self.assertEqual(serve.outdated(codes[theirs]), replaces)


if __name__ == "__main__":
    unittest.main()
