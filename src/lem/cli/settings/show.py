"""`lem settings show`: every setting, each with the file it comes from.

    lem settings show

A stub until the step `slice-land` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem settings show`."""


def run(call: Call) -> None:
    """Refuse until the step `slice-land` builds `lem settings show`."""
    raise not_built("settings show", "slice-land")


COMMAND = click.Command(
    "show",
    params=[],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Every setting, each with the file it comes from.",
)
