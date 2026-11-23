"""lem_peers.py's rules, each called in this process: a machine's name for `--join`, the loop guard, the
list of two machines' workspaces and its order, a machine that does not answer, a redirect kept inside
the peer's addresses, and the headers that pass. Two servers that pass pages and a stream through run
in tests/lem-peers.sh.

    python3 -B -m unittest discover -s tests/unit
"""

import email.message
import importlib
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
sys.path.insert(
    0, str(Path(__file__).resolve().parents[2] / "skills" / "lem" / "scripts")
)
peers = importlib.import_module("lem_peers")
pages = importlib.import_module("lem_board_pages")

SUFFIX = "tail1234.ts.net"


def headers(*pairs: tuple[str, str]) -> email.message.Message:
    message = email.message.Message()
    for name, value in pairs:
        message[name] = value
    return message


def own(name: str, waits: int = 0) -> dict:
    return {
        "name": name,
        "path": f"/src/{name}",
        "url": f"/alpha/{name}/",
        "waits": waits,
        "building": 0,
        "checks": 0,
        "running": 0,
    }


def theirs(name: str, waits: int = 0) -> dict:
    # a peer answers with its own addresses; the entry builds them again
    return {
        "name": name,
        "path": f"/work/{name}",
        "url": f"/beta/{name}/",
        "waits": waits,
        "building": 1,
        "checks": 0,
        "running": 1,
    }


class Names(unittest.TestCase):
    def test_a_name_is_one_label_and_a_full_name_of_this_tailnet_is_cut_to_it(
        self,
    ) -> None:
        self.assertEqual(peers.peer_name("Mac-Mini", SUFFIX), "mac-mini")
        self.assertEqual(peers.peer_name(f"mac-mini.{SUFFIX}.", SUFFIX), "mac-mini")
        self.assertEqual(peers.parse_join("mac-mini:4538", SUFFIX), ("mac-mini", 4538))
        self.assertEqual(peers.parse_join("mac-mini", SUFFIX), ("mac-mini", None))

    def test_another_tailnet_a_word_that_is_no_label_and_a_bad_port_are_refused(
        self,
    ) -> None:
        with self.assertRaisesRegex(peers.PeerError, "no machine of this tailnet"):
            peers.peer_name("mac-mini.other.ts.net", SUFFIX)
        with self.assertRaisesRegex(peers.PeerError, "no machine of this tailnet"):
            peers.peer_name(f"a.b.{SUFFIX}", SUFFIX)
        for bad in ("mac mini", "-mini", "mac_mini", ""):
            with self.assertRaisesRegex(peers.PeerError, "no machine's name"):
                peers.peer_name(bad, SUFFIX)
        with self.assertRaisesRegex(peers.PeerError, "no port"):
            peers.parse_join("mac-mini:99999", SUFFIX)


class Loop(unittest.TestCase):
    def test_a_request_of_another_server_is_never_forwarded_and_every_request_to_a_peer_says_so(
        self,
    ) -> None:
        self.assertTrue(peers.hopped(headers(("Lem-Hop", "1"))))
        self.assertFalse(peers.hopped(headers(("Accept", "text/html"))))
        self.assertEqual(peers.request_headers(headers())["Lem-Hop"], "1")


