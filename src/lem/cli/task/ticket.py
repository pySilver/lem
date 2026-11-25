"""`lem task ticket`: record a step Lem did on a task's ticket, after the end too.

    lem task ticket SLUG STEP [--login LOGIN]

Written once, after the tracker took it (`assigned` before, with the login), and accepted
after the task's end (`app/tasks/ticket.py`).
"""

from typing import Literal

import click
import msgspec

from lem.app.tasks import ticket
from lem.cli import place
from lem.cli.words import choice

type Step = Literal[
    "started", "assigned", "unassigned", "commented", "landed", "dropped", "answered"
]


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem task ticket`."""

    slug: str
    step: Step
    login: str | None = None


def run(call: Call) -> ticket.Shown:
    """Write the step down, and give the ticket as it is now."""
    return ticket.stepped(place.folder(), call.slug, call.step, call.login)


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
