"""`lem session open`: open the task's session for its phase.

    lem session open SLUG [--why WHY] [--session ID]

It opens the task's session with no focus for the phase the task's record gives, or gives the
one that runs (`app/sessions/opening.py`). With `--why new` it names the wait for the task's
first line, which the caller runs in the background. `--why stopped` is the guard's restart
beside a stopped session, or the owner's open over a logged stop (`app/sessions/guard_steps.py`).
"""

from typing import TYPE_CHECKING, Literal

import click
import msgspec

from lem.app.sessions import guard_steps, here, opening
from lem.cli import place
from lem.cli.words import choice
from lem.kernel import clock
from lem.kernel.errors import Refusal

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
    if call.session is not None and call.why != "stopped":
        raise Refusal(
            "session-option",
            "--session goes with open --why stopped and wake --why status, the steps of the "
            "guard of a stopped session",
            f"leave --session out: {call.why} takes the task's newest session",
        )
    bound = here.bound(place.folder())
    if call.why == "stopped":
        acted = guard_steps.stepped(
            bound, call.slug, "restart", call.session, clock.now()
        )
        return here.enveloped(acted, acted.say)
    made = opening.open_session(bound, call.slug, call.why, None, clock.now())
    waits = call.why == "new" and not made.already
    then = f"lem session wait {call.slug} --first-line" if waits else None
    return here.enveloped(made, made.said(), then)


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
