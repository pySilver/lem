"""A browser question's answers and its own document's pagehide."""

import re
import time
from concurrent.futures import ThreadPoolExecutor
from http.client import HTTPConnection
from typing import TYPE_CHECKING

import pytest

from lem.cli.ask import browser
from lem.cli.ask.browser_http import BrowserServer

if TYPE_CHECKING:
    from collections.abc import Callable

    from lem.cli.ask.answer import Words

HTML = b"<!doctype html><html><head></head><body></body></html>"
DISMISS = b'{"status":"dismissed"}'


def request(server: BrowserServer, method: str, path: str, body: bytes = b"") -> bytes:
    """Send one request and finish it before the next test step."""
    peer = HTTPConnection("127.0.0.1", server.server_port, timeout=3)
    try:
        peer.request(method, path, body=body, headers={"Origin": server.origin})
        response = peer.getresponse()
        assert response.status == (200 if method == "GET" else 204)
        return response.read()
    finally:
        peer.close()


def load(server: BrowserServer) -> str:
    html = request(server, "GET", server.page)
    seen = re.search(rb'<meta name="lem-ask-load" content="([0-9]+)">', html)
    assert seen
    return seen[1].decode()


@pytest.mark.parametrize("beacon_first", [False, True])
def test_a_reload_keeps_the_question_for_either_request_order(
    *, beacon_first: bool
) -> None:
    def reload(server: BrowserServer) -> None:
        previous = load(server)
        if not beacon_first:
            assert load(server) != previous
        request(server, "POST", f"{server.page}answer?load={previous}", DISMISS)
        if beacon_first:
            assert load(server) != previous
        assert server.dismissed is None
        request(server, "POST", server.page + "answer", b"[1]")

    assert completed(reload)["answers"] == {
        "answer": {"selected": [], "labels": [], "text": "[1]"}
    }


@pytest.mark.parametrize("action", ["cancel", "about:blank"])
def test_cancel_and_pagehide_still_dismiss(action: str) -> None:
    def dismiss(server: BrowserServer) -> None:
        loaded = load(server)
        query = f"?load={loaded}" if action == "about:blank" else ""
        request(server, "POST", f"{server.page}answer{query}", DISMISS)

    assert completed(dismiss) == {"outcome": "dismissed"}


def completed(visit: Callable[[BrowserServer], None]) -> Words:
    with BrowserServer(HTML) as server, ThreadPoolExecutor() as pool:
        work = pool.submit(visit, server)
        outcome = browser.wait(server, time.monotonic() + 5)
        work.result()
        return outcome
