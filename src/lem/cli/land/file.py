"""`lem land file`: file the review's findings into the backlog.

    lem land file SLUG [--again] [--same RN.M=PATH]... [--new RN.M]...

A stub until the step `land-review` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem land file`."""

    slug: str
    again: bool = False
    same: tuple[str, ...] = ()
    new: tuple[str, ...] = ()


def run(call: Call) -> None:
    """Refuse until the step `land-review` builds `lem land file`."""
    raise not_built("land file", "land-review")


COMMAND = click.Command(
    "file",
    params=[
        click.Argument(["slug"]),
        click.Option(
            ["--again"],
            is_flag=True,
            help="write once more each filed item that is gone from the tip",
        ),
        click.Option(
            ["--same"],
            multiple=True,
            help="the defect is the one the backlog item PATH holds",
        ),
        click.Option(
            ["--new"], multiple=True, help="the defect is a defect of its own"
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="File the review's findings into the backlog.",
)
