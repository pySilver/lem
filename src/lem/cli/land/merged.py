"""`lem land merged`: the steps after the forge merged the pull request.

    lem land merged SLUG

The plain path, as the step `slice-land` built it; the step `land-merge` owns it.
"""

from typing import TYPE_CHECKING

import click
import msgspec

from lem.app.landing import merged
from lem.cli import place

if TYPE_CHECKING:
    from lem.kernel.envelope import Envelope


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem land merged`."""

    slug: str


def run(call: Call) -> Envelope:
    """Write down the forge's merge, and land the task."""
    return merged.run(place.folder(), call.slug)


COMMAND = click.Command(
    "merged",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The steps after the forge merged the pull request.",
)
