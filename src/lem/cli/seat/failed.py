"""`lem seat failed`: a seat's agent gave an error: the fallback stands in.

    lem seat failed SLUG ROLE --seat SEAT --error KIND [--said LINE]

Only the reviewer, the planner and the merge agent have a fallback.
The fallback stands in from then on, or the task is blocked with the seat named
(`app/sessions/seats.py`).
"""

from typing import Literal

import click
import msgspec

from lem.app.sessions import here, seat_lines, seats
from lem.cli import place
from lem.cli.words import choice
from lem.kernel import clock
from lem.kernel.errors import Refusal
from lem.records.work import SeatError, StandIn

type Role = Literal["reviewer", "planner", "merger"]


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem seat failed`."""

    slug: str
    role: Role
    seat: str
    error: SeatError
    said: str | None = None


def run(call: Call) -> seat_lines.Decision:
    """The fallback stands in, or the task is blocked."""
    said = call.said
    if said is not None and (not said.strip() or "\n" in said):
        raise Refusal(
            "said",
            "--said is the agent's own line of the error, one line of text",
            "give its line again, or leave --said out",
        )
    failure = StandIn(
        seat=call.role,
        failed=call.seat,
        error=call.error,
        said=said.strip() if said else None,
        at=clock.now(),
    )
    return seats.failed(here.bound(place.folder()), call.slug, failure)


COMMAND = click.Command(
    "failed",
    params=[
        click.Argument(["slug"]),
        click.Argument(["role"], type=choice(Role)),
        click.Option(
            ["--seat"],
            required=True,
            help="the seat the stage opened, as `lem seat show` printed it",
        ),
        click.Option(
            ["--error"],
            required=True,
            type=choice(SeatError),
            help="missing, login, tokens, usage-limit or model",
        ),
        click.Option(["--said"], help="the agent's own line of the error"),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="A seat's agent gave an error: the fallback stands in.",
)
