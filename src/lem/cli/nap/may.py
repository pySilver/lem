"""`lem nap may`: whether a nap may start now.

    lem nap may

A stub until the step `addons-flow` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem nap may`."""


def run(call: Call) -> None:
    """Refuse until the step `addons-flow` builds `lem nap may`."""
    raise not_built("nap may", "addons-flow")


COMMAND = click.Command(
    "may",
    params=[],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Whether a nap may start now.",
)
