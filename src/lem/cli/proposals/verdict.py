"""`lem proposals verdict`: the reviewer's verdict on each proposal.

    lem proposals verdict --file FILE

A stub until the step `addons-flow` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem proposals verdict`."""

    path: str


def run(call: Call) -> None:
    """Refuse until the step `addons-flow` builds `lem proposals verdict`."""
    raise not_built("proposals verdict", "addons-flow")


COMMAND = click.Command(
    "verdict",
    params=[
        click.Option(
            ["--file", "path"],
            required=True,
            help="the verdicts as JSON, or - for stdin",
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The reviewer's verdict on each proposal.",
)
