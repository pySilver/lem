"""`lem task talked`: the counts of the plan talk, which the pull request shows.

    lem task talked SLUG --reviewer AGENT --turns N ...

A stub until the step `task` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


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


def run(call: Call) -> None:
    """Refuse until the step `task` builds `lem task talked`."""
    raise not_built("task talked", "task")


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
