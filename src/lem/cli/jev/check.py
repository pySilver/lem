"""`lem jev check`: ask the Jev model the questions of a spec.

    lem jev [check] SPEC

A stub until the step `addons-outside` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem jev check`."""

    spec: str


def run(call: Call) -> None:
    """Refuse until the step `addons-outside` builds `lem jev check`."""
    raise not_built("jev check", "addons-outside")


COMMAND = click.Command(
    "check",
    params=[
        click.Argument(["spec"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Ask the Jev model the questions of a spec.",
)
