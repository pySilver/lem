"""`lem serve ensure`: make sure one board server runs, from this code.

    lem serve ensure

A stub until the step `slice-board` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem serve ensure`."""


def run(call: Call) -> None:
    """Refuse until the step `slice-board` builds `lem serve ensure`."""
    raise not_built("serve ensure", "slice-board")


COMMAND = click.Command(
    "ensure",
    params=[],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Make sure one board server runs, from this code.",
)
