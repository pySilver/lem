"""`lem nap may`: whether a nap may start now.

    lem nap may

With the naps off it is a no with exit 0 that writes nothing; with them on, a yes writes the
nap's start down, and its answer names the minute of the nap's folder (`addons/naps/may.py`).
The naps' table is the main checkout's, and one person's local file may only say no.
"""

from typing import TYPE_CHECKING

import click
import msgspec

from lem.addons.naps import may
from lem.cli import place
from lem.kernel import clock
from lem.settings.load import settings_of
from lem.store import places

if TYPE_CHECKING:
    from lem.addons.naps.answer import May


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem nap may`."""


def run(call: Call) -> May:
    """Whether a nap may start now; a yes writes it down."""
    where = places.workspace(place.folder())
    loaded = settings_of(where.checkout)
    switch = (loaded.settings.naps.on, loaded.sources["naps.on"])
    return may.may_nap(places.state_of(where.checkout), switch, clock.now())


COMMAND = click.Command(
    "may",
    params=[],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Whether a nap may start now.",
)
