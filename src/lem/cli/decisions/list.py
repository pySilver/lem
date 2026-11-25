"""`lem decisions list`: a task's decisions.

    lem decisions list SLUG

Every decision and breaker of the task, each as it stands now: a breaker waits, or the owner's
help settled it.
"""

from typing import TYPE_CHECKING

import click
import msgspec

from lem.app.decisions import listing
from lem.cli import place

if TYPE_CHECKING:
    from lem.model.decisions.book import Listed


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem decisions list`."""

    slug: str


def run(call: Call) -> tuple[Listed, ...]:
    """Every decision and breaker of the task, each as it stands now."""
    return listing.listed(place.folder(), call.slug)


COMMAND = click.Command(
    "list",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="A task's decisions.",
)
