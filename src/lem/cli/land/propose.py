"""`lem land propose`: green or not green, the pull request's text, the push and the pull request.

    lem land propose SLUG --title TITLE --notes NOTES

Its result names the pull request's number and address, and `say` gives them with green or each
reason it is not (`app/landing/propose.py`).
"""

from typing import TYPE_CHECKING

import click
import msgspec

from lem.app.landing import propose
from lem.cli import place

if TYPE_CHECKING:
    from lem.kernel.envelope import Envelope


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem land propose`."""

    slug: str
    title: str
    notes: str


def run(call: Call) -> Envelope:
    """Push the tip and open or update the pull request."""
    title, notes = call.title, call.notes
    return propose.run(place.folder(), call.slug, title=title, notes=notes)


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
