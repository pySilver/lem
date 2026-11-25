"""`lem session worked`: log the turn the session took after a status message.

    lem session worked SLUG [--session ID]

A stub until the step `sessions` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem session worked`."""

    slug: str
    session: str | None = None


def run(call: Call) -> None:
    """Refuse until the step `sessions` builds `lem session worked`."""
    raise not_built("session worked", "sessions")


COMMAND = click.Command(
    "worked",
    params=[
        click.Argument(["slug"]),
        click.Option(["--session"], help="the session the turn is of"),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Log the turn the session took after a status message.",
)
