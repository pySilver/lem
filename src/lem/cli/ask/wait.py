"""Read the answer to a question whose page is open."""

import click
import msgspec

from lem.cli.ask import asking, context, preferences, waiting
from lem.cli.ask.shown import Shown, options


class Call(Shown, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem ask wait`."""

    page_id: str


def run(call: Call) -> asking.Words:
    """Resume the wait, even when the board already took the answer."""
    here = context.here()
    if here is None:
        return asking.no_terminal()
    return waiting.wait(here, call.page_id, call, preferences.defaults())


COMMAND = click.Command(
    "wait",
    params=[
        click.Argument(["page_id"]),
        *options(),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Wait for the answer of a page opened with --no-wait.",
)
