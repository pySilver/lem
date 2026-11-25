"""`lem decisions list`: a task's decisions.

    lem decisions list SLUG

A stub until the step `criteria` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem decisions list`."""

    slug: str


def run(call: Call) -> None:
    """Refuse until the step `criteria` builds `lem decisions list`."""
    raise not_built("decisions list", "criteria")


COMMAND = click.Command(
    "list",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="A task's decisions.",
)
