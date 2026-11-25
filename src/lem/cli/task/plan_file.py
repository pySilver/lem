"""`lem task plan-file`: the name a task's plan takes in the plans folder.

    lem task plan-file SLUG [--date DAY]

A stub until the step `task` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem task plan-file`."""

    slug: str
    date: str | None = None


def run(call: Call) -> None:
    """Refuse until the step `task` builds `lem task plan-file`."""
    raise not_built("task plan-file", "task")


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
