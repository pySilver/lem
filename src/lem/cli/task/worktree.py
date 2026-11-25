"""`lem task worktree`: make a task's worktree, or print where it is.

    lem task worktree SLUG [--path] [--branch B] [--checkout DIR]

A stub until the step `slice-land` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem task worktree`."""

    slug: str
    path: bool = False
    branch: str | None = None
    checkout: str | None = None


def run(call: Call) -> None:
    """Refuse until the step `slice-land` builds `lem task worktree`."""
    raise not_built("task worktree", "slice-land")


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
