"""`lem task worktree`: make a task's worktree, or print where it is.

    lem task worktree SLUG [--path] [--branch B] [--checkout DIR]

Made on its branch, cut from origin's base after a fetch, with `checks.setup` run once in it
(`app/tasks/worktree.py`); `--path` prints where it is and makes nothing.
"""

from pathlib import Path

import click
import msgspec

from lem.app.tasks import worktree
from lem.cli import place


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem task worktree`."""

    slug: str
    path: bool = False
    branch: str | None = None
    checkout: str | None = None


def run(call: Call) -> worktree.Made:
    """Make the task's worktree, or print its path."""
    checkout = None if call.checkout is None else Path(call.checkout)
    asked = (call.branch, checkout)
    return worktree.worktree(
        place.folder(), call.slug, path_only=call.path, asked=asked
    )


COMMAND = click.Command(
    "worktree",
    params=[
        click.Argument(["slug"]),
        click.Option(
            ["--path"], is_flag=True, help="print the worktree's path, and make nothing"
        ),
        click.Option(["--branch"], help="the branch the worktree takes"),
        click.Option(
            ["--checkout"], help="the main checkout the worktree is made from"
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Make a task's worktree, or print where it is.",
)
