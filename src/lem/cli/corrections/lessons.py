"""`lem corrections lessons`: the lessons the corrections became.

    lem corrections lessons

Read only: the lessons earlier retros recorded, with their files and verdicts
(`addons/corrections/lessons.py`).
"""

import click
import msgspec

from lem.addons.corrections import lessons
from lem.cli import place
from lem.store import places


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem corrections lessons`."""


def run(call: Call) -> tuple[lessons.Lesson, ...]:
    """The lessons recorded."""
    return lessons.lessons(places.workspace(place.folder()).state)


COMMAND = click.Command(
    "lessons",
    params=[],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The lessons the corrections became.",
)
