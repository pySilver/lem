"""`lem owner away`: the owner is away, for every repository on this machine.

    lem owner away [--words WORDS]

It writes the machine's mark with the owner's words as typed, unless it changes nothing, and
names this workspace's tasks his word changed (`app/owner/presence.py`).
"""

import click
import msgspec

from lem.app.owner import presence
from lem.cli import place
from lem.kernel import clock


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem owner away`."""

    words: str | None = None


def run(call: Call) -> presence.Said:
    """Mark the owner away, for every repository on this machine."""
    return presence.said(place.folder(), call.words, clock.now(), away=True)


COMMAND = click.Command(
    "away",
    params=[
        click.Option(["--words"], help="the owner's words, as typed"),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The owner is away, for every repository on this machine.",
)
