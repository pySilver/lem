"""`lem cast run-dir`: make a panel's own folder for a task.

lem cast run-dir SLUG
"""

import click
import msgspec

from lem.addons.cast import setup
from lem.cli.place import folder


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem cast run-dir`."""

    slug: str


def run(call: Call) -> dict[str, str]:
    """Run the cast command for the active worktree."""
    return {"dir": setup.run_dir(folder(), call.slug)}


COMMAND = click.Command(
    "run-dir",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Make a panel's own folder for a task.",
)
