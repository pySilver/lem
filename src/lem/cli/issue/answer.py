"""`lem issue answer`: the task ended with an answer: one comment with it.

    lem issue answer SLUG

A stub until the step `task` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem issue answer`."""

    slug: str


def run(call: Call) -> None:
    """Refuse until the step `task` builds `lem issue answer`."""
    raise not_built("issue answer", "task")


COMMAND = click.Command(
    "answer",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The task ended with an answer: one comment with it.",
)
