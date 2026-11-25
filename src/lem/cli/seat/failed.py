"""`lem seat failed`: a seat's agent gave an error: the fallback stands in.

    lem seat failed SLUG ROLE --seat SEAT --error KIND [--said LINE]

Only the reviewer, the planner and the merge agent have a fallback, and an error is one of the
four of `main`'s `state.SEAT_ERRORS`. A stub until the step `sessions` builds it: it refuses
`not-built`.
"""

from typing import Literal

import click
import msgspec

from lem.cli.stub import not_built
from lem.cli.words import choice

type Role = Literal["reviewer", "planner", "merger"]
type Error = Literal["missing", "login", "tokens", "model"]


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem seat failed`."""

    slug: str
    role: Role
    seat: str
    error: Error
    said: str | None = None


def run(call: Call) -> None:
    """Refuse until the step `sessions` builds `lem seat failed`."""
    raise not_built("seat failed", "sessions")


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
            type=choice(Error),
            help="missing, login, tokens or model",
        ),
        click.Option(["--said"], help="the agent's own line of the error"),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="A seat's agent gave an error: the fallback stands in.",
)
