"""`lem settings show`: every setting, each with the file it comes from.

    lem settings show

The plain form of the fast track, as the step `slice-land` built it; the step `settings` owns it.
"""

import click
import msgspec

from lem.cli import place
from lem.kernel.errors import Refusal
from lem.settings.load import Shown, show
from lem.store import places


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem settings show`."""


def run(call: Call) -> Shown:
    """The settings of the workspace; none where Lem is not set up."""
    try:
        checkout = places.workspace(place.folder()).checkout
    except Refusal as refused:
        if refused.code != "no-lem":
            raise
        return show(None)
    return show(checkout)


COMMAND = click.Command(
    "show",
    params=[],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Every setting, each with the file it comes from.",
)
