"""`lem criteria digest`: the digest of a task's criteria, or of a file.

    lem criteria digest SLUG [--file FILE]

A stub until the step `criteria` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem criteria digest`."""

    slug: str
    path: str | None = None


def run(call: Call) -> None:
    """Refuse until the step `criteria` builds `lem criteria digest`."""
    raise not_built("criteria digest", "criteria")


COMMAND = click.Command(
    "digest",
    params=[
        click.Argument(["slug"]),
        click.Option(["--file", "path"], help="the criteria to mark"),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The digest of a task's criteria, or of a file.",
)
