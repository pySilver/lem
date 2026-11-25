"""`lem corrections record`: record what became of one correction.

    lem corrections record ID --decision D --verdict V [--target FILE] [--lesson L]

A lesson needs `--lesson` and `--target`; a lesson that went into a proposal of the retro is
`--verdict proposed`, with the proposal's name in its sentence (`addons/corrections/reviewing.py`).
"""

from typing import Literal

import click
import msgspec

from lem.addons.corrections import reviewing
from lem.cli import place
from lem.cli.words import choice
from lem.kernel import clock
from lem.store import places

type Decision = Literal["lesson", "not_lesson"]
type Verdict = Literal[
    "accepted", "changed", "rejected", "proposed", "missed", "unasked"
]


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem corrections record`."""

    entry: str
    decision: Decision
    verdict: Verdict
    target: str | None = None
    lesson: str | None = None


def run(call: Call) -> reviewing.Recorded:
    """Write what was decided about the group."""
    state = places.state_of(places.workspace(place.folder()).checkout)
    review = reviewing.Review(
        gid=call.entry,
        decision=call.decision,
        verdict=call.verdict,
        target=call.target,
        lesson=call.lesson,
    )
    return reviewing.recorded(state, review, clock.now())


COMMAND = click.Command(
    "record",
    params=[
        click.Argument(["entry"]),
        click.Option(
            ["--decision"],
            required=True,
            type=choice(Decision),
            help="a lesson, or not one",
        ),
        click.Option(
            ["--verdict"],
            required=True,
            type=choice(Verdict),
            help="the owner's answer to the move, or what became of it",
        ),
        click.Option(["--target"], help="the file the lesson went to"),
        click.Option(["--lesson"], help="the lesson in one sentence"),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Record what became of one correction.",
)
