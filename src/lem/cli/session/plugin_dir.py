"""`lem session plugin-dir`: the folder --plugin-dir names on a launch line.

    lem session plugin-dir

The folder `--plugin-dir` names on a launch line of this Lem, the app's own data, or null when
the project loads the installed plugin.
"""

import os

import click
import msgspec

from lem.adapters import harness_claude
from lem.cli import place
from lem.kernel import paths
from lem.ports.place import Place
from lem.store import places


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem session plugin-dir`."""


def run(call: Call) -> str | None:
    """The folder --plugin-dir names, or None."""
    where = places.workspace(place.folder())
    home = paths.home(os.environ)
    at = Place(checkout=where.checkout, home=home, environ=os.environ)
    folder = harness_claude.bind(at).plugin_folder(paths.root())
    return None if folder is None else str(folder)


COMMAND = click.Command(
    "plugin-dir",
    params=[],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The folder --plugin-dir names on a launch line.",
)
