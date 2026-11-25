"""`lem task plan-file`: the name a task's plan takes in the plans folder.

    lem task plan-file SLUG [--date DAY]

The name comes from `[paths] plan_file` of the team's file (`YYYY-MM-DD-<slug>.md` unless it
says otherwise), in `[paths] plans`; `found` is the plan the task has now.
"""

import click
import msgspec

from lem.app.tasks import plans
from lem.cli import place
from lem.store import places


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem task plan-file`."""

    slug: str
    date: str | None = None


def run(call: Call) -> plans.PlanFile:
    """The name of the task's plan, and the plan it has now."""
    return plans.plan_file(places.workspace(place.folder()), call.slug, call.date)


COMMAND = click.Command(
    "plan-file",
    params=[
        click.Argument(["slug"]),
        click.Option(
            ["--date"], help="the day the plan is written (default: today, in UTC)"
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The name a task's plan takes in the plans folder.",
)
