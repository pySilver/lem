"""`lem land alike`: the backlog items that may hold the same defect.

    lem land alike SLUG --where PLACE --title TITLE --what FILE

A stub until the step `land-review` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem land alike`."""

    slug: str
    where: str
    title: str
    what: str


def run(call: Call) -> None:
    """Refuse until the step `land-review` builds `lem land alike`."""
    raise not_built("land alike", "land-review")


COMMAND = click.Command(
    "alike",
    params=[
        click.Argument(["slug"]),
        click.Option(
            ["--where"], required=True, help="the finding's place, PATH or PATH:SYMBOL"
        ),
        click.Option(["--title"], required=True, help="the finding's title, one line"),
        click.Option(
            ["--what"],
            required=True,
            help="a file with the finding's run: what happens, with the input",
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The backlog items that may hold the same defect.",
)
