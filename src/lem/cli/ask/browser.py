"""A question in the owner's browser, on a private loopback address."""

import time
import webbrowser
from typing import TYPE_CHECKING

from lem.cli.ask import html as document
from lem.cli.ask.browser_http import BrowserServer

if TYPE_CHECKING:
    from pathlib import Path

    from lem.cli.ask.answer import Words
    from lem.cli.ask.shown import Shown
    from lem.cli.ask.spec import Spec

RELOAD_GRACE = 1.0  # time for a new load after pagehide, as on main
POLL = 0.25
OUTCOME = "outcome"


def question(spec: Spec, base: Path, call: Shown) -> Words:
    """Wait on the browser for this call's lifetime."""
    if call.no_wait:
        return {OUTCOME: "unavailable", "hint": "--no-wait requires an agterm overlay"}
    return ask(document.build(spec, base), call.timeout)


def ask(html: bytes, timeout: float) -> Words:
    """Serve one browser question until the owner answers or the wait ends."""
    with BrowserServer(html) as server:
        if not webbrowser.open(server.address):
            return {
                OUTCOME: "unavailable",
                "said": "the owner's browser did not open",
            }
        return wait(server, time.monotonic() + timeout)


def wait(server: BrowserServer, deadline: float) -> Words:
    """A new load clears the dismissal of the old page on reload."""
    while True:
        server.timeout = max(0, min(POLL, deadline - time.monotonic()))
        server.handle_request()
        if server.answer is not None:
            return {**server.answer, OUTCOME: server.answer.get("status", "answered")}
        now = time.monotonic()
        if server.dismissed is not None and now - server.dismissed >= RELOAD_GRACE:
            return {OUTCOME: "dismissed"}
        if now >= deadline:
            return {OUTCOME: "timeout", "hint": "ask again with a longer --timeout"}
