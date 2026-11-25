"""`lem path`: the place of one thing Lem reads in this repository.

    lem path NAME

A stub until the step `settings` builds it: it refuses `not-built`.
"""

from typing import Literal, get_args

import click
import msgspec

from lem.cli.stub import not_built

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

# A key of [paths] that names no place, which the parser takes to say where to look instead.
PLAN_FILE = "plan_file"


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem path`."""

    name: Name


def placed(ctx: click.Context, place: click.Parameter, word: str) -> str:
    """The name; `plan_file` is a wrong call that says what to run for a plan's file name."""
    if word == PLAN_FILE:
        raise click.BadParameter(
            "paths.plan_file is the pattern of a plan's name, not a path: "
            "`lem task plan-file SLUG` prints the name of a plan's file",
            ctx,
            place,
        )
    return word


def run(call: Call) -> None:
    """Refuse until the step `settings` builds `lem path`."""
    raise not_built("path", "settings")


COMMAND = click.Command(
    "path",
    params=[
        click.Argument(
            ["name"],
            metavar="NAME",
            type=click.Choice((*get_args(Name.__value__), PLAN_FILE)),
            callback=placed,
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The place of one thing Lem reads in this repository.",
)
