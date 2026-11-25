"""`lem criteria change`: the owner's change of a task's criteria.

    lem criteria change SLUG (--file FILE|--typed|--pairs|--unchanged) [--words W]

A stub until the step `criteria` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem criteria change`."""

    slug: str
    path: str | None = None
    words: str | None = None
    typed: bool = False
    pairs: bool = False
    unchanged: bool = False


def run(call: Call) -> None:
    """Refuse until the step `criteria` builds `lem criteria change`."""
    raise not_built("criteria change", "criteria")


COMMAND = click.Command(
    "change",
    params=[
        click.Argument(["slug"]),
        click.Option(["--file", "path"], help="the changed criteria"),
        click.Option(["--words"], help="the owner's note, in his words"),
        click.Option(
            ["--typed"],
            is_flag=True,
            help="record the owner's No typed in the task's session",
        ),
        click.Option(
            ["--pairs"], is_flag=True, help="print the pairs of the newest change again"
        ),
        click.Option(
            ["--unchanged"],
            is_flag=True,
            help="the owner's No changes no criterion: the same criteria wait",
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The owner's change of a task's criteria.",
)