class List(unittest.TestCase):
    def test_two_machines_each_row_names_its_machine_and_its_address_is_built_here(
        self,
    ) -> None:
        rows = peers.merged(
            [own("lem"), own("shop", 2)],
            "alpha",
            [
                {
                    "name": "beta",
                    "reachable": True,
                    "rows": [theirs("lem", 1), {"url": "/x/"}],
                }
            ],
        )
        self.assertEqual(
            [(r["host"], r["name"], r["url"], r["waits"]) for r in rows],
            [
                ("alpha", "lem", "/alpha/lem/", 0),
                ("alpha", "shop", "/alpha/shop/", 2),
                ("beta", "lem", "/beta/lem/", 1),
            ],
        )

    def test_what_waits_comes_first_across_machines_and_a_machine_that_does_not_answer_last(
        self,
    ) -> None:
        rows = peers.merged(
            [own("lem"), own("shop", 2)],
            "alpha",
            [
                {"name": "beta", "reachable": True, "rows": [theirs("site", 5)]},
                {
                    "name": "gamma",
                    "reachable": False,
                    "answered": 1000,
                    "said": "it sleeps",
                    "rows": [theirs("old", 9)],
                },
            ],
        )
        page = pages.index_page("alpha", rows, lambda name: f"/assets/{name}")
        order = [part.split('"', 1)[0] for part in page.split('id="space-')[1:]]
        self.assertEqual(order, ["beta-site", "alpha-shop", "alpha-lem", "gamma-old"])
        self.assertIn("4 repositories on 3 machines", page)
        self.assertIn("not reachable", page)

    def test_one_machine_lists_as_it_does_with_no_peer(self) -> None:
        page = pages.index_page(
            "alpha",
            peers.merged([own("lem"), own("shop", 2)], "alpha", []),
            lambda name: f"/assets/{name}",
        )
        self.assertIn('id="space-shop"', page)
        self.assertTrue("<h2>shop</h2>" in page and "<h2>alpha/" not in page)
        self.assertIn("2 repositories on this machine", page)

    def test_a_machine_that_does_not_answer_keeps_its_last_rows_grayed_with_its_last_answer(
        self,
    ) -> None:
        rows = peers.merged(
            [],
            "alpha",
            [
                {
                    "name": "beta",
                    "reachable": False,
                    "answered": 1700000000000,
                    "said": "beta does not answer",
                    "rows": [theirs("lem", 3)],
                }
            ],
        )
        self.assertEqual(
            [(r["name"], r["reachable"], r["answered"], r["waits"]) for r in rows],
            [("lem", False, 1700000000000, None)],
        )
        never = peers.merged(
            [], "alpha", [{"name": "beta", "reachable": None, "rows": []}]
        )
        self.assertEqual(
            [(r["host"], r["name"], r["reachable"], r["said"]) for r in never],
            [("beta", "", False, "no answer yet")],
        )

    def test_a_peer_of_this_machines_own_name_is_left_out(self) -> None:
        self.assertEqual(
            [
                r["host"]
                for r in peers.merged(
                    [own("lem")],
                    "alpha",
                    [{"name": "alpha", "reachable": True, "rows": [theirs("x")]}],
                )
            ],
            ["alpha"],
        )

    def test_a_peers_page_gets_the_entrys_list_with_its_own_rows_fresh_in_their_place(
        self,
    ) -> None:
        sent = peers.merged(
            [own("lem")],
            "alpha",
            [
                {"name": "beta", "reachable": True, "rows": [theirs("site", 1)]},
                {"name": "gamma", "reachable": True, "rows": [theirs("x")]},
            ],
        )
        said = peers.request_headers(headers(), sent)["Lem-Spaces"]
        given = peers.spaces_of(said)
        mine = peers.with_own(
            given, [{**theirs("site", 4), "url": "/beta/site/"}], "beta"
        )
        self.assertEqual(
            [(r["host"], r["name"], r["waits"]) for r in mine],
            [("alpha", "lem", 0), ("beta", "site", 4), ("gamma", "x", 0)],
        )
        self.assertEqual(
            [r["url"] for r in mine], ["/alpha/lem/", "/beta/site/", "/gamma/x/"]
        )
        self.assertEqual(
            peers.with_own([], [theirs("site")], "beta")[0]["host"], "beta"
        )
        self.assertEqual(peers.spaces_of("not json"), [])


class Passing(unittest.TestCase):
    BASE = "https://beta.tail1234.ts.net:4537"

    def test_a_redirect_stays_inside_the_peers_addresses(self) -> None:
        self.assertEqual(
            peers.kept_location("/beta/shop/", "beta", self.BASE), "/beta/shop/"
        )
        self.assertEqual(
            peers.kept_location(
                f"{self.BASE}/beta/shop/backlog?read=1", "beta", self.BASE
            ),
            "/beta/shop/backlog?read=1",
        )
        self.assertEqual(
            peers.kept_location("/shop/backlog", "beta", self.BASE),
            "/beta/shop/backlog",
        )
        self.assertEqual(peers.kept_location("/", "beta", self.BASE), "/")
        self.assertIsNone(
            peers.kept_location("https://evil.example/beta/", "beta", self.BASE)
        )
        self.assertIsNone(peers.kept_location("//evil.example/x", "beta", self.BASE))

    def test_only_the_boards_own_cookie_and_the_headers_a_page_needs_pass(self) -> None:
        sent = peers.request_headers(
            headers(
                ("Cookie", "lem_board=%7B%22rail%22%3Atrue%7D; session=secret"),
                ("Turbo-Frame", "task"),
                ("Tailscale-User-Login", "owner@example.com"),
                ("Last-Event-ID", "87"),
            )
        )
        self.assertEqual(sent["Cookie"], "lem_board=%7B%22rail%22%3Atrue%7D")
        self.assertEqual((sent["Turbo-Frame"], sent["Last-Event-ID"]), ("task", "87"))
        self.assertNotIn("Tailscale-User-Login", sent)
        back = peers.reply_headers(
            [
                ("Content-Type", "text/html"),
                ("Set-Cookie", "other=1"),
                ("Set-Cookie", "lem_board=x; Path=/"),
                ("Location", "/shop/"),
                ("Server", "lem-serve"),
                ("Connection", "close"),
            ],
            "beta",
            self.BASE,
        )
        self.assertEqual(
            back,
            [
                ("Content-Type", "text/html"),
                ("Set-Cookie", "lem_board=x; Path=/"),
                ("Location", "/beta/shop/"),
            ],
        )

    def test_a_test_names_a_peers_address_and_the_server_s_name(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "LEM_SERVE_PEERS": "beta=http://127.0.0.1:4621,gamma=mac.tail1234.ts.net",
                "LEM_SERVE_NAME": "alpha",
            },
        ):
            self.assertEqual(peers.base_of("beta", 4537, None), "http://127.0.0.1:4621")
            self.assertEqual(
                peers.base_of("gamma", 4548, None), "https://mac.tail1234.ts.net:4548"
            )
            self.assertEqual(peers.test_name(), "alpha")
        with mock.patch.dict(os.environ, {"LEM_SERVE_PEERS": ""}):
            self.assertEqual(
                peers.base_of("beta", 4537, SUFFIX), "https://beta.tail1234.ts.net:4537"
            )
            with self.assertRaisesRegex(peers.PeerError, "no MagicDNS suffix"):
                peers.base_of("beta", 4537, None)


if __name__ == "__main__":
    unittest.main()
