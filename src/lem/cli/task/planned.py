"""`lem task planned`: record that the plan is committed, with its count of tasks.

    lem task planned SLUG --tasks N [--careful WHY] [--large]

A stub until the step `task` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem task planned`."""

    slug: str
    tasks: int
    careful: str | None = None
    large: bool = False


def run(call: Call) -> None:
    """Refuse until the step `task` builds `lem task planned`."""
    raise not_built("task planned", "task")


COMMAND = click.Command(
    "planned",
    params=[
        click.Argument(["slug"]),
        click.Option(
            ["--tasks"],
            required=True,
            type=click.INT,
            help="the number of tasks the plan holds",
        ),
        click.Option(["--careful"], help="why the change needs care"),
        click.Option(["--large"], is_flag=True, help="the plan is large"),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Record that the plan is committed, with its count of tasks.",
)
