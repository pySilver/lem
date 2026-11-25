"""`lem seat show`: the seat in use for a task's role.

    lem seat show SLUG ROLE

A stub until the step `sessions` builds it: it refuses `not-built`.
"""

from typing import Literal

import click
import msgspec

from lem.cli.stub import not_built
from lem.cli.words import choice

type Role = Literal["reviewer", "planner", "merger", "session"]


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem seat show`."""

    slug: str
    role: Role


def run(call: Call) -> None:
    """Refuse until the step `sessions` builds `lem seat show`."""
    raise not_built("seat show", "sessions")


COMMAND = click.Command(
    "show",
    params=[
        click.Argument(["slug"]),
        click.Argument(["role"], type=choice(Role)),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The seat in use for a task's role.",
)
