"""`lem session stopped`: log that the task's session stopped.

    lem session stopped SLUG [--session ID]

The guard's stop, after one more look in the task's lock (`app/sessions/guard_steps.py`).
"""

from typing import TYPE_CHECKING

import click
import msgspec

from lem.app.sessions import guard_steps, here
from lem.cli import place
from lem.kernel import clock

if TYPE_CHECKING:
    from lem.kernel.envelope import Envelope


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem session stopped`."""

    slug: str
    session: str | None = None


def run(call: Call) -> Envelope:
    """Put the stop of the task's session on record when it is due."""
    bound = here.bound(place.folder())
    acted = guard_steps.stepped(bound, call.slug, "stopped", call.session, clock.now())
    return here.enveloped(acted, acted.say)


COMMAND = click.Command(
    "stopped",
    params=[
        click.Argument(["slug"]),
        click.Option(["--session"], help="the session the stop is for"),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Log that the task's session stopped.",
)
