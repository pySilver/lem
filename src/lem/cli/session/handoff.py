"""`lem session handoff`: check the task's handoff.md against its template.

    lem session handoff SLUG --check

A stub until the step `sessions` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.checks import exactly_one
from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem session handoff`."""

    slug: str
    check: bool = False


def run(call: Call) -> None:
    """Refuse until the step `sessions` builds `lem session handoff`."""
    raise not_built("session handoff", "sessions")


COMMAND = click.Command(
    "handoff",
    params=[
        click.Argument(["slug"]),
        click.Option(
            ["--check"],
            is_flag=True,
            help="check the handoff against templates/handoff.md",
        ),
    ],
    callback=lambda **given: run(msgspec.convert(exactly_one(given, "check"), Call)),
    help="Check the task's handoff.md against its template.",
)
