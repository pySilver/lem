"""`lem land start`: start the landing of a ready task.

    lem land start SLUG [--conflicting]

A stub until the step `land-base` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem land start`."""

    slug: str
    conflicting: bool = False


def run(call: Call) -> None:
    """Refuse until the step `land-base` builds `lem land start`."""
    raise not_built("land start", "land-base")


COMMAND = click.Command(
    "start",
    params=[
        click.Argument(["slug"]),
        click.Option(
            ["--conflicting"],
            is_flag=True,
            help="an open task the forge calls conflicting",
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Start the landing of a ready task.",
)
