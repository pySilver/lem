"""The guards of a step of `lem issue` on a task, before any write: a project whose tracker is
GitHub's, a task read through the release stop, a task of an issue of GitHub, in the status the
step belongs to, that holds its issue itself, and whose issue is of origin's repository."""

from typing import TYPE_CHECKING

from lem.app.tasks import release
from lem.app.tasks.issues import facts, status
from lem.app.tasks.issues.run import Run
from lem.kernel.errors import Refusal
from lem.model.task import claim, tickets
from lem.store import tasks

if TYPE_CHECKING:
    from lem.app.wiring import Ports
    from lem.records.record import Record
    from lem.records.task import Task
    from lem.records.tickets import Ticket
    from lem.store.places import Workspace


def issue_of(task: Task) -> Ticket:
    """The task's ticket, once it is an issue of a repository of GitHub."""
    ticket = tickets.of(task)
    if ticket.tracker != "github" or ticket.repo is None:
        raise Refusal(
            "not-an-issue",
            f"the task {task.slug} keeps the ticket {ticket.id} with no repository of "
            "GitHub: it is no issue lem issue can write to",
            f"the owner writes to {ticket.id} by hand",
        )
    return ticket


def ticket_of(task: Task, step: status.IssueStep, every: tuple[Record, ...]) -> Ticket:
    """The task's issue, once its tracker, its status and its holder are checked."""
    ticket = issue_of(task)
    refused = status.status_refusal(task, step, ticket.id)
    if refused is not None:
        raise refused
    return held(task, ticket, every)


def held(task: Task, ticket: Ticket, every: tuple[Record, ...]) -> Ticket:
    """The task's issue, unless a task that went on from it holds the issue now."""
    holder = claim.holder(task, every)
    if holder is not None:
        raise Refusal(
            "issue-held",
            f"issue {ticket.id} is held by the task {holder} now, which went on from "
            f"{task.slug}: {task.slug} owes the issue nothing",
            f"what the issue gets is {holder}'s to write: lem issue STEP {holder} when "
            "that task ends",
        )
    return ticket


def repository(issues: facts.Issues, ticket: Ticket, slug: str) -> str:
    """The issue's repository, when origin names it; refused when origin names another."""
    origin, repo = issues.origin(), ticket.repo or ""
    if status.same(origin, repo):
        return repo
    raise Refusal(
        "issue-origin",
        f"origin names {origin}, and the task {slug} came from issue {ticket.id} of "
        f"{repo}: Lem writes to an issue of origin's repository only",
        f"set origin back (git remote set-url origin https://github.com/{repo}.git) and "
        f"run this again, or the owner writes to issue {ticket.id} of {repo} by hand",
    )


def run_of(ports: Ports, where: Workspace, slug: str, step: status.IssueStep) -> Run:
    """The step `step` on the issue of the task `slug`, once every guard passed."""
    status.github(where.checkout)
    record = release.checked(where.state, slug, ends=step != "start")
    every = tasks.every(where.state)
    ticket = ticket_of(record.task, step, every)
    issues = facts.of(ports)
    return Run(
        state=where.state,
        record=record,
        every=every,
        issues=issues,
        repo=repository(issues, ticket, slug),
        number=int(ticket.id.removeprefix("#")),
    )
