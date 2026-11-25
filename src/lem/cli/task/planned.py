"""`lem task planned`: record that the plan is committed, with its count of tasks.

    lem task planned SLUG --tasks N [--careful WHY] [--large]

The task goes from `building` to `planned`, with its plan file, the newest of the name
`lem task plan-file SLUG` gives in the task's worktree.
"""

import click
import msgspec

from lem.app.tasks import planned
from lem.cli import place
from lem.records.work import Plan
from lem.store import places


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem task planned`."""

    slug: str
    tasks: int
    careful: str | None = None
    large: bool = False


def run(call: Call) -> Plan:
    """Record the plan, and move the task to `planned`."""
    words = Plan(
        path="",
        tasks=call.tasks,
        careful=call.careful,
        large=call.large,
    )
    return planned.planned(places.workspace(place.folder()), call.slug, words)


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
