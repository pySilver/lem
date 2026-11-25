"""`lem task park`: put a task aside on the owner's word, with his reason.

    lem task park SLUG --why WHY

The hold `parked` of the design's part 3; `lem task resume SLUG` brings the task back. A stub
until the step `task` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem task park`."""

    slug: str
    why: str


def run(call: Call) -> None:
    """Refuse until the step `task` builds `lem task park`."""
    raise not_built("task park", "task")


COMMAND = click.Command(
    "park",
    params=[
        click.Argument(["slug"]),
        click.Option(["--why"], required=True, help="the owner's reason, in his words"),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Put a task aside on the owner's word, with his reason.",
)
