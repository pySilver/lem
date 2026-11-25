"""`lem land checks`: run the machine checks, or say how they run.

    lem land checks SLUG [--status|--stop]

A stub until the step `land-checks` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.checks import at_most_one
from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem land checks`."""

    slug: str
    status: bool = False
    stop: bool = False


def run(call: Call) -> None:
    """Refuse until the step `land-checks` builds `lem land checks`."""
    raise not_built("land checks", "land-checks")


COMMAND = click.Command(
    "checks",
    params=[
        click.Argument(["slug"]),
        click.Option(
            ["--status"],
            is_flag=True,
            help="whether the checks run now, and how their last run ended",
        ),
        click.Option(
            ["--stop"],
            is_flag=True,
            help="stop the checks that run now, and wait for their end",
        ),
    ],
    callback=lambda **given: run(
        msgspec.convert(at_most_one(given, "status", "stop"), Call)
    ),
    help="Run the machine checks, or say how they run.",
)
