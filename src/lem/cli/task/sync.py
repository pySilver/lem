"""`lem task sync NAME`: the feature NAME takes in origin's base by a merge commit while it waits
for its parts, with the settings' checks on the merge and a push with a lease
(`app/tasks/sync.py`)."""

from typing import TYPE_CHECKING

import click
import msgspec

from lem.app.tasks import sync
from lem.cli import place

if TYPE_CHECKING:
    from lem.kernel.envelope import Envelope


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem task sync`."""

    slug: str


def run(call: Call) -> Envelope:
    """Sync the feature."""
    return sync.run(place.folder(), call.slug)


COMMAND = click.Command(
    "sync",
    params=[click.Argument(["slug"])],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Merge origin's base into the branch of the feature NAME, check it, and push it.",
)
