"""`lem cast show`: the panel's cast: its personas, its seats, the profile and where each is from.

    lem cast [show]

`lem cast` alone is this verb (`main`'s `cast.resolve`). A stub until the step `addons-outside`
builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem cast show`."""


def run(call: Call) -> None:
    """Refuse until the step `addons-outside` builds `lem cast show`."""
    raise not_built("cast show", "addons-outside")


COMMAND = click.Command(
    "show",
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The panel's cast: its personas, its seats, the profile and where each is from.",
)
