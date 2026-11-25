"""`lem session talk`: copy the turns about the task's ask into its talk.md.

    lem session talk SLUG --from WORDS [--leave WORDS]...

A stub until the step `sessions` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem session talk`."""

    slug: str
    start: str
    leave: tuple[str, ...] = ()


def run(call: Call) -> None:
    """Refuse until the step `sessions` builds `lem session talk`."""
    raise not_built("session talk", "sessions")


COMMAND = click.Command(
    "talk",
    params=[
        click.Argument(["slug"]),
        click.Option(
            ["--from", "start"],
            required=True,
            help="the first words of the owner's turn where the topic began",
        ),
        click.Option(
            ["--leave"],
            multiple=True,
            help="the first words of an owner turn of another topic",
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Copy the turns about the task's ask into its talk.md.",
)
