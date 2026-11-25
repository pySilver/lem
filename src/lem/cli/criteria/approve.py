"""`lem criteria approve`: approve a task's criteria.

    lem criteria approve SLUG [--file FILE] [--small|--read|--alone] [--shown DIGEST]

A stub until the step `slice-land` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem criteria approve`."""

    slug: str
    path: str | None = None
    small: bool = False
    read: bool = False
    alone: bool = False
    shown: str | None = None


def run(call: Call) -> None:
    """Refuse until the step `slice-land` builds `lem criteria approve`."""
    raise not_built("criteria approve", "slice-land")


COMMAND = click.Command(
    "approve",
    params=[
        click.Argument(["slug"]),
        click.Option(
            ["--file", "path"], help="the criteria approved, with no test lines"
        ),
        click.Option(
            ["--small"],
            is_flag=True,
            help="Lem approves the one criterion of a fast-track task",
        ),
        click.Option(
            ["--read"],
            is_flag=True,
            help="the lead freezes criteria a read found clear",
        ),
        click.Option(
            ["--alone"],
            is_flag=True,
            help="the criteria of a task that runs without the owner",
        ),
        click.Option(
            ["--shown"],
            help="with --file: the digest of the file as the owner's page showed it",
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Approve a task's criteria.",
)
