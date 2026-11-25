"""`lem issue answer`: the task ended with an answer: one comment with it.

lem issue answer SLUG
"""

import click
import msgspec

from lem.app.tasks import ports
from lem.app.tasks.issues import ends
from lem.cli import place
from lem.store import places


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem issue answer`."""

    slug: str


def run(call: Call) -> object:
    """Post the answer's comment, and remove the assignee Lem added."""
    where = places.workspace(place.folder())
    return ends.ended(ports.bound(where), where, call.slug, "answer")


COMMAND = click.Command(
    "answer",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The task ended with an answer: one comment with it.",
)
