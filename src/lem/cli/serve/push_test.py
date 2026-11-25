"""`lem serve push-test`: send one push to every device that turned it on.

    lem serve push-test

A stub until the step `board-service` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem serve push-test`."""


def run(call: Call) -> None:
    """Refuse until the step `board-service` builds `lem serve push-test`."""
    raise not_built("serve push-test", "board-service")


COMMAND = click.Command(
    "push-test",
    params=[],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Send one push to every device that turned it on.",
)
