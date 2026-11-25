"""The first record of a task, from the words of `lem task open`: its ask, its ticket, its
backlog item, its night, its queue and the dropped task it goes on from."""

import datetime as dt
from typing import TYPE_CHECKING

from lem.kernel import release
from lem.kernel.errors import Refusal
from lem.model.task import tickets
from lem.records.base import Frozen, Moment
from lem.records.journal.task import StateNoted
from lem.records.record import Record
from lem.records.task import Task
from lem.records.tickets import Ticket

if TYPE_CHECKING:
    from lem.records.tickets import Tracker
    from lem.store.places import Workspace


# The folder of the reviewer's items, from the main checkout.
REVIEWER_ITEMS = ".lem/state/backlog"


class Asked(Frozen, frozen=True, kw_only=True):
    """What `lem task open` was given."""

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


def ticket_of(asked: Asked, kind: Tracker | None) -> Ticket | None:
    """The task's ticket in its one form, or None; `--ticket-repo` goes with `--ticket`."""
    if asked.ticket is None:
        if asked.ticket_repo is not None:
            raise Refusal(
                "ticket-repo",
                "--ticket-repo is the repository of the issue the task came from",
                "give it with --ticket, or leave it out",
            )
        return None
    named = tickets.ticket_id(kind, asked.ticket)
    if kind is None:
        return None
    repo = tickets.repository(kind, asked.ticket_repo)
    return Ticket(tracker=kind, id=named, repo=repo)


def night_of(asked: Asked) -> dt.date | None:
    """The night that opens the task, or None."""
    if asked.night is None:
        return None
    try:
        return dt.date.fromisoformat(asked.night)
    except ValueError:
        raise Refusal(
            "night",
            f"--night is the night's date, YYYY-MM-DD, not {asked.night!r}",
            "give the night's date, as 2026-11-25",
        ) from None


def item_of(workspace: Workspace, asked: Asked) -> str | None:
    """The backlog item the task starts from, a path in the main checkout; refused when it
    is gone (the owner dropped it in the meantime)."""
    path = asked.backlog_item or reviewer_item(workspace, asked.ask)
    if path is None:
        return None
    if not (workspace.checkout / path).is_file():
        raise Refusal(
            "item-gone",
            f"the backlog item {path} is not in {workspace.checkout}: the owner dropped it, "
            "or it never was",
            "start the task from the owner's own words (--ask), with no --item",
        )
    return path


def reviewer_item(workspace: Workspace, ask: str) -> str | None:
    """The reviewer's item an ask is (the board's "Start a task" writes its path,
    `.lem/state/backlog/NAME.md`, whole or from the main checkout), or None."""
    path = ask.strip().removeprefix(f"{workspace.checkout}/")
    parent, _, name = path.rpartition("/")
    if parent != REVIEWER_ITEMS or not name.endswith(".md") or name == ".md":
        return None
    return path


def words_of(asked: Asked) -> str:
    """The owner's words, as given; refused when they are empty."""
    if not asked.ask.strip():
        raise Refusal(
            "ask",
            "--ask is the owner's words for this task, and they are empty",
            "give his words as he typed them",
        )
    return asked.ask.strip()


def fresh(
    workspace: Workspace, asked: Asked, kind: Tracker | None, now: Moment
) -> Record:
    """The first record of the task `asked` names."""
    night = night_of(asked)
    status = "queued" if asked.after else "shaping"
    task = Task(
        slug=asked.slug,
        ask=words_of(asked),
        opened=now,
        status=status,
        since=now,
        branch=asked.branch,
        backlog_item=item_of(workspace, asked),
        resumed_from=asked.origin,
        ticket=ticket_of(asked, kind),
        night=night,
        plan_only=asked.plan_only,
        after=asked.after,
        mode="with-owner" if night is None else "alone",
        mode_since=None if night is None else now,
    )
    entry = StateNoted(at=now, status=status, line="the task is open")
    return Record(release=release.running(), task=task, journal=(entry,))
