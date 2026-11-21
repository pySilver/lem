"""serve.py's rules, each called in this process: who the tailnet door lets in, who may ask the main
listener for an act, the note of a merge that runs, the machine's names in an address, and which duty
the server owes the tasks. The routes, the stream and the start on demand run in tests/lem-serve.sh, with a server.

    python3 -B -m unittest discover -s tests/unit
"""

import email.message
import importlib
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "lem" / "scripts"))
serve = importlib.import_module("serve")
bm = importlib.import_module("lem_board_model")

OWNER = "owner@example.com"
SERVED = "mac-mini.tail1234.ts.net"
PORT = 4537


def headers(*pairs: tuple[str, str], **given: str) -> email.message.Message:
    """Request headers as the server's handler has them, each name once for each time it came; `_` in
    a keyword's name is `-`."""
    message = email.message.Message()
    for name, value in [*pairs, *((key.replace("_", "-"), value) for key, value in given.items())]:
        message[name] = value
    return message


def door(method: str = "GET", **given: str) -> str | None:
    return serve.door_refusal(headers(**given), method, OWNER, SERVED, PORT)


class Door(unittest.TestCase):
    def test_the_owners_login_for_the_macs_own_name_is_let_in(self):
        self.assertIsNone(door(Host=f"{SERVED}:{PORT}", Tailscale_User_Login=OWNER))
        self.assertIsNone(door(Host=SERVED.upper(), Tailscale_User_Login=OWNER.upper()))

    def test_another_login_and_no_login_are_refused(self):
        self.assertEqual(door(Host=SERVED, Tailscale_User_Login="guest@example.com"), serve.NOT_THE_OWNER)
        self.assertIn("carries none", door(Host=SERVED))
        self.assertEqual(serve.door_refusal(headers(("Host", SERVED), ("Tailscale-User-Login", OWNER), ("Tailscale-User-Login", OWNER)), "GET", OWNER, SERVED, PORT),
                         serve.NOT_THE_OWNER)

    def test_a_request_through_funnel_is_refused_whatever_its_login(self):
        self.assertIn("Funnel", door(Host=SERVED, Tailscale_User_Login=OWNER, Tailscale_Funnel_Request="?1"))

    def test_another_host_name_is_refused(self):
        self.assertIn("not the board's name", door(Host="evil.example.com", Tailscale_User_Login=OWNER))
        self.assertIn("not the board's name", door(Host=f"{SERVED}:443", Tailscale_User_Login=OWNER))

    def test_a_post_from_another_site_is_refused_and_one_from_the_board_is_let_in(self):
        own = f"https://{SERVED}:{PORT}"
        self.assertIsNone(door("POST", Host=SERVED, Tailscale_User_Login=OWNER, Origin=own, Sec_Fetch_Site="same-origin"))
        self.assertIn("another site", door("POST", Host=SERVED, Tailscale_User_Login=OWNER, Origin=own, Sec_Fetch_Site="cross-site"))
        self.assertIn("another origin", door("POST", Host=SERVED, Tailscale_User_Login=OWNER, Origin="https://evil.example.com"))


class Actions(unittest.TestCase):
    """The main listener's acts (of agterm, of the board on a task): only a page of the board on this Mac asks them."""

    def refusal(self, client: str = "127.0.0.1", **given: str) -> str | None:
        return serve.action_refusal(client, headers(**given), 4536)

    def test_the_boards_own_page_on_this_mac_is_let_in(self):
        self.assertIsNone(self.refusal(Host="127.0.0.1:4536", Origin="http://127.0.0.1:4536", Sec_Fetch_Site="same-origin"))
        self.assertIsNone(self.refusal("::1", Host="localhost:4536", Origin="http://localhost:4536"))

    def test_another_machine_another_site_and_a_name_that_points_here_are_refused(self):
        self.assertIn("on this Mac", self.refusal("100.64.0.2", Host="127.0.0.1:4536", Origin="http://127.0.0.1:4536"))
        self.assertIn("another site", self.refusal(Host="127.0.0.1:4536", Origin="http://127.0.0.1:4536", Sec_Fetch_Site="cross-site"))
        self.assertIn("another origin", self.refusal(Host="127.0.0.1:4536", Origin="http://evil.example.com"))
        self.assertIn("or none", self.refusal(Host="127.0.0.1:4536"))
        # a name of another site that resolves to 127.0.0.1 carries that name in Host
        self.assertIn("not the board's own", self.refusal(Host="evil.example.com:4536", Origin="http://evil.example.com:4536"))


