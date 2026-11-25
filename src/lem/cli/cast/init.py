"""`lem cast init`: copy the persona panel's cast into this repository.

    lem cast init

A stub until the step `addons-outside` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem cast init`."""


def run(call: Call) -> None:
    """Refuse until the step `addons-outside` builds `lem cast init`."""
    raise not_built("cast init", "addons-outside")


COMMAND = click.Command(
    "init",
    params=[],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Copy the persona panel's cast into this repository.",
)
