"""`lem waiting`: everything that waits for the owner, in its nine groups.

    lem waiting [--task SLUG]

A stub until the step `owner` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem waiting`."""

    task: str | None = None


def run(call: Call) -> None:
    """Refuse until the step `owner` builds `lem waiting`."""
    raise not_built("waiting", "owner")


COMMAND = click.Command(
    "waiting",
    params=[
        click.Option(["--task"], help="only what waits for this task"),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Everything that waits for the owner, in its nine groups.",
)
