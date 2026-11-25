"""`lem corrections worker`: judge one correction the hook wrote.

    lem corrections worker PAYLOAD

A stub until the step `addons-flow` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem corrections worker`."""

    payload: str


def run(call: Call) -> None:
    """Refuse until the step `addons-flow` builds `lem corrections worker`."""
    raise not_built("corrections worker", "addons-flow")


COMMAND = click.Command(
    "worker",
    params=[
        click.Argument(["payload"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Judge one correction the hook wrote.",
)
