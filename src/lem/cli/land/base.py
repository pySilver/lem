"""`lem land base`: bring the task's branch onto the base it lands on.

    lem land base SLUG

Built by the step `land-base`: the plain rebase, judged from git's merges, a conflict kept for a
builder, and what git refused in its own words.
"""

from typing import TYPE_CHECKING

import click
import msgspec

from lem.app.landing import base
from lem.cli import place

if TYPE_CHECKING:
    from lem.kernel.envelope import Envelope


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem land base`."""

    slug: str


def run(call: Call) -> Envelope:
    """Bring the task's branch onto origin's base."""
    return base.run(place.folder(), call.slug)


COMMAND = click.Command(
    "base",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Bring the task's branch onto the base it lands on.",
)
