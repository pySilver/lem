"""`lem task open`: open a task: its record and its folder.

    lem task open SLUG --ask WORDS [--ticket ID] [--branch B] ...

The plain form of the fast track, as the step `slice-land` built it; the step `task` owns it.
"""

from typing import TYPE_CHECKING

import click
import msgspec

from lem.app.tasks import open as opening
from lem.cli import place
from lem.cli.stub import not_built

if TYPE_CHECKING:
    from lem.app.tasks.open import Opened


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem task open`."""

    slug: str
    ask: str
    ticket: str | None = None
    ticket_repo: str | None = None
    branch: str | None = None
    night: str | None = None
    after: str | None = None
    plan_only: bool = False
    backlog_item: str | None = None
    origin: str | None = None


def run(call: Call) -> Opened:
    """Open the task; the other words are the step `task`'s."""
    others = (call.ticket, call.ticket_repo, call.night, call.after, call.backlog_item)
    if any(others) or call.origin or call.plan_only:
        raise not_built(
            "task open --ticket|--night|--after|--plan-only|--item|--from", "task"
        )
    ask, branch = call.ask, call.branch
    return opening.opened(place.folder(), call.slug, ask=ask, branch=branch)


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
        click.Option(["--after"], help="the task this one waits for"),
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
