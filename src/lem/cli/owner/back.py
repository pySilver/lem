"""`lem owner back`: the owner is back, for every repository on this machine.

    lem owner back [--words WORDS]

It writes the machine's mark with the owner's words as typed, unless it changes nothing, and
names this workspace's tasks his word changed (`app/owner/presence.py`).
"""

import click
import msgspec

from lem.app.owner import presence
from lem.cli import place
from lem.kernel import clock


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem owner back`."""

    words: str | None = None


def run(call: Call) -> presence.Said:
    """Mark the owner back, for every repository on this machine."""
    return presence.said(place.folder(), call.words, clock.now(), away=False)


COMMAND = click.Command(
    "back",
    params=[
        click.Option(["--words"], help="the owner's words, as typed"),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The owner is back, for every repository on this machine.",
)
