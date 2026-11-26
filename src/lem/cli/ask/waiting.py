"""Wait for an overlay outcome or for the card's answer on the board."""

import math
import time
from typing import TYPE_CHECKING

from lem.app.asking import keys
from lem.app.asking.overlay_read import PageRefused
from lem.cli.ask import answer, card_wait, glyph, temp_pages
from lem.cli.ask.spec import invalid
from lem.ports.faults import Unanswered

if TYPE_CHECKING:
    from collections.abc import Iterator

    from lem.cli.ask.context import Context
    from lem.cli.ask.shown import Shown
    from lem.settings.shared import Ask

POLL = 0.4  # the overlay read interval on main
UNREADABLE_LIMIT = 5  # consecutive unreadable replies, as on main


def check_time(timeout: float) -> None:
    """A wait's limit must make a finite deadline."""
    if not math.isfinite(timeout) or timeout < 0:
        raise invalid("timeout needs a finite number of seconds, zero or more")


def wait(here: Context, page: str, call: Shown, pref: Ask) -> answer.Words:
    """Wait until it ends or the deadline arrives. A pending card stays open."""
    keys.checked(page)
    check_time(call.timeout)
    asking = None if call.no_status else pref.status.get("asking", temp_pages.ASKING)
    temp_pages.remember(page, asking)
    if call.no_status:
        return until(here, page, call.timeout)
    return marked_wait(here, page, call.timeout, pref)


def marked_wait(here: Context, page: str, timeout: float, pref: Ask) -> answer.Words:
    """Set the sidebar's mark while the owner has a question."""
    asking = pref.status.get("asking", temp_pages.ASKING)
    glyph.set_mark(here.overlay, asking)
    answered = pref.status.get("answered", ("active",))
    try:
        printed = until(here, page, timeout)
    except BaseException:
        glyph.set_mark(here.overlay, answered)
        raise
    what = (
        (*asking, "--auto-reset") if printed.get("outcome") == "pending" else answered
    )
    glyph.set_mark(here.overlay, what)
    return printed


def until(here: Context, page: str, timeout: float) -> answer.Words:
    """Poll the two places, with the task's first answer as the record."""
    deadline = time.monotonic() + timeout
    try:
        for found in polling(here, page):
            if found is not None:
                return found
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                hint = f"run lem ask wait {page}"
                return {"outcome": "pending", "pageID": page, "hint": hint}
            time.sleep(min(POLL, remaining))
    except PageRefused as error:
        return unavailable(page, error)
    raise AssertionError("the overlay poll did not return an outcome")


def polling(here: Context, page: str) -> Iterator[answer.Words | None]:
    """Read the card, with a limit on consecutive failed reads."""
    unreadable = 0
    while True:
        try:
            found = poll(here, page)
        except Unanswered as error:
            unreadable += 1
            if unreadable >= UNREADABLE_LIMIT:
                yield unavailable(page, error)
                return
            yield None
        else:
            unreadable = 0
            yield found


def poll(here: Context, page: str) -> answer.Words | None:
    """Read one turn of a wait, taking an end from either surface."""
    kept = card_wait.recorded(here, page)
    if kept is not None:
        if kept.get("from") == "board":
            card_wait.after_board(here, page, kept)
        return kept
    told = here.overlay.outcome(page)
    if told.kind == "submitted":
        return card_wait.finished(
            here, page, "answered", answer.submitted(told.payload)
        )
    if told.kind == "dismissed":
        return card_wait.finished(here, page, "dismissed", {"status": "dismissed"})
    return None


def unavailable(page: str, error: Unanswered | PageRefused) -> answer.Words:
    """Tell the caller why agterm could not give the page's outcome."""
    return {"outcome": "unavailable", "pageID": page, "said": str(error)}
