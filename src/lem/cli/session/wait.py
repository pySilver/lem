"""`lem session wait`: wait for a state, an event or the task's first line.

    lem session wait SLUG (--until STATES|--event EVENT|--first-line) ...

A stub until the step `sessions` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.checks import exactly_one
from lem.cli.stub import not_built

# seconds between two looks, unless the call says
EVERY = 10.0
# seconds the wait lasts at most, unless the call says
BOUND = 600.0


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem session wait`."""

    slug: str
    until: str | None = None
    event: str | None = None
    first_line: bool = False
    companion: str | None = None
    quiet: str | None = None
    every: float = EVERY
    bound: float = BOUND


def run(call: Call) -> None:
    """Refuse until the step `sessions` builds `lem session wait`."""
    raise not_built("session wait", "sessions")


COMMAND = click.Command(
    "wait",
    params=[
        click.Argument(["slug"]),
        click.Option(
            ["--until"], help="the states that end the wait, joined by commas"
        ),
        click.Option(["--event"], help="the event that ends the wait"),
        click.Option(
            ["--first-line"], is_flag=True, help="end with the task's first line"
        ),
        click.Option(
            ["--companion"], help="end too when this companion of the session is gone"
        ),
        click.Option(
            ["--quiet"], help="end too when FILE has not changed for 45 minutes"
        ),
        click.Option(
            ["--every"],
            type=click.FLOAT,
            default=EVERY,
            hidden=True,
            help="seconds between two looks",
        ),
        click.Option(
            ["--bound"],
            type=click.FLOAT,
            default=BOUND,
            hidden=True,
            help="seconds the wait lasts at most",
        ),
    ],
    callback=lambda **given: run(
        msgspec.convert(exactly_one(given, "until", "event", "first_line"), Call)
    ),
    help="Wait for a state, an event or the task's first line.",
)
