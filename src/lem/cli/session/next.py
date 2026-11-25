"""`lem session next`: the change of phase: open the next session.

    lem session next SLUG [--same]

It opens the session of the phase the task's record now gives, after a check of `handoff.md`,
and gives the line that closes the old one once the owner has left it
(`app/sessions/handing.py`).
"""

from typing import TYPE_CHECKING

import click
import msgspec

from lem.app.sessions import handing, here
from lem.cli import place
from lem.kernel import clock

if TYPE_CHECKING:
    from lem.kernel.envelope import Envelope


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem session next`."""

    slug: str
    same: bool = False


def run(call: Call) -> Envelope:
    """Open the next session of the task."""
    bound = here.bound(place.folder())
    now = clock.now()
    made = handing.hand_on(bound, call.slug, same=call.same, now=now)
    say = (
        f"{made.task} goes on in a fresh session for the phase {made.phase}; this one "
        "closes once the owner has left it"
    )
    return here.enveloped(made, say, made.close)


COMMAND = click.Command(
    "next",
    params=[
        click.Argument(["slug"]),
        click.Option(
            ["--same"],
            is_flag=True,
            help="the owner's hand off: a fresh session for the same phase",
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The change of phase: open the next session.",
)
