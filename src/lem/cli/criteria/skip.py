"""`lem criteria skip`: the skip of the persona read: asked, yes or no.

    lem criteria skip SLUG asked|yes|no

`asked` as the interview asks him, and his yes or no; on his yes the interview also logs his
words as a decision of his (`stages/interview.md`, step 5).
"""

from typing import TYPE_CHECKING, Literal

import click
import msgspec

from lem.app.criteria import skipping
from lem.cli import place
from lem.cli.words import choice

if TYPE_CHECKING:
    from lem.records.criteria import Criteria

type Answer = Literal["asked", "yes", "no"]


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem criteria skip`."""

    slug: str
    answer: Answer


def run(call: Call) -> Criteria:
    """Write the owner's word on the skip of the personas' read."""
    return skipping.skipped(place.folder(), call.slug, call.answer)


COMMAND = click.Command(
    "skip",
    params=[
        click.Argument(["slug"]),
        click.Argument(["answer"], type=choice(Answer)),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The skip of the persona read: asked, yes or no.",
)
