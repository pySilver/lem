"""`lem task build`: build a planned task, by its slug or its plan file.

    lem task build SLUG|PLAN-FILE

A stub until the step `task` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem task build`."""

    target: str


def run(call: Call) -> None:
    """Refuse until the step `task` builds `lem task build`."""
    raise not_built("task build", "task")


COMMAND = click.Command(
    "build",
    params=[
        click.Argument(["target"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Build a planned task, by its slug or its plan file.",
)
