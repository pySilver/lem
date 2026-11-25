"""`lem land polish`: the polish pass, and its check when it is done.

    lem land polish SLUG [--done]

Its start prints what the polish builder gets; `--done` checks what it committed and keeps the
pass. The fast track has none. The step `land-checks` owns it.
"""

from typing import TYPE_CHECKING

import click
import msgspec

from lem.app.landing import polish
from lem.cli import place

if TYPE_CHECKING:
    from lem.kernel.envelope import Envelope


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem land polish`."""

    slug: str
    done: bool = False


def run(call: Call) -> Envelope:
    """Start the pass, or check it when it is done."""
    return polish.run(place.folder(), call.slug, done=call.done)


COMMAND = click.Command(
    "polish",
    params=[
        click.Argument(["slug"]),
        click.Option(
            ["--done"],
            is_flag=True,
            help="after the polish builder: check what it committed",
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The polish pass, and its check when it is done.",
)
