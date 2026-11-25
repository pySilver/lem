"""`lem ask close`: close a question page.

    lem ask close [PAGE_ID]

A stub until the step `ask` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem ask close`."""

    page_id: str | None = None


def run(call: Call) -> None:
    """Refuse until the step `ask` builds `lem ask close`."""
    raise not_built("ask close", "ask")


COMMAND = click.Command(
    "close",
    params=[
        click.Argument(["page_id"], required=False),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Close a question page.",
)
