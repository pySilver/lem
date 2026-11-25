"""`lem cast init`: copy the persona panel's cast into this repository.

lem cast init
"""

import click
import msgspec

from lem.addons.cast import setup
from lem.cli.place import folder


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem cast init`."""


def run(call: Call) -> dict[str, str]:
    """Run the cast command for the active worktree."""
    return setup.init(folder())


COMMAND = click.Command(
    "init",
    params=[],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Copy the persona panel's cast into this repository.",
)
