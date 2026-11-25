"""`lem decisions breaker`: the circuit breaker: record the stop and hold the task.

    lem decisions breaker SLUG --cause irreversible|criteria [--irreversible WHAT]

It records the stop with its number, its cause and its document, and holds the task with the
line `breaker N waits for the owner`. FILE is `breaker.md` of the task's folder unless named, in
the form of `templates/breaker.md`, which it keeps as `breaker-N.md`: refused without one of its
parts, without `handoff.md` beside it, with work in the worktree that no commit holds, while
another breaker of the task waits, and for a task with its landing or ended.
"""

from typing import TYPE_CHECKING, Literal

import click
import msgspec

from lem.app.decisions import bound
from lem.app.decisions import breaker as breaking
from lem.app.decisions.stopping import Asked
from lem.cli import place
from lem.cli.words import choice
from lem.store import places

if TYPE_CHECKING:
    from lem.records.decisions import Breaker

type Cause = Literal["irreversible", "criteria"]
type Irreversible = Literal["data", "system", "person", "money"]


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem decisions breaker`."""

    slug: str
    cause: Cause
    irreversible: Irreversible | None = None
    document: str | None = None


def run(call: Call) -> Breaker:
    """Trip the breaker, and hold the task."""
    folder = place.folder()
    ports = bound.ports_of(places.workspace(folder).checkout)
    asked = Asked(cause=call.cause, kind=call.irreversible, document=call.document)
    return breaking.tripped(ports, folder, call.slug, asked)


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
