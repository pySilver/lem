"""`lem session list`: each task's newest session.

    lem session list

A stub until the step `slice-session` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem session list`."""


def run(call: Call) -> None:
    """Refuse until the step `slice-session` builds `lem session list`."""
    raise not_built("session list", "slice-session")


COMMAND = click.Command(
    "list",
    params=[],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Each task's newest session.",
)
