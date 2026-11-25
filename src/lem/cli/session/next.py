"""`lem session next`: the change of phase: open the next session.

    lem session next SLUG [--same]

A stub until the step `slice-session` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem session next`."""

    slug: str
    same: bool = False


def run(call: Call) -> None:
    """Refuse until the step `slice-session` builds `lem session next`."""
    raise not_built("session next", "slice-session")


COMMAND = click.Command(
    "next",
    params=[
        click.Argument(["slug"]),
        click.Option(
            ["--same"],
            is_flag=True,
            help="the owner's hand off: a fresh session for the same phase",
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The change of phase: open the next session.",
)
