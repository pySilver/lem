"""`lem session list`: each task's newest session.

    lem session list

Each task's newest session that Lem opened, with the phase its task is in now, whether agterm
still has it, and its signs of work (`app/sessions/listing.py`).
"""

import click
import msgspec

from lem.app.sessions import here, listing
from lem.cli import place


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem session list`."""


def run(call: Call) -> tuple[listing.Listed, ...]:
    """Each task's newest session."""
    return listing.list_sessions(here.bound(place.folder()))


COMMAND = click.Command(
    "list",
    params=[],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Each task's newest session.",
)
