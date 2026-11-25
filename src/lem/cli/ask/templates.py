"""`lem ask templates`: the question page's templates.

    lem ask templates

A stub until the step `ask` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem ask templates`."""


def run(call: Call) -> None:
    """Refuse until the step `ask` builds `lem ask templates`."""
    raise not_built("ask templates", "ask")


COMMAND = click.Command(
    "templates",
    params=[],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The question page's templates.",
)