class Reads(unittest.TestCase):
    """The main listener reads a request only for a `Host` of its own: a name of another site that points
    at this machine (DNS rebinding) reads nothing."""

    def test_its_own_names_are_read_and_another_is_refused(self):
        for host in ("127.0.0.1:4536", "localhost:4536", "[::1]:4536", "127.0.0.1", "LOCALHOST:4536"):
            self.assertIsNone(serve.host_refusal(headers(Host=host), 4536), host)
        for given in (headers(Host="evil.example.com:4536"), headers(), headers(("Host", "127.0.0.1:4536"), ("Host", "evil.example.com"))):
            self.assertIn("not the board's own", serve.host_refusal(given, 4536))
        self.assertIsNone(serve.host_refusal(headers(Host="10.0.0.5:4536"), 4536, "10.0.0.5"))
        self.assertIsNotNone(serve.host_refusal(headers(Host="10.0.0.5:4536"), 4536))


class Notes(unittest.TestCase):
    def test_a_second_press_of_a_merge_that_runs_gets_the_first_ones_note(self):
        notes = serve.Notes()
        first, new = notes.start_merge(("shop", "gift-note"), task="gift-note", state="running", said="merging")
        again, second = notes.start_merge(("shop", "gift-note"), task="gift-note", state="running", said="merging")
        self.assertEqual((again, new, second, notes.running("shop")), (first, True, False, {"gift-note"}))
        notes.change(first, state="done", said="merged")
        self.assertEqual((notes.get(first)["state"], notes.get("no-such-token")), ("done", None))


class Names(unittest.TestCase):
    def test_the_tailnet_name_is_the_address_and_the_host_name_its_alias(self):
        self.assertEqual(serve.names_of("MacBook-Pro-SLVR.tail1234.ts.net"), ("macbook-pro-slvr", (serve.SHORT_NAME,)))

    def test_with_no_tailnet_the_short_host_name_alone(self):
        self.assertEqual(serve.names_of(None), (serve.SHORT_NAME, ()))
        self.assertEqual(serve.names_of(f"{serve.SHORT_NAME}.tail1234.ts.net"), (serve.SHORT_NAME, ()))

    def test_a_name_is_a_word_of_an_address(self):
        self.assertEqual(serve.host_word("Mac mini (Office)"), "mac-mini-office")


