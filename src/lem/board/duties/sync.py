"""A duty of the board server: the sync of a feature while it waits for its parts
(`docs/plans/2026-11-27-a-feature-in-parts.md`, "The sync").

A feature is a task that a part names in `Task.part_of`. For each feature that is `queued` with
no hold, whose turn has not come (the queue duty gives it its end, whose landing takes in the
base), and whose branch on origin does not hold origin's base, the feature's session gets the
wake `lem: NAME sync`, and with none alive a session opens, as for the turn of a queued task. It
wakes once for each commit of the base: the wake keeps that commit in `Wake.head`, and a base
commit that a `sync` wake names already is passed over. The session runs `lem task sync NAME`.

Origin is read as git last fetched it, as the merge duty reads it (`app/owner/merge_bases.py`):
each landing step fetches. With no feature on record, the duty makes no git call.
"""

from typing import TYPE_CHECKING

from lem.app.owner import releases
from lem.app.tasks import bases
from lem.board.duties import queue, wakes
from lem.store import survey

if TYPE_CHECKING:
    from collections.abc import Collection, Mapping

    from lem.app.sessions.acts import WakeWhy
    from lem.board.duties.context import Duty
    from lem.records.record import Record

WHY: WakeWhy = "sync"


def tick(duty: Duty) -> None:
    """Wake each feature whose branch on origin lacks origin's base, once for each base
    commit."""
    owed = waiting(duty)
    if not owed or not wakes.known(duty):
        return
    for record in owed:
        base = behind(duty, record)
        slug = record.task.slug
        if base is not None and not wakes.for_head(duty, slug, WHY, base):
            wakes.woken(duty, slug, WHY, base)


def waiting(duty: Duty) -> list[Record]:
    """The features that wait for their parts; none, with no git call, when no part names a
    feature."""
    records = releases.with_stops(survey.records(duty.state).readable)
    named = {record.task.part_of for record in records} - {None}
    if not named:
        return []
    statuses = {record.task.slug: record.task.status for record in records}
    return [record for record in records if waits(record, named, statuses)]


def waits(
    record: Record, named: Collection[str | None], statuses: Mapping[str, str]
) -> bool:
    """Whether the task is a feature that waits for its parts: queued on its branch, with no
    hold, and its turn not come."""
    task = record.task
    if task.slug not in named or task.branch is None:
        return False
    if task.status != "queued" or task.hold is not None:
        return False
    return not queue.turn(record, statuses)


def behind(duty: Duty, record: Record) -> str | None:
    """Origin's base commit, when origin's branch of the feature does not hold it; None when
    it does, or when origin has either branch not."""
    git, checkout = duty.here.ports.git, duty.checkout
    base = git.remote_head(checkout, bases.chosen(git, duty.here.where, record))
    tip = git.remote_head(checkout, record.task.branch or "")
    if base is None or tip is None or git.is_ancestor(checkout, base, tip):
        return None
    return base
