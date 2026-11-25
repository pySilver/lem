"""`lem settings show`: every setting in force, each with the file it comes from.

    lem settings show

The settings of the workspace of the call; outside a repository where Lem is set up,
`settings` is null and the machine's values and the load still show.
"""

import os

import click
import msgspec

from lem.cli import place
from lem.kernel.errors import Refusal
from lem.settings.show import Shown, shown
from lem.store import places


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem settings show`."""


def run(call: Call) -> Shown:
    """The settings of the workspace; its machine's alone where Lem is not set up."""
    try:
        checkout = places.workspace(place.folder()).checkout
    except Refusal as refused:
        if refused.code != "no-lem":
            raise
        return shown(None, os.environ)
    return shown(checkout, os.environ)


COMMAND = click.Command(
    "show",
    params=[],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Every setting, each with the file it comes from.",
)
