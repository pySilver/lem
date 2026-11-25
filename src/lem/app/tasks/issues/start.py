"""`lem issue start SLUG`: the build of the task started. An issue with no assignee gets the
person signed in to gh; an issue with one keeps its assignees.

`assigned LOGIN` is written down before the add, so that a session cut off after the add leaves
a record whose removal reads the assignees first; a failed add is written down as `unassigned`,
and the owner is told why. A resumed task takes over the assignee its dropped task added, so that
its own end removes it.
"""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.tasks.issues import guard, status
from lem.app.tasks.issues.results import enveloped
from lem.model.task import claim, tickets

if TYPE_CHECKING:
    import msgspec

    from lem.adapters.tracker_gh_facts import Issue
    from lem.app.tasks.issues.run import Run
    from lem.app.wiring import Ports
    from lem.kernel.envelope import Envelope
    from lem.records.task import Task
    from lem.store.places import Workspace

type Assigned = tuple[Issue, str | None]

STEP = "start"


def from_task(run: Run) -> Task | None:
    """The task this one went on from, when it went on from one."""
    slug = run.record.task.resumed_from
    if slug is None:
        return None
    went = (other.task for other in run.every if other.task.slug == slug)
    return next(went, None)


def carried(run: Run) -> str | None:
    """The assignee Lem added for the task this one went on from, with the same issue, and did
    not remove."""
    own = tickets.of(run.record.task)
    before = from_task(run)
    if before is None or not claim.same(before.ticket, own):
        return None
    ticket = tickets.of(before)
    acts = {step.act for step in ticket.steps}
    if "unassigned" in acts:
        return None
    return tickets.assignee(ticket)


def added(run: Run, issue: Issue, login: str) -> Assigned:
    """The add of `login`: the issue with it, or the line that says why gh refused it, with
    the step undone."""
    refused = run.issues.assign(run.repo, run.number, login)
    if refused is None:
        run.did.append(f"added the assignee {login}")
        return replace(issue, assignees=(*issue.assignees, login)), None
    run.write("unassigned")
    return issue, (
        f"gh could not make {login} the assignee of {run.named} ({refused}): the build "
        "goes on with no assignee there"
    )


def others(run: Run, issue: Issue) -> str | None:
    """The line for an issue that has assignees: who, when one is not the person signed in."""
    me = run.issues.who()
    names = status.others_than(issue.assignees, me)
    if not names:
        return None
    listed = ", ".join(names)
    return (
        f"{run.named} is assigned to {listed}: Lem added nobody, and the build goes on"
    )


def assigned(run: Run, issue: Issue) -> Assigned:
    """The assignee of the start, and the line for the owner, if any."""
    if "assigned" in run.acts:
        # a start cut off after its record: the add, only while the issue has nobody
        if "unassigned" in run.acts or issue.assignees:
            return issue, None
        login = tickets.assignee(tickets.of(run.record.task)) or ""
        return added(run, issue, login)
    before = carried(run)
    if before and status.others_than(issue.assignees, before) != issue.assignees:
        run.write("assigned", before)
        return issue, None
    if issue.assignees:
        return issue, others(run, issue)
    login = run.issues.who()
    run.write("assigned", login)
    return added(run, issue, login)


def start(ports: Ports, where: Workspace, slug: str) -> Envelope | msgspec.Struct:
    """The start's step on the task's issue; a second start writes nothing."""
    run = guard.run_of(ports, where, slug, STEP)
    if "started" in run.acts:
        return run.stepped(STEP, None)
    issue = run.issues.issue(run.repo, run.number)
    issue, say = assigned(run, issue)
    run.write("started")
    return enveloped(run.stepped(STEP, issue), say)
