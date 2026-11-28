"""The guards of `lem issue tick NAME` before any write (`tick.py`): a project whose tracker is
GitHub's, a task read through the release stop that is a feature (a part names it) and no part
itself, an issue of GitHub that it holds itself, of origin's repository. Any status passes: the
tick runs while the feature waits for its parts, and after it landed.
"""

from typing import TYPE_CHECKING

from lem.app.tasks import release
from lem.app.tasks.issues import facts, guard, status
from lem.app.tasks.issues.run import Run
from lem.model.task import feature_parts, parts_comment
from lem.store import tasks

if TYPE_CHECKING:
    from lem.app.wiring import Ports
    from lem.records.record import Record
    from lem.store.places import Workspace


def feature_of(where: Workspace, slug: str) -> tuple[Record, tuple[Record, ...]]:
    """The record of the feature `slug` through the release stop, and every record; refused
    for a part, and for a task no part names."""
    record = release.checked(where.state, slug, ends=True)
    every = tasks.every(where.state)
    parts = feature_parts.parts_of(record.task, (one.task for one in every))
    refused = parts_comment.refusal(record.task, parts)
    if refused is not None:
        raise refused
    return record, every


def feature_run(ports: Ports, where: Workspace, slug: str) -> Run:
    """The step on the issue of the feature `slug`, once every guard passed."""
    status.github(where.checkout)
    record, every = feature_of(where, slug)
    ticket = guard.held(record.task, guard.issue_of(record.task), every)
    issues = facts.of(ports)
    return Run(
        state=where.state,
        record=record,
        every=every,
        issues=issues,
        repo=guard.repository(issues, ticket, slug),
        number=int(ticket.id.removeprefix("#")),
    )