class Duties(unittest.TestCase):
    """What the server owes the tasks, read from the files and the forge's last look alone."""

    PR = "pull request https://github.com/acme/shop/pull/41"

    @staticmethod
    def ev(minute: float, event: str, task: str = "gift-note", **fields) -> dict:
        return {"ts": f"2026-11-20T09:{minute:02d}:00Z", "event": event, "task": task, **fields}

    def state(self, minute: float, status: str, text: str, *lines: str, task: str = "gift-note") -> dict:
        return self.ev(minute, "task.state", task, status=status, text=text, lines=list(lines))

    def model(self, *events: dict, sessions=None, demo: bool = False):
        m = bm.derive(list(events), [], 1_800_000_000_000, meta={"demo": True} if demo else {})
        m.sessions = sessions
        return m

    def test_a_merge_wakes_the_tasks_session_once_while_its_worktree_stays(self):
        merged = (self.state(0, "open", self.PR), self.state(5, "landed", "main: pull request https://github.com/acme/shop/pull/41 is merged"))
        self.assertEqual(serve.duties(self.model(*merged), {}, {"gift-note"}), [("wake", "gift-note", "merged")])
        self.assertEqual(serve.duties(self.model(*merged), {}, set()), [])
        woken = (*merged, self.ev(6, "session.wake", session="S1", why="merged"))
        self.assertEqual(serve.duties(self.model(*woken), {}, {"gift-note"}), [])
        closed = (self.state(0, "open", self.PR), self.state(5, "dropped", "the pull request was closed on the forge", "pull request ... is closed"))
        self.assertEqual(serve.duties(self.model(*closed), {}, {"gift-note"}), [("wake", "gift-note", "merged")])
        by_word = (self.state(0, "building", "task 1 of 2"), self.state(5, "dropped", "the owner dropped it"))
        self.assertEqual(serve.duties(self.model(*by_word), {}, {"gift-note"}), [])

    def test_a_conflict_wakes_the_session_once_for_each_head(self):
        events = (self.ev(0, "proposed", green=True, not_green=[], tip="abc123456"), self.state(1, "open", self.PR))
        seen = {"gift-note": {"mergeable": "CONFLICTING", "head": "abc123456789"}}
        self.assertEqual(serve.duties(self.model(*events), seen, set()), [("wake", "gift-note", "conflict")])
        self.assertEqual(serve.duties(self.model(*events), {"gift-note": {"mergeable": "MERGEABLE", "head": "abc123456789"}}, set()), [])
        self.assertEqual(serve.duties(self.model(*events), {"gift-note": {"mergeable": "CONFLICTING", "head": "fff000"}}, set()), [])
        woken = (*events, self.ev(2, "session.wake", session="S1", why="conflict"))
        self.assertEqual(serve.duties(self.model(*woken), seen, set()), [])
        again = (*woken, self.ev(3, "proposed", green=True, not_green=[], tip="def456789"), self.state(4, "open", self.PR))
        self.assertEqual(serve.duties(self.model(*again), {"gift-note": {"mergeable": "CONFLICTING", "head": "def456789aaa"}}, set()), [("wake", "gift-note", "conflict")])

    def test_a_queued_task_gets_its_session_when_its_task_ended(self):
        landed = (self.state(0, "landed", "main: pull request ... is merged", task="coupon"),)
        queued = (self.state(1, "queued", "it starts after coupon", "after: coupon"),)
        self.assertEqual(serve.duties(self.model(*landed, *queued, sessions={}), {}, set()), [("open", "gift-note", "queue")])
        self.assertEqual(serve.duties(self.model(*landed, *queued, sessions=None), {}, set()), [])
        self.assertEqual(serve.duties(self.model(*landed, *queued, sessions={"gift-note": {"live": True, "agent": True}}), {}, set()), [])
        opened = (*landed, *queued, self.ev(2, "session.open", session="S2", why="queue"))
        self.assertEqual(serve.duties(self.model(*opened, sessions={}), {}, set()), [])
        waiting = (self.state(0, "open", self.PR, task="coupon"), *queued)
        self.assertEqual(serve.duties(self.model(*waiting, sessions={}), {}, set()), [])

    def test_the_merge_agents_merge_of_the_proposed_tip_is_the_servers(self):
        proposed = (self.ev(0, "proposed", green=True, not_green=[], tip="abc123456"), self.state(1, "open", self.PR))
        merge = (*proposed, self.ev(2, "merge.review", verdict="merge", calls=False, by="claude/opus:high", tip="abc123456"))
        self.assertEqual(serve.duties(self.model(*merge), {}, set()), [("merge", "gift-note", "merger")])
        # one that runs in this process is not started twice
        self.assertEqual(serve.duties(self.model(*merge), {}, set(), {"gift-note"}), [])
        call = (*proposed, self.ev(2, "merge.review", verdict="call", calls=True, by="claude/opus:high", tip="abc123456"))
        self.assertEqual(serve.duties(self.model(*call), {}, set()), [])
        overruled = (*proposed, self.ev(2, "merge.review", verdict="merge", calls=True, by="claude/opus:high", tip="abc123456"))
        self.assertEqual(serve.duties(self.model(*overruled), {}, set()), [])
        other_tip = (*proposed, self.ev(2, "merge.review", verdict="merge", calls=False, by="claude/opus:high", tip="fff000111"))
        self.assertEqual(serve.duties(self.model(*other_tip), {}, set()), [])
        # a refused try is not tried again on that tip, and the task's session is woken once for it
        refused = (*merge, self.ev(3, "merge.refused", by="merger", via="server", said="main moved after the checks ran", tip="abc123456"))
        self.assertEqual(serve.duties(self.model(*refused), {}, set()), [("wake", "gift-note", "refused")])
        self.assertEqual(serve.duties(self.model(*refused, self.ev(4, "session.wake", session="S1", why="refused")), {}, set()), [])
        # a new proposal and its new review make a new try
        again = (*refused, self.ev(5, "proposed", green=True, not_green=[], tip="def456789"), self.state(6, "open", self.PR),
                 self.ev(7, "merge.review", verdict="merge", calls=False, by="claude/opus:high", tip="def456789"))
        self.assertEqual(serve.duties(self.model(*again), {}, set()), [("merge", "gift-note", "merger")])
        merged = (*merge, self.state(3, "landed", "main: pull request https://github.com/acme/shop/pull/41 is merged"))
        self.assertEqual(serve.duties(self.model(*merged), {}, set()), [])
        self.assertEqual(serve.duties(self.model(*merge, demo=True), {}, set()), [])

    def test_after_a_moved_base_the_session_lands_it_again_and_the_server_merges_the_new_tip(self):
        proposed = (self.ev(0, "proposed", green=True, not_green=[], tip="abc123456"), self.state(1, "open", self.PR))
        # the owner's merge from the board met a moved base: Lem kept it, and the task's session is woken once
        base = (*proposed, self.ev(2, "merge.refused", by="owner", via="server", kind="base", said="origin/main moved after the checks ran", tip="abc123456", **{"from": "lem"}))
        self.assertEqual(serve.duties(self.model(*base), {}, set()), [("wake", "gift-note", "refused")])
        self.assertEqual(serve.duties(self.model(*base, self.ev(3, "session.wake", session="S1", why="refused")), {}, set()), [])
        # GitHub's refusal of his merge is his to read, and wakes nobody
        github = (*proposed, self.ev(2, "merge.refused", by="owner", via="server", said="Required status check is expected", tip="abc123456", **{"from": "github"}))
        self.assertEqual(serve.duties(self.model(*github), {}, set()), [])
        # the new landing's proposal carried the merge agent's review, and his merge stands for its tip
        again = (*base, self.ev(4, "proposed", green=True, not_green=[], tip="def456789"), self.state(5, "open", self.PR))
        carried = self.ev(6, "merge.review", verdict="merge", calls=False, by="claude/opus:high", tip="def456789", carried="abc123456")
        self.assertEqual(serve.duties(self.model(*again, carried), {}, set()), [("merge", "gift-note", "merger")])
        stands = self.ev(7, "merge.stands", by="owner", tip="def456789", **{"from": "abc123456"})
        self.assertEqual(serve.duties(self.model(*again, carried, stands), {}, set()), [("merge", "gift-note", "owner")])
        self.assertEqual(serve.duties(self.model(*again, stands), {}, set(), {"gift-note"}), [])
        conflicting = {"gift-note": {"mergeable": "CONFLICTING", "head": "def456789aaa"}}
        self.assertEqual(serve.duties(self.model(*again, stands, self.ev(8, "session.wake", session="S1", why="conflict")), conflicting, set()), [])
        self.assertEqual(serve.merge_args({"history": "squash", "title": "fix: x"}, "gift-note", "owner", True),
                         ["merge", "gift-note", "--by", "owner", "--via", "server", "--standing", "--message", "fix: x"])

    def test_a_failed_bookkeeping_of_a_merged_pull_request_is_tried_again(self):
        key = ("gift-note", 41)
        self.assertTrue(serve.merged_due(key, set(), {}, 1000.0))
        self.assertFalse(serve.merged_due(key, {key}, {}, 1000.0))
        failed = {key: (1000.0, "`lem land merged gift-note` failed")}
        self.assertFalse(serve.merged_due(key, set(), failed, 1000.0 + serve.DUTY_RETRY - 1))
        self.assertTrue(serve.merged_due(key, set(), failed, 1000.0 + serve.DUTY_RETRY))

    def test_a_demo_workspace_owes_nothing(self):
        merged = (self.state(0, "landed", "main: pull request ... is merged"),)
        self.assertEqual(serve.duties(self.model(*merged, demo=True), {}, {"gift-note"}), [])

    def test_the_list_of_sessions_reads_by_task(self):
        listed = serve.session_entries('[{"task": "gift-note", "session": "S1", "live": true, "agent": false, "unanswered": false, "phase": "build"}]')
        self.assertEqual(listed, {"gift-note": {"live": True, "agent": False, "unanswered": False, "session": "S1", "name": None}})
        self.assertEqual(serve.session_entries('{"sessions": []}'), {})
        with self.assertRaises(ValueError):
            serve.session_entries('{"said": "no"}')



