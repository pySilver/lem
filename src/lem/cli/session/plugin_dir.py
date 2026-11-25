"""`lem session plugin-dir`: the folder --plugin-dir names on a launch line.

    lem session plugin-dir

A stub until the step `sessions` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem session plugin-dir`."""


def run(call: Call) -> None:
    """Refuse until the step `sessions` builds `lem session plugin-dir`."""
    raise not_built("session plugin-dir", "sessions")


COMMAND = click.Command(
    "plugin-dir",
    params=[],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The folder --plugin-dir names on a launch line.",
)
