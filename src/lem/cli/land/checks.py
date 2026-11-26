"""`lem land checks`: run the machine checks, or say how they run.

    lem land checks SLUG [--status|--stop|--repair-limit]

The run is the repository's own commands in the task's worktree, under the task's step lock;
`--status` and `--stop` look at the lock and never take it. The step `land-checks` owns it.
"""

from typing import TYPE_CHECKING

import click
import msgspec

from lem.app.landing import checks_repair, checks_step, checks_watch
from lem.cli import place
from lem.cli.checks import at_most_one

if TYPE_CHECKING:
    from lem.kernel.envelope import Envelope


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem land checks`."""

    slug: str
    status: bool = False
    stop: bool = False
    repair_limit: bool = False


def run(call: Call) -> Envelope | checks_watch.Status | checks_watch.Stopped:
    """Run the checks, say how they run, or stop them."""
    if call.status:
        return checks_watch.status(place.folder(), call.slug)
    if call.stop:
        return checks_watch.stop(place.folder(), call.slug)
    if call.repair_limit:
        return checks_repair.run(place.folder(), call.slug)
    return checks_step.run(place.folder(), call.slug)


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
        click.Option(
            ["--repair-limit"],
            is_flag=True,
            help="hold the landing for the owner after two builders could not repair a failure",
        ),
    ],
    callback=lambda **given: run(
        msgspec.convert(at_most_one(given, "status", "stop", "repair_limit"), Call)
    ),
    help="Run the machine checks, or say how they run.",
)
