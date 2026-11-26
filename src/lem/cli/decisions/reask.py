"""Ask the owner again after a breaker's Help talk ends without a decision."""

from typing import TYPE_CHECKING

import click
import msgspec

from lem.app.decisions import reasking
from lem.cli import place

if TYPE_CHECKING:
    from lem.records.questions import Question


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The task, the Help question it answered, and the session's line about the talk."""

    slug: str
    question: str
    line: str


def run(call: Call) -> Question:
    """Return the new question of the breaker's hold."""
    return reasking.reasked(place.folder(), call.slug, call.question, call.line)


COMMAND = click.Command(
    "reask",
    params=[
        click.Argument(["slug"]),
        click.Option(
            ["--question"], required=True, help="the key of the owner's Help answer"
        ),
        click.Option(
            ["--line"], required=True, help="the session's line about the talk"
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Ask the owner again after Help ends without a decision.",
)
