"""`lem issue drop SLUG` and `lem issue answer SLUG`: one comment (why the task was dropped, or
its answer and where), then the assignee Lem added goes, whoever is signed in to gh now. Every
other assignee stays, and the issue stays open: whether it closes is the owner's call."""

from typing import TYPE_CHECKING, Literal

from msgspec.structs import replace

from lem.app.tasks.issues import guard, status, words
from lem.app.tasks.issues.comment import commented
from lem.app.tasks.issues.results import enveloped
from lem.model.task import tickets

if TYPE_CHECKING:
    import msgspec

    from lem.adapters.tracker_gh_facts import Issue
    from lem.app.tasks.issues.run import Run
    from lem.app.wiring import Ports
    from lem.kernel.envelope import Envelope
    from lem.store.places import Workspace

type End = Literal["drop", "answer"]


def unassigned(run: Run, issue: Issue) -> Issue:
    """The issue with the assignee Lem added removed, when it is still there; the step is
    written down either way."""
    acts = run.acts
    if "assigned" not in acts or "unassigned" in acts:
        return issue
    login = tickets.assignee(tickets.of(run.record.task)) or ""
    kept = status.others_than(issue.assignees, login)
    if kept != issue.assignees:
        run.issues.unassign(run.repo, run.number, login)
        run.did.append(f"removed the assignee {login}")
        issue = replace(issue, assignees=kept)
    run.write("unassigned")
    return issue


def ended(
    ports: Ports, where: Workspace, slug: str, step: End
) -> Envelope | msgspec.Struct:
    """The end's comment and the removal of Lem's assignee on the task's issue."""
    run = guard.run_of(ports, where, slug, step)
    said = (
        words.dropped(run.record)
        if step == "drop"
        else words.answered(run.state, run.record)
    )
    commented(run, step, said)
    issue = unassigned(run, run.issues.issue(run.repo, run.number))
    say = (
        f"{run.named} is closed already, by someone else than Lem"
        if issue.state == "closed"
        else f"{run.named} stays open: whether it closes is the owner's call"
    )
    return enveloped(run.stepped(step, issue), say)
