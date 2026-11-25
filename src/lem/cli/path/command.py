"""`lem path`: the place of one thing Lem reads in this repository.

    lem path NAME

A stub until the step `settings` builds it: it refuses `not-built`.
"""

from typing import Literal

import click
import msgspec

from lem.cli.stub import not_built
from lem.cli.words import choice

type Name = Literal[
    "profile",
    "personas",
    "lessons",
    "worktrees",
    "rules",
    "review",
    "backlog",
    "plans",
    "rulings",
    "cast",
    "state",
]


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem path`."""

    name: Name


def run(call: Call) -> None:
    """Refuse until the step `settings` builds `lem path`."""
    raise not_built("path", "settings")


COMMAND = click.Command(
    "path",
    params=[
        click.Argument(["name"], type=choice(Name)),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The place of one thing Lem reads in this repository.",
)
