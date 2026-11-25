"""`lem waiting`: everything that waits for the owner, in its nine groups.

    lem waiting [--task SLUG]

Read only: the owner's presence, each group of what waits for him, the board's rows and stacks,
and the count of tasks that wait (`app/owner/listing.py`).
"""

from typing import TYPE_CHECKING

import click
import msgspec

from lem.app.owner import listing
from lem.cli import place
from lem.kernel import clock

if TYPE_CHECKING:
    from lem.app.owner.listed import Waiting


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem waiting`."""

    task: str | None = None


def run(call: Call) -> Waiting:
    """Everything that waits for the owner."""
    now = clock.now()
    today = now.astimezone().date()
    return listing.listed(place.folder(), call.task, now, today)


COMMAND = click.Command(
    "waiting",
    params=[
        click.Option(["--task"], help="only what waits for this task"),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Everything that waits for the owner, in its nine groups.",
)
