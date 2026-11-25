"""`lem corrections record`: record what became of one correction.

    lem corrections record ID --decision D --verdict V [--target FILE] [--lesson L]

A stub until the step `addons-flow` builds it: it refuses `not-built`.
"""

from typing import Literal

import click
import msgspec

from lem.cli.stub import not_built
from lem.cli.words import choice

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


def run(call: Call) -> None:
    """Refuse until the step `addons-flow` builds `lem corrections record`."""
    raise not_built("corrections record", "addons-flow")


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
