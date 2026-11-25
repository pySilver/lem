"""`lem session stopped`: log that the task's session stopped.

    lem session stopped SLUG [--session ID]

A stub until the step `sessions` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem session stopped`."""

    slug: str
    session: str | None = None


def run(call: Call) -> None:
    """Refuse until the step `sessions` builds `lem session stopped`."""
    raise not_built("session stopped", "sessions")


COMMAND = click.Command(
    "stopped",
    params=[
        click.Argument(["slug"]),
        click.Option(["--session"], help="the session the stop is for"),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Log that the task's session stopped.",
)
