"""`lem land file`: file the review's findings into the backlog.

    lem land file SLUG [--again] [--same RN.M=PATH]... [--new RN.M]...

The plain path, as the step `slice-land` built it; the step `land-review` owns it.
"""

from typing import TYPE_CHECKING

import click
import msgspec

from lem.app.landing import filing
from lem.cli import place
from lem.model.landing.world import later

if TYPE_CHECKING:
    from lem.kernel.envelope import Envelope


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem land file`."""

    slug: str
    again: bool = False
    same: tuple[str, ...] = ()
    new: tuple[str, ...] = ()


def run(call: Call) -> Envelope:
    """File the findings; `--again`, `--same` and `--new` are the step `land-review`'s."""
    if call.again or call.same or call.new:
        raise later("`lem land file --again|--same|--new`", "land-review")
    return filing.run(place.folder(), call.slug)


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
