"""`lem task span`: the start or the end of one span of a task's work.

    lem task span SLUG NAME start|end [--of N/M] [--job J] [--by B]

A start that takes no field refuses one, a task of the plan takes `--of N/M`, a builder's job is
one of its jobs, the plan talk names its reviewer with `--by`, and the lead its kind; an end
needs an open span of its name, and a second start of an open span is refused
(`model/task/span_forms.py`).
"""

from typing import Literal

import click
import msgspec

from lem.app.tasks import spans
from lem.cli import place
from lem.cli.words import choice
from lem.model.task.span_forms import Given
from lem.store import places

type Edge = Literal["start", "end"]


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem task span`."""

    slug: str
    name: str
    edge: Edge
    of: str | None = None
    job: str | None = None
    by: str | None = None


def run(call: Call) -> spans.Marked:
    """Mark the start or the end of the span, now."""
    state = places.workspace(place.folder()).state
    given = Given(
        name=call.name,
        edge=call.edge,
        of=call.of,
        job=call.job,
        by=call.by,
    )
    return spans.marked(state, call.slug, given)


COMMAND = click.Command(
    "span",
    params=[
        click.Argument(["slug"]),
        click.Argument(["name"]),
        click.Argument(["edge"], type=choice(Edge)),
        click.Option(
            ["--of"], help="with the span task: its number of the plan's tasks, N/M"
        ),
        click.Option(["--job"], help="the job the span is of"),
        click.Option(["--by"], help="who works in the span"),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The start or the end of one span of a task's work.",
)
