"""`lem cast show`: the panel's cast: its personas, its seats, the profile and where each is from.

    lem cast [show]

`lem cast` alone is this verb (`main`'s `cast.resolve`).
"""

import click
import msgspec

from lem.addons.cast import project
from lem.cli.place import folder


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem cast show`."""


def run(call: Call) -> project.Cast:
    """Run the cast command for the active worktree."""
    return project.resolve(folder())


COMMAND = click.Command(
    "show",
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The panel's cast: its personas, its seats, the profile and where each is from.",
)
