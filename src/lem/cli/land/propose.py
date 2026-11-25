"""`lem land propose`: open or update the pull request.

    lem land propose SLUG --title TITLE --notes NOTES

A stub until the step `land-propose` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem land propose`."""

    slug: str
    title: str
    notes: str


def run(call: Call) -> None:
    """Refuse until the step `land-propose` builds `lem land propose`."""
    raise not_built("land propose", "land-propose")


COMMAND = click.Command(
    "propose",
    params=[
        click.Argument(["slug"]),
        click.Option(
            ["--title"],
            required=True,
            help="the subject of the change, one semantic line",
        ),
        click.Option(
            ["--notes"],
            required=True,
            help="the pull request's notes: decisions, what is left open",
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Open or update the pull request.",
)
