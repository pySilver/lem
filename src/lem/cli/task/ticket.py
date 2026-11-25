"""`lem task ticket`: record a step Lem did on a task's ticket, after the end too.

    lem task ticket SLUG STEP [--login LOGIN]

A stub until the step `task` builds it: it refuses `not-built`.
"""

from typing import Literal

import click
import msgspec

from lem.cli.stub import not_built
from lem.cli.words import choice

type Step = Literal[
    "started", "assigned", "unassigned", "commented", "landed", "dropped", "answered"
]


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem task ticket`."""

    slug: str
    step: Step
    login: str | None = None


def run(call: Call) -> None:
    """Refuse until the step `task` builds `lem task ticket`."""
    raise not_built("task ticket", "task")


COMMAND = click.Command(
    "ticket",
    params=[
        click.Argument(["slug"]),
        click.Argument(["step"], type=choice(Step)),
        click.Option(
            ["--login"], help="with assigned: the login Lem added as the assignee"
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Record a step Lem did on a task's ticket, after the end too.",
)
