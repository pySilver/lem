"""`lem task open`: open a task: its record and its folder.

    lem task open SLUG --ask WORDS [--ticket ID] [--branch B] ...

The task opens `shaping`, or `queued` behind each `--after`; a ticket, a backlog item and the
dropped task `--from` names are claimed under the workspace lock (`app/tasks/open.py`).
"""

import click
import msgspec

from lem.app.tasks import open as opening
from lem.app.tasks.opening import Asked
from lem.cli import place


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem task open`."""

    slug: str
    ask: str
    ticket: str | None = None
    ticket_repo: str | None = None
    branch: str | None = None
    night: str | None = None
    after: tuple[str, ...] = ()
    plan_only: bool = False
    backlog_item: str | None = None
    origin: str | None = None


def run(call: Call) -> opening.Opened:
    """Open the task."""
    return opening.opened(
        place.folder(), msgspec.convert(call, Asked, from_attributes=True)
    )


COMMAND = click.Command(
    "open",
    params=[
        click.Argument(["slug"]),
        click.Option(
            ["--ask"], required=True, help="the owner's words for this task, as given"
        ),
        click.Option(
            ["--ticket"],
            help="the tracker's ticket the ask came from: ABC-12, 42 or #42",
        ),
        click.Option(
            ["--ticket-repo"], help="with a GitHub issue: the repository of the issue"
        ),
        click.Option(
            ["--branch"], help="the branch the task takes, when it is not TYPE/SLUG"
        ),
        click.Option(["--night"], help="the night that opens the task, YYYY-MM-DD"),
        click.Option(
            ["--after"],
            multiple=True,
            help="a task this one waits for, once for each; it waits for all of them",
        ),
        click.Option(
            ["--plan-only"],
            is_flag=True,
            help="plan the task, and build nothing until the owner says",
        ),
        click.Option(
            ["--item", "backlog_item"], help="the backlog item the task starts from"
        ),
        click.Option(
            ["--from", "origin"], help="the dropped task this one starts again from"
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Open a task: its record and its folder.",
)
