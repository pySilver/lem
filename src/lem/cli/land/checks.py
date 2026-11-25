"""`lem land checks`: run the machine checks, or say how they run.

    lem land checks SLUG [--status|--stop]

The plain path, as the step `slice-land` built it; the step `land-checks` owns it.
"""

from typing import TYPE_CHECKING

import click
import msgspec

from lem.app.landing import checks_run
from lem.cli import place
from lem.cli.checks import at_most_one
from lem.cli.stub import not_built

if TYPE_CHECKING:
    from lem.kernel.envelope import Envelope


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem land checks`."""

    slug: str
    status: bool = False
    stop: bool = False


def run(call: Call) -> Envelope:
    """Run the checks; `--status` and `--stop` are the step `land-checks`'s."""
    if call.status or call.stop:
        raise not_built("land checks --status|--stop", "land-checks")
    return checks_run.run(place.folder(), call.slug)


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
