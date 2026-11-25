"""`lem serve stop`: end the board server that runs.

    lem serve stop

A stub until the step `slice-board` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem serve stop`."""


def run(call: Call) -> None:
    """Refuse until the step `slice-board` builds `lem serve stop`."""
    raise not_built("serve stop", "slice-board")


COMMAND = click.Command(
    "stop",
    params=[],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="End the board server that runs.",
)
