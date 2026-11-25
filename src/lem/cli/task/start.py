"""`lem task start`: start a queued task on the owner's word.

    lem task start SLUG --words WORDS

A stub until the step `task` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem task start`."""

    slug: str
    words: str


def run(call: Call) -> None:
    """Refuse until the step `task` builds `lem task start`."""
    raise not_built("task start", "task")


COMMAND = click.Command(
    "start",
    params=[
        click.Argument(["slug"]),
        click.Option(["--words"], required=True, help="the owner's words, as typed"),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Start a queued task on the owner's word.",
)
