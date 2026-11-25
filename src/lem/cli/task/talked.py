"""`lem task talked`: the counts of the plan talk, which the pull request shows.

    lem task talked SLUG --reviewer AGENT --turns N ...

The counts agree with each other (`model/task/talk.py`), and the record ends the talk's span,
which `lem task span SLUG plan-talk start --by AGENT` began.
"""

import click
import msgspec

from lem.app.tasks import talked
from lem.cli import place
from lem.kernel import clock
from lem.records.work import Talk
from lem.store import places


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem task talked`."""

    slug: str
    reviewer: str
    turns: int
    questions: int
    settled: int
    left_open: int
    repaired: int
    design: int
    unargued: int
    root: int
    layer: int
    shared: int


def run(call: Call) -> talked.Talked:
    """Write the plan talk's counts."""
    counts = Talk(
        reviewer=call.reviewer,
        turns=call.turns,
        questions=call.questions,
        settled=call.settled,
        open=call.left_open,
        repaired=call.repaired,
        design=call.design,
        unargued=call.unargued,
        root=call.root,
        layer=call.layer,
        shared=call.shared,
        at=clock.now(),
    )
    return talked.talked(places.workspace(place.folder()).state, call.slug, counts)


COMMAND = click.Command(
    "talked",
    params=[
        click.Argument(["slug"]),
        click.Option(
            ["--reviewer"], required=True, help="the agent that reviewed the plan"
        ),
        click.Option(
            ["--turns"], required=True, type=click.INT, help="the turns of the talk"
        ),
        click.Option(
            ["--questions"],
            required=True,
            type=click.INT,
            help="the questions the reviewer asked",
        ),
        click.Option(
            ["--settled"], required=True, type=click.INT, help="the questions settled"
        ),
        click.Option(
            ["--open", "left_open"],
            required=True,
            type=click.INT,
            help="the questions left open",
        ),
        click.Option(
            ["--repaired"],
            required=True,
            type=click.INT,
            help="the repairs of the plan",
        ),
        click.Option(
            ["--design"],
            required=True,
            type=click.INT,
            help="the changes of the design",
        ),
        click.Option(
            ["--unargued"],
            required=True,
            type=click.INT,
            help="the points nobody argued",
        ),
        click.Option(
            ["--root"],
            required=True,
            type=click.INT,
            help="the causes found at their root",
        ),
        click.Option(
            ["--layer"],
            required=True,
            type=click.INT,
            help="the fixes at another layer",
        ),
        click.Option(
            ["--shared"], required=True, type=click.INT, help="the shared causes"
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The counts of the plan talk, which the pull request shows.",
)
