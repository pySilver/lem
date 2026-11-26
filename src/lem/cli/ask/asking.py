"""Show a question to the owner and return its outcome."""

import os
import sys
from typing import TYPE_CHECKING

from lem.app.asking import form, saved
from lem.cli.ask import browser, context, glyph, html, preferences, temp_pages, waiting
from lem.cli.ask.spec import check
from lem.kernel import errors
from lem.ports.faults import Unanswered

OUTCOME = "outcome"
HINT = "hint"

if TYPE_CHECKING:
    from pathlib import Path

    from lem.cli.ask.answer import Words
    from lem.cli.ask.shown import Shown
    from lem.cli.ask.spec import Spec


def ask(spec: Spec, base: Path, call: Shown) -> Words:
    """Use the owner's requested surface, or name the reason a page cannot open."""
    check(spec)
    if os.environ.get("CLAUDE_CODE_SESSION_ATTENDED") == "0":
        return {OUTCOME: "unattended", HINT: "the owner is away from this session"}
    pref = preferences.defaults()
    preferences.apply(spec, pref, call)
    waiting.check_time(call.timeout)
    here = context.here()
    if call.browser or (here is None and pref.browser):
        return browser.question(spec, base, call)
    if here is None:
        return no_terminal()
    return in_overlay(spec, base, call, here, pref)


def in_overlay(
    spec: Spec, base: Path, call: Shown, here: context.Context, pref: preferences.Ask
) -> Words:
    """Open this session's question and let it wait on both surfaces."""
    display = preferences.display(spec, pref, call)
    body = html.assemble(spec, base)
    path = temp_pages.page_file(body, quiet=call.no_status)
    try:
        opened = here.overlay.opening(path, display)
    except Unanswered as error:
        path.unlink(missing_ok=True)
        return {OUTCOME: "unavailable", "said": str(error)}
    if opened.busy or opened.page is None:
        path.unlink(missing_ok=True)
        return busy(opened.page)
    return opened_page(spec, call, here, pref, (opened.page, path))


def opened_page(
    spec: Spec,
    call: Shown,
    here: context.Context,
    pref: preferences.Ask,
    opened: tuple[str, Path],
) -> Words:
    """Record the card before its question waits for the owner."""
    page, path = opened
    if here.task is not None:
        try:
            saved.keep(
                here.task,
                form.metadata(spec, page, here.overlay.session),
                path.read_bytes(),
            )
        except (OSError, errors.Fault, errors.Refusal) as error:
            sys.stderr.write(f"lem ask: the board does not show card {page}: {error}\n")
            here = context.Context(overlay=here.overlay, task=None)
    words = (
        left_open(here, call, pref, page, path)
        if call.no_wait
        else waiting.wait(here, page, call, pref)
    )
    return context.with_board_notice(here, page, words)


def left_open(
    here: context.Context, call: Shown, pref: preferences.Ask, page: str, path: Path
) -> Words:
    """Name the displayed page and leave its question mark."""
    temp_pages.remember(page, status=not call.no_status)
    if not call.no_status:
        asking = pref.status.get("asking", ("blocked",))
        glyph.set_mark(here.overlay, (*asking, "--auto-reset"))
    return {OUTCOME: "open", "pageID": page, "file": str(path)}


def busy(page: str | None) -> Words:
    """The overlay slot is taken. Name the existing page only if it is ours."""
    if page is not None:
        return {OUTCOME: "busy", "pageID": page, HINT: f"run lem ask wait {page}"}
    return {
        OUTCOME: "busy",
        HINT: "ask the owner in the session; another overlay is open",
    }


def no_terminal() -> Words:
    """The ordinary conversation is available outside agterm."""
    return {
        OUTCOME: "no-agterm",
        HINT: "ask in the session or use lem ask ask SPEC --browser",
    }
