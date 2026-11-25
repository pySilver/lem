"""`lem land file`: file the review's findings into the backlog.

    lem land file SLUG [--again] [--same RN.M=PATH]... [--new RN.M]...

The step `land-review` builds it (`app/landing/filing_step.py`).
"""

from typing import TYPE_CHECKING

import click
import msgspec

from lem.app.landing import filing_step
from lem.cli import place
from lem.model.landing.filing_flags import Flags

if TYPE_CHECKING:
    from lem.kernel.envelope import Envelope


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem land file`."""

    slug: str
    again: bool = False
    same: tuple[str, ...] = ()
    new: tuple[str, ...] = ()


def run(call: Call) -> Envelope:
    """Give each defect outside the change its place."""
    flags = Flags(again=call.again, same=call.same, new=call.new)
    return filing_step.run(place.folder(), call.slug, flags)


COMMAND = click.Command(
    "file",
    params=[
        click.Argument(["slug"]),
        click.Option(
            ["--again"],
            is_flag=True,
            help="write once more each filed item that is gone from the tip",
        ),
        click.Option(
            ["--same"],
            multiple=True,
            help="the defect is the one the backlog item PATH holds",
        ),
        click.Option(
            ["--new"], multiple=True, help="the defect is a defect of its own"
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="File the review's findings into the backlog.",
)
