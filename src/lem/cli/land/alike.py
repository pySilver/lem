"""`lem land alike`: the backlog items that may hold the same defect.

    lem land alike SLUG --where PLACE --title TITLE --what FILE

The step `land-review` builds it (`app/landing/alike.py`).
"""

from typing import TYPE_CHECKING

import click
import msgspec

from lem.app.landing import alike, alike_words
from lem.cli import place

if TYPE_CHECKING:
    from lem.kernel.envelope import Envelope


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem land alike`."""

    slug: str
    where: str
    title: str
    what: str


def run(call: Call) -> Envelope:
    """Name the items Jev reads as the same defect as the finding."""
    defect = alike_words.defect_of(call.where, call.title, call.what)
    return alike.run(place.folder(), call.slug, defect)


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
