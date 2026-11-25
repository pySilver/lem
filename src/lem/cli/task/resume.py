"""`lem task resume`: bring back a parked task, or start again from a dropped one.

    lem task resume SLUG

A stub until the step `task` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem task resume`."""

    slug: str


def run(call: Call) -> None:
    """Refuse until the step `task` builds `lem task resume`."""
    raise not_built("task resume", "task")


COMMAND = click.Command(
    "resume",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Bring back a parked task, or start again from a dropped one.",
)
