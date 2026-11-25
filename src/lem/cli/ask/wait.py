"""`lem ask wait`: wait for the answer of a page opened with `--no-wait`.

    lem ask wait PAGE_ID [--timeout SECONDS] ...

A stub until the step `ask` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.ask.shown import Shown, options
from lem.cli.stub import not_built


class Call(Shown, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem ask wait`."""

    page_id: str


def run(call: Call) -> None:
    """Refuse until the step `ask` builds `lem ask wait`."""
    raise not_built("ask wait", "ask")


COMMAND = click.Command(
    "wait",
    params=[
        click.Argument(["page_id"]),
        *options(),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Wait for the answer of a page opened with --no-wait.",
)
