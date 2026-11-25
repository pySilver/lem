"""`lem issue read`: one issue of origin's repository, by number or address.

    lem issue read ISSUE

A stub until the step `task` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem issue read`."""

    issue: str


def run(call: Call) -> None:
    """Refuse until the step `task` builds `lem issue read`."""
    raise not_built("issue read", "task")


COMMAND = click.Command(
    "read",
    params=[
        click.Argument(["issue"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="One issue of origin's repository, by number or address.",
)
