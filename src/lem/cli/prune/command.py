"""`lem prune`: remove what the state folder no longer needs.

    lem prune [--dry-run] [--days N]

A stub until the step `board-duties` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem prune`."""

    dry_run: bool = False
    days: int | None = None


def run(call: Call) -> None:
    """Refuse until the step `board-duties` builds `lem prune`."""
    raise not_built("prune", "board-duties")


COMMAND = click.Command(
    "prune",
    params=[
        click.Option(
            ["--dry-run"], is_flag=True, help="remove nothing: say what would go"
        ),
        click.Option(
            ["--days"],
            type=click.INT,
            help="with --dry-run: what would go if state.keep_days were N",
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Remove what the state folder no longer needs.",
)
