"""`lem cast run-dir`: make a panel's own folder for a task.

    lem cast run-dir SLUG

A stub until the step `addons-outside` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem cast run-dir`."""

    slug: str


def run(call: Call) -> None:
    """Refuse until the step `addons-outside` builds `lem cast run-dir`."""
    raise not_built("cast run-dir", "addons-outside")


COMMAND = click.Command(
    "run-dir",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Make a panel's own folder for a task.",
)
