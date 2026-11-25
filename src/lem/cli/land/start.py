"""`lem land start`: start the landing of a ready task.

    lem land start SLUG [--conflicting]

Built by the step `land-base`: a round begins, goes on after a cut, or starts again for an open
task, counted in its relands.
"""

from typing import TYPE_CHECKING

import click
import msgspec

from lem.app.landing import start
from lem.cli import place

if TYPE_CHECKING:
    from lem.kernel.envelope import Envelope


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem land start`."""

    slug: str
    conflicting: bool = False


def run(call: Call) -> Envelope:
    """Start the landing of the task."""
    return start.run(place.folder(), call.slug, conflicting=call.conflicting)


COMMAND = click.Command(
    "start",
    params=[
        click.Argument(["slug"]),
        click.Option(
            ["--conflicting"],
            is_flag=True,
            help="an open task the forge calls conflicting",
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Start the landing of a ready task.",
)
