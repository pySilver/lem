"""`lem session open`: open the task's session for its phase.

    lem session open SLUG [--why WHY] [--session ID]

It opens the task's session with no focus for the phase the task's record gives, or gives the
one that runs (`app/sessions/opening.py`). `--why stopped`, the restart of a stopped session
beside it, is the step `sessions`'s, and refuses `not-built` until then.
"""

from typing import TYPE_CHECKING, Literal

import click
import msgspec

from lem.app.sessions import here, opening
from lem.cli import place
from lem.cli.stub import not_built
from lem.cli.words import choice
from lem.kernel import clock

if TYPE_CHECKING:
    from lem.kernel.envelope import Envelope

type Why = Literal[
    "new",
    "handoff",
    "dead",
    "merged",
    "conflict",
    "refused",
    "queue",
    "night",
    "owner",
    "stopped",
]


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem session open`."""

    slug: str
    why: Why = "owner"
    session: str | None = None


def run(call: Call) -> Envelope:
    """Open the task's session, or give the one that runs."""
    if call.why == "stopped":
        raise not_built("session open --why stopped", "sessions")
    bound = here.bound(place.folder())
    made = opening.open_session(bound, call.slug, call.why, None, clock.now())
    return here.enveloped(made, opening.said(made))


COMMAND = click.Command(
    "open",
    params=[
        click.Argument(["slug"]),
        click.Option(
            ["--why"],
            type=choice(Why),
            default="owner",
            help="why it opens, for the record",
        ),
        click.Option(
            ["--session"], help="with --why stopped: the session the restart replaces"
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Open the task's session for its phase.",
)
