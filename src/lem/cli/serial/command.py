"""`lem serial`: run one command under the repository's one serial lock.

    lem serial -- COMMAND...

A stub until the step `land-checks` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem serial`."""

    command: tuple[str, ...]


def run(call: Call) -> None:
    """Refuse until the step `land-checks` builds `lem serial`."""
    raise not_built("serial", "land-checks")


COMMAND = click.Command(
    "serial",
    params=[
        click.Argument(["command"], nargs=-1, required=True),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Run one command under the repository's one serial lock.",
)
