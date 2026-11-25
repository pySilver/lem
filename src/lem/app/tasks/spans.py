"""`lem task span`: the start or the end of one span of a task's work, written as it happens,
so that the time card has exact moments (the owner's pick of 2026-11-17)."""

from functools import partial
from typing import TYPE_CHECKING

from lem.app.tasks import release
from lem.kernel import clock
from lem.model.task import spans
from lem.records.base import Frozen, Moment
from lem.store import tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.model.task.span_forms import Given


class Marked(Frozen, frozen=True, kw_only=True):
    """The mark written: the task, the span, its edge, its job, and the moment."""

    slug: str
    name: str
    edge: str
    job: str | None = None
    at: Moment


def marked(state: Path, slug: str, given: Given) -> Marked:
    """Write the start or the end of the span `given` of the task `slug`, now."""
    record = release.checked(state, slug)
    now = clock.now()
    tasks.update(
        state, slug, partial(spans.marked, given=given, now=now), record.revision
    )
    return Marked(
        slug=slug,
        name=given.name,
        edge=given.edge,
        job=spans.job_of(given),
        at=now,
    )
