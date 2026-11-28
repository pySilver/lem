"""The owner's drop of a feature (`docs/plans/2026-11-27-a-feature-in-parts.md`, "The drop"):
each of its parts that has not ended first, each through `drop.dropped` under its own step lock,
then the feature. As for any drop, each open pull request stays open and each branch keeps its
commits. The line for the owner names each open pull request and the one command that deletes
the feature's branch on origin, which Lem never runs (`model/task/feature_drop.py`). The ticket's
"drop" runs as for any dropped task, and the ticket stays open.

A part's drop that is refused stops the feature's: the parts dropped stay dropped, and the drop
run again goes on from there. A task with no parts is dropped by `drop.dropped` alone.
"""

from typing import TYPE_CHECKING

import msgspec

from lem.app.tasks import release
from lem.app.tasks.drop import DROPPED, dropped
from lem.kernel.envelope import Envelope
from lem.model.task import claim, feature_drop, feature_parts, table
from lem.store import places, tasks

if TYPE_CHECKING:
    from lem.app.wiring import Ports
    from lem.records.task import Task


def pull_of(where: places.Workspace, slug: str) -> str | None:
    """The address of the task's pull request as its record holds it now, or None."""
    landing = tasks.read(where.state, slug).landing
    pull = landing.pull if landing else None
    return pull.url if pull else None


def parts_named(where: places.Workspace, task: Task) -> tuple[Task, ...]:
    """The parts of the task, a feature. A task whose `after` is empty has none, and no record
    is read for it: a part goes into its feature's `after` before its record is published, and
    a resumed part goes on from a part that did."""
    if not task.after:
        return ()
    return feature_parts.parts_of(
        task, (record.task for record in tasks.every(where.state))
    )


def parts_dropped(
    where: places.Workspace,
    feature: str,
    found: tuple[Task, ...],
    line: str,
    given: Ports | None,
) -> tuple[feature_drop.PartDropped, ...]:
    """Drop each part in `found` that has not ended, in their order, each under its own step
    lock, with the owner's reason `line`."""
    reason = feature_drop.part_line(feature, line)
    return tuple(
        feature_drop.PartDropped(
            slug=part.slug,
            was=dropped(where, part.slug, reason, given).was,
            pull=pull_of(where, part.slug),
        )
        for part in found
        if part.status not in claim.ENDED
    )


def enveloped(
    where: places.Workspace,
    feature: Task,
    moved: table.Moved,
    parts: tuple[feature_drop.PartDropped, ...],
) -> Envelope:
    """The drop of the feature as printed, with its line for the owner."""
    done = feature_drop.FeatureDropped(
        slug=feature.slug,
        was=moved.was,
        status=moved.status,
        parts=parts,
        pull=pull_of(where, feature.slug),
        branch=feature.branch,
        delete=feature_drop.delete_of(feature.branch),
    )
    return Envelope(
        ok=True,
        outcome=msgspec.Raw(msgspec.json.encode(done)),
        say=feature_drop.said(done),
    )


def feature_dropped(
    where: places.Workspace, slug: str, line: str, given: Ports | None = None
) -> table.Moved | Envelope:
    """Drop the task `slug`; a feature with each of its parts that has not ended first."""
    before = release.checked(where.state, slug, ends=True)
    refused = table.refusal(before.task, DROPPED, None)
    if refused is not None:
        raise refused
    found = parts_named(where, before.task)
    if not found:
        return dropped(where, slug, line, given)
    parts = parts_dropped(where, slug, found, line, given)
    return enveloped(where, before.task, dropped(where, slug, line, given), parts)
