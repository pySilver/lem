"""`lem task worktree`: make a task's worktree, or print where it is.

    lem task worktree SLUG [--path] [--branch B] [--checkout DIR]

The plain form of the fast track, as the step `slice-land` built it; the step `task` owns it.
"""

import click
import msgspec

from lem.app.tasks import worktree
from lem.cli import place
from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem task worktree`."""

    slug: str
    path: bool = False
    branch: str | None = None
    checkout: str | None = None


def run(call: Call) -> worktree.Made:
    """Make the task's worktree, or print its path; `--checkout` is the step `task`'s."""
    if call.checkout:
        raise not_built("task worktree --checkout", "task")
    folder = place.folder()
    return worktree.worktree(folder, call.slug, path_only=call.path, branch=call.branch)


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
