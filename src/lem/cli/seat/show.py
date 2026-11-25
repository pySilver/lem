"""`lem seat show`: the seat in use for a task's role.

    lem seat show SLUG ROLE

The fallback while it stands in for the task, else the seat the settings name, with where it
comes from (`app/sessions/seats.py`).
"""

from typing import Literal

import click
import msgspec

from lem.app.sessions import here, seating, seats
from lem.cli import place
from lem.cli.words import choice

type Role = Literal["reviewer", "planner", "merger", "session"]


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem seat show`."""

    slug: str
    role: Role


def run(call: Call) -> seating.Shown:
    """The seat in use for the task's role."""
    return seats.shown(here.bound(place.folder()), call.slug, call.role)


COMMAND = click.Command(
    "show",
    params=[
        click.Argument(["slug"]),
        click.Argument(["role"], type=choice(Role)),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The seat in use for a task's role.",
)
