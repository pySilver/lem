"""`lem rules`: the rule files that hold for FILES and a range's files.

    lem rules [FILES]... [--range RANGE]

A stub until the step `settings` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.checks import at_least_one
from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem rules`."""

    files: tuple[str, ...] = ()
    commits: str | None = None


def run(call: Call) -> None:
    """Refuse until the step `settings` builds `lem rules`."""
    raise not_built("rules", "settings")


COMMAND = click.Command(
    "rules",
    params=[
        click.Argument(["files"], nargs=-1),
        click.Option(
            ["--range", "commits"], help="also the files this range of commits changes"
        ),
    ],
    callback=lambda **given: run(
        msgspec.convert(at_least_one(given, "files", "commits"), Call)
    ),
    help="The rule files that hold for FILES and a range's files.",
)
