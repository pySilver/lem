"""`lem doctor`: check this machine for the tools Lem needs and recommends.

    lem doctor

A stub until the step `settings` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem doctor`."""


def run(call: Call) -> None:
    """Refuse until the step `settings` builds `lem doctor`."""
    raise not_built("doctor", "settings")


COMMAND = click.Command(
    "doctor",
    params=[],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Check this machine for the tools Lem needs and recommends.",
)
