"""`lem corrections lessons`: the lessons the corrections became.

    lem corrections lessons

A stub until the step `addons-flow` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem corrections lessons`."""


def run(call: Call) -> None:
    """Refuse until the step `addons-flow` builds `lem corrections lessons`."""
    raise not_built("corrections lessons", "addons-flow")


COMMAND = click.Command(
    "lessons",
    params=[],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The lessons the corrections became.",
)
