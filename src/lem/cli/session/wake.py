"""`lem session wake`: a message to the task's live session, or a new session.

    lem session wake SLUG --why WHY [--head SHA] [--session ID]

It sends `lem: SLUG WHY` to the task's live session, or opens one (`app/sessions/waking.py`);
`--why status` is the guard's status message, to the live session only
(`app/sessions/guard_steps.py`).
"""

from typing import TYPE_CHECKING, Literal

import click
import msgspec

from lem.app.sessions import guard_steps, here, waking
from lem.cli import place
from lem.cli.words import choice
from lem.kernel import clock

if TYPE_CHECKING:
    from lem.kernel.envelope import Envelope

type Why = Literal["merged", "conflict", "refused", "queue", "owner", "inbox", "status"]


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem session wake`."""

    slug: str
    why: Why
    head: str | None = None
    session: str | None = None


def run(call: Call) -> Envelope:
    """Wake the task's session, or open one."""
    bound = here.bound(place.folder())
    now = clock.now()
    if call.why == "status":
        acted = guard_steps.stepped(bound, call.slug, "status", call.session, now)
        return here.enveloped(acted, acted.say)
    woken = waking.wake(bound, call.slug, call.why, call.head, now)
    return here.enveloped(woken, woken.say)


COMMAND = click.Command(
    "wake",
    params=[
        click.Argument(["slug"]),
        click.Option(["--why"], required=True, type=choice(Why), help="why it wakes"),
        click.Option(["--head"], help="the pull request's head the wake is for"),
        click.Option(
            ["--session"], help="with --why status: the session the line is for"
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="A message to the task's live session, or a new session.",
)
