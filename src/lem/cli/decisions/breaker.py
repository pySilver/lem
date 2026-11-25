"""`lem decisions breaker`: the circuit breaker: record the stop and hold the task.

    lem decisions breaker SLUG --cause irreversible|criteria [--irreversible WHAT]

A stub until the step `criteria` builds it: it refuses `not-built`.
"""

from typing import Literal

import click
import msgspec

from lem.cli.stub import not_built
from lem.cli.words import choice

type Cause = Literal["irreversible", "criteria"]
type Irreversible = Literal["data", "system", "person", "money"]


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem decisions breaker`."""

    slug: str
    cause: Cause
    irreversible: Irreversible | None = None
    document: str | None = None


def run(call: Call) -> None:
    """Refuse until the step `criteria` builds `lem decisions breaker`."""
    raise not_built("decisions breaker", "criteria")


COMMAND = click.Command(
    "breaker",
    params=[
        click.Argument(["slug"]),
        click.Option(
            ["--cause"], required=True, type=choice(Cause), help="why the breaker trips"
        ),
        click.Option(
            ["--irreversible"],
            type=choice(Irreversible),
            help="with --cause irreversible: what no later no can undo",
        ),
        click.Option(
            ["--document"],
            help="the breaker's document (default: breaker.md of the task)",
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The circuit breaker: record the stop and hold the task.",
)
