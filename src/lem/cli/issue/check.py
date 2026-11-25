"""`lem issue check`: whether origin's issues can be Lem's tracker; writes nothing.

    lem issue check

A stub until the step `task` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem issue check`."""


def run(call: Call) -> None:
    """Refuse until the step `task` builds `lem issue check`."""
    raise not_built("issue check", "task")


COMMAND = click.Command(
    "check",
    params=[],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Whether origin's issues can be Lem's tracker; writes nothing.",
)
