"""The resume of a dropped task: a new task that goes on from it (`project.cmd_resume` and
`resume_as_request` on `main`).

A task dropped with a breaker that waits goes on from its handoff, its records and its branch,
held by that breaker, on the release the dropped one began on. A task the release stop dropped
goes on as a new request on this release, from the notes it left and its branch, and takes its
shape anew. The dropped task stays dropped.
"""

from functools import partial
from typing import TYPE_CHECKING

from lem.app.tasks import carry, ports, worktree
from lem.app.tasks.park import Resumed
from lem.kernel import clock, release
from lem.kernel.errors import Refusal
from lem.model.task import claim, ending, resumes
from lem.records.record import Record
from lem.store import places, tasks, workspace

if TYPE_CHECKING:
    from lem.records.decisions import Breaker
    from lem.records.task import Task
    from lem.records.tickets import Tracker


def old_branch(where: places.Workspace, record: Record) -> str | None:
    """The dropped task's branch, when git still has it."""
    named = record.task.branch
    if named is None:
        return None
    tip = ports.bound(where).git.tip(where.checkout, f"refs/heads/{named}")
    return None if tip is None else named


def opened(where: places.Workspace, made: Record, kind: Tracker | None) -> Record:
    """Claim and write the new task's record, under the workspace lock."""
    return workspace.claimed(where.state, partial(claim.claimed, made, kind=kind))


def placed(
    where: places.Workspace, made: Record, taken: carry.Taken, document: str
) -> None:
    """Write the carried files into the new task's folder, and its brief with its own
    lines and the line that names the breaker's `document`."""
    target = places.task_folder(where.state, made.task.slug)
    carry.written(target, taken.files)
    if taken.brief is None:
        return
    origin = made.task.resumed_from
    own = {
        "task": made.task.slug,
        "branch": made.task.branch or "",
        "worktree": str(worktree.where.worktree(where, made.task.slug)),
        "task directory": str(target),
    }
    line = f"resumed from: {origin}; read handoff.md and {document} first"
    brief = carry.rebriefed(taken.brief, own, line)
    (target / carry.BRIEF).write_text(brief, encoding="utf-8")


def gathered(where: places.Workspace, record: Record) -> tuple[carry.Taken, str]:
    """The files the resume carries, read whole, and the new task's slug; refused when
    retention folded the dropped task while they were read (it removes the files after the
    fold), so no successor goes on from half its files."""
    slug, ask = record.task.slug, record.task.ask
    taken = carry.taken(places.task_folder(where.state, slug))
    if ending.summarized(tasks.read(where.state, slug)):
        raise Refusal(
            "resume",
            f"{slug} was folded into its summary while its files were read, so they are "
            "not whole",
            f"new work for it is a new ask: /lem {ask}",
        )
    return taken, resumes.next_slug(slug, tasks.every(where.state))


def as_breaker(
    where: places.Workspace, record: Record, breaker: Breaker, kind: Tracker | None
) -> Resumed:
    """The new task of a task dropped with `breaker` waiting."""
    taken, new = gathered(where, record)
    task = resumes.breaker_task(record.task, new, breaker.id, clock.now())
    made = opened(where, Record(release=record.release, task=task), kind)
    placed(where, made, taken, breaker.document)
    start = old_branch(where, record)
    worktree.made(ports.bound(where), where, made, (task.branch, start))
    return said(made.task, "dropped", start, breaker.id)


def as_request(
    where: places.Workspace, record: Record, kind: Tracker | None
) -> Resumed:
    """The new request of a task the release stop dropped."""
    taken, new = gathered(where, record)
    start = old_branch(where, record)
    task = resumes.request_task(record.task, new, start, clock.now())
    made = opened(where, Record(release=release.running(), task=task), kind)
    placed(where, made, carry.Taken(files=taken.files, brief=None), "")
    if start is None:
        return said(made.task, "request", None, None, record.task.branch)
    worktree.made(ports.bound(where), where, made, (task.branch, start))
    return said(made.task, "request", start, None)


def said(
    task: Task,
    how: str,
    start: str | None,
    breaker: int | None,
    missing: str | None = None,
) -> Resumed:
    """What a resume of a dropped task prints, with the line the owner reads."""
    old = task.resumed_from
    source = "the base branch" if start is None else f"the commits of {start}"
    goes = (
        f"is a new request on this release, from the notes {old} left and {source}: its "
        "session takes its shape anew"
        if breaker is None
        else f"goes on from its handoff and {source}"
    )
    return Resumed(
        task=task.slug,
        resumed=how,
        origin=old,
        status=task.status,
        branch=task.branch,
        breaker=breaker,
        missing=missing,
        says=f"{old} stays dropped; {task.slug} {goes}",
    )
