"""`lem path`: the place of one thing Lem reads in this repository.

    lem path NAME

The absolute path in the main checkout, from a task's worktree too, and whether it is there;
the plans folder and the rulings file as the team's settings name them.
"""

from typing import Literal, get_args

import click
import msgspec

from lem.cli import place
from lem.settings.load import team_of
from lem.settings.placed import Placed, places_of
from lem.store import places

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


def run(call: Call) -> Placed:
    """The place NAME names in the workspace of the call."""
    checkout = places.workspace(place.folder()).checkout
    return places_of(checkout, team_of(checkout).paths)[call.name]


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
