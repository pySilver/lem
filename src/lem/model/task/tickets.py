"""A task's ticket: its id in the one saved form, what its end still owes it, and the record of
each step Lem took on it (`project.ticket_id`, `ticket_owed` and `cmd_ticket_step` on `main`).

A step is written once, after the tracker took it; `assigned` is written before the add, with
the login, so that a removal reads whom Lem added even when the session is cut off after the add.
"""

import re
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.records.tickets import Ticket, TicketStep

if TYPE_CHECKING:
    from lem.records.base import Moment
    from lem.records.task import Task
    from lem.records.tickets import TicketAct, Tracker

ASSIGNED = "assigned"
# A Linear ticket's id (MBZ-12), a GitHub issue's number (42, #42, #042), a repository of
# GitHub (OWNER/REPO), and a login of GitHub.
LINEAR = re.compile(r"[A-Za-z][A-Za-z0-9]*-[0-9]+")
ISSUE = re.compile(r"#?([0-9]+)")
REPOSITORY = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?/[A-Za-z0-9._-]+")
LOGIN = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?")


def ticket_id(kind: Tracker | None, given: str) -> str:
    """The id of a ticket as the task keeps it: a Linear id in upper case, an issue's number
    after `#`. A project with no tracker takes no ticket: nothing would act on it."""
    if kind is None:
        raise Refusal(
            "no-tracker",
            f"--ticket {given!r} names a tracker's ticket, and .lem/settings.toml has no "
            "[tracker]",
            'add the table with its kind (kind = "linear" or kind = "github"), or open '
            "the task with --ask alone",
        )
    if kind == "github":
        found = ISSUE.fullmatch(given)
        if found is None or int(found[1]) == 0:
            raise Refusal(
                "ticket",
                f"--ticket {given!r} is not an issue's number: the tracker is github",
                "give the issue's number, as 42 or #42",
            )
        return f"#{int(found[1])}"
    if LINEAR.fullmatch(given) is None:
        raise Refusal(
            "ticket",
            f"--ticket {given!r} is not a ticket's id: the tracker is {kind}",
            "give the ticket's id, as MBZ-12",
        )
    return given.upper()


def repository(kind: Tracker, repo: str | None) -> str | None:
    """The repository of a GitHub issue, which the task keeps; refused for another tracker,
    and missing or of another form for GitHub."""
    if kind != "github":
        if repo is not None:
            raise Refusal(
                "ticket-repo",
                f"--ticket-repo names a GitHub issue's repository, and the tracker is {kind}",
                "leave --ticket-repo out",
            )
        return None
    if repo is None or REPOSITORY.fullmatch(repo) is None:
        raise Refusal(
            "ticket-repo",
            f"an issue of GitHub keeps the repository it was read from, not {repo!r}",
            "give it as --ticket-repo OWNER/REPO, from the address lem issue read gave",
        )
    return repo


def owed(task: Task, held_by: str | None) -> tuple[TicketAct, ...]:
    """The steps the ticket still waits for now that its task ended; nothing while it runs,
    with no ticket, or when another task holds the ticket (a resume went on from this one):
    a drop comment would tell the readers that work they still get was dropped."""
    ticket = task.ticket
    if ticket is None or held_by is not None:
        return ()
    taken = {step.act for step in ticket.steps}
    wanted: tuple[TicketAct, ...] = ()
    if task.status == "landed":
        wanted = ("commented", "landed")
    elif task.status in {"dropped", "answered"}:
        unassign: tuple[TicketAct, ...] = ("unassigned",) if ASSIGNED in taken else ()
        wanted = (task.status, *unassign)
    return tuple(act for act in wanted if act not in taken)


def step_refusal(ticket: Ticket, act: TicketAct, login: str | None) -> str | None:
    """Why `act` may not be written on `ticket`, or None."""
    taken = {step.act for step in ticket.steps}
    if (act == ASSIGNED) != (login is not None):
        return "--login goes with the step assigned, and the step assigned needs it"
    if login is not None and LOGIN.fullmatch(login) is None:
        return f"--login {login!r} is not a login of GitHub"
    if act in taken:
        return f"the step {act} is written down for {ticket.id} already: it was done"
    if act == "unassigned" and ASSIGNED not in taken:
        return f"no step assigned is written down for {ticket.id}: Lem added nobody"
    return None


def stepped(ticket: Ticket, act: TicketAct, login: str | None, now: Moment) -> Ticket:
    """The ticket with the step `act` written down; refused when it was done already, or
    when its login does not fit it."""
    refused = step_refusal(ticket, act, login)
    if refused is not None:
        raise Refusal(
            "ticket-step",
            refused,
            "read the task's ticket steps (lem task show SLUG), and do only what it owes",
        )
    step = TicketStep(act=act, at=now, login=login)
    return replace(ticket, steps=(*ticket.steps, step))


def assignee(ticket: Ticket) -> str | None:
    """The login Lem set out to add as the issue's assignee, or None."""
    return next((step.login for step in ticket.steps if step.act == ASSIGNED), None)


def of(task: Task) -> Ticket:
    """The ticket of `task`; refused for a task that came from none."""
    if task.ticket is None:
        raise Refusal(
            "no-ticket",
            f"the task {task.slug} came from no ticket",
            "a step of the tracker is for a task opened with --ticket",
        )
    return task.ticket
