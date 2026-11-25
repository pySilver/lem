"""`lem land read`: the review's read: what is due, or its record.

    lem land read SLUG [--record FILE]

The step `land-review` builds it (`app/landing/review.py`).
"""

from typing import TYPE_CHECKING

import click
import msgspec

from lem.app.landing import review
from lem.cli import place

if TYPE_CHECKING:
    from lem.kernel.envelope import Envelope


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem land read`."""

    slug: str
    record: str | None = None


def run(call: Call) -> Envelope:
    """Say what review is due, or record the one the agent ran."""
    return review.run(place.folder(), call.slug, call.record)


COMMAND = click.Command(
    "read",
    params=[
        click.Argument(["slug"]),
        click.Option(
            ["--record"], help="a JSON file that says what the review was and found"
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The review's read: what is due, or its record.",
)
