"""`lem session close`: log the close of a session, then close it.

    lem session close SLUG --why handoff|ended|owner [--session ID] [--when-unselected]

It puts the close on record, then closes the session, never one the owner has selected
(`app/sessions/closing.py`).
"""

import time
from typing import Literal

import click
import msgspec

from lem.app.sessions import closing, here
from lem.cli import place
from lem.cli.words import choice
from lem.kernel import clock

type Why = Literal["handoff", "ended", "owner"]

# seconds between two looks, unless the call says
EVERY = 5.0


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem session close`."""

    slug: str
    session: str | None = None
    why: Why
    when_unselected: bool = False
    every: float = EVERY


def run(call: Call) -> closing.Closed:
    """Close the task's session once nobody looks at it."""
    bound = here.bound(place.folder())
    asked = msgspec.convert(msgspec.structs.asdict(call), closing.Closing)
    return closing.close_session(bound, asked, time.sleep, clock.now)


COMMAND = click.Command(
    "close",
    params=[
        click.Argument(["slug"]),
        click.Option(
            ["--session"], help="the session to close (default: the task's newest)"
        ),
        click.Option(["--why"], required=True, type=choice(Why), help="why it closes"),
        click.Option(
            ["--when-unselected"],
            is_flag=True,
            help="wait until the owner has left the session, then close it",
        ),
        click.Option(
            ["--every"],
            type=click.FLOAT,
            default=EVERY,
            hidden=True,
            help="seconds between two looks",
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Log the close of a session, then close it.",
)
