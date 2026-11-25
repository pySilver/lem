"""`lem serve peers`: each machine joined, and whether it answers now.

    lem serve peers

A stub until the step `addons-outside` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem serve peers`."""


def run(call: Call) -> None:
    """Refuse until the step `addons-outside` builds `lem serve peers`."""
    raise not_built("serve peers", "addons-outside")


COMMAND = click.Command(
    "peers",
    params=[],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Each machine joined, and whether it answers now.",
)