class Look(unittest.TestCase):
    """`bin/lem`'s look for the server: its pid file, and whether that process lives."""

    def test_a_server_lives_only_where_its_pid_file_names_a_live_process(self):
        import importlib.machinery
        import importlib.util
        import os
        import subprocess
        import tempfile
        path = Path(__file__).resolve().parents[2] / "bin" / "lem"
        loader = importlib.machinery.SourceFileLoader("lem_command", str(path))
        command = importlib.util.module_from_spec(importlib.util.spec_from_loader("lem_command", loader))
        loader.exec_module(command)
        with tempfile.TemporaryDirectory() as folder:
            self.assertFalse(command.server_lives(folder), "no pid file")
            pid_file = Path(folder) / command.PID_FILE
            pid_file.write_text(f"{os.getpid()} 4536\n")
            self.assertTrue(command.server_lives(folder))
            ended = subprocess.run([sys.executable, "-c", "import os; print(os.getpid())"], capture_output=True, text=True, check=True)
            pid_file.write_text(f"{ended.stdout.strip()} 4536\n")
            self.assertFalse(command.server_lives(folder), "a process that ended")
            pid_file.write_text("0 4536\n")
            self.assertFalse(command.server_lives(folder), "0 names a process group")


if __name__ == "__main__":
    unittest.main()
