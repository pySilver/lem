"""Close a question in the overlay of this session."""

import click
import msgspec

from lem.cli.ask import asking, card_wait, context, waiting
from lem.ports.faults import Unanswered


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem ask close`."""

    page_id: str | None = None


def run(call: Call) -> asking.Words:
    """Keep the first result, then close this session's own page."""
    here = context.here()
    if here is None:
        return asking.no_terminal()
    try:
        return close(here, call.page_id)
    except Unanswered as error:
        return {"outcome": "unavailable", "said": str(error)}


def close(here: context.Context, wanted: str | None) -> asking.Words:
    """Only close a page opened by the question command."""
    page = here.overlay.shown(wanted)
    if page is None:
        kept = None if wanted is None else card_wait.recorded(here, wanted)
        return kept or {"outcome": "gone"}
    ended = waiting.poll(here, page)
    if ended is None:
        ended = card_wait.finished(here, page, "closed", {"status": "closed"})
    here.overlay.close(page)
    return ended


COMMAND = click.Command(
    "close",
    params=[
        click.Argument(["page_id"], required=False),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Close a question page.",
)
