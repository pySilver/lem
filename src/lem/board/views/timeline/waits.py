"""The criteria's waits for the owner's yes (`time_of` on `main`): from the personas' read to his
approval after it. A yes he gave before the read was in, and a criterion Lem approved in his
name, cost him no wait."""

from typing import TYPE_CHECKING

from lem.board.views.timeline import shapes

if TYPE_CHECKING:
    from collections.abc import Iterator
    from datetime import datetime

    from lem.records.approvals import PersonaRead
    from lem.records.record import Record


def waited(record: Record) -> Iterator[shapes.Held]:
    """The criteria's waits for the owner's yes, from a read to his approval after it."""
    criteria = record.task.criteria
    since = None
    for approval in criteria.approvals:
        last = read_before(criteria.reads, since, approval.at)
        if approval.by == "owner" and last is not None and last.ended:
            yield shapes.Held(
                shapes.YOU,
                last.ended,
                approval.at,
                "The criteria waited for your yes",
                waited_sub(last),
            )
        since = approval.at


def read_before(
    reads: tuple[PersonaRead, ...], since: datetime | None, until: datetime
) -> PersonaRead | None:
    """The newest read that ended after `since` and before `until`."""
    ended = [one for one in reads if between(one.ended, since, until)]
    return ended[-1] if ended else None


def between(moment: datetime | None, since: datetime | None, until: datetime) -> bool:
    """Whether `moment` is after `since` (when there is one) and before `until`."""
    if moment is None or moment >= until:
        return False
    return since is None or moment > since


def waited_sub(last: PersonaRead) -> str:
    """The wait's line, with the doubt the read found."""
    doubt = " · the read found a doubt" if last.flagged or last.split else ""
    return f"from the personas’ read to your approval{doubt}"
