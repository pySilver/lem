"""The criteria a part takes from its feature (`docs/plans/2026-11-27-a-feature-in-parts.md`,
"The criteria of a part").

A part's criteria are its heading's, numbered from 1, with the feature's approval and the
personas' read copied onto it with the part's own mark, as a resume carries a dropped task's
criteria in one record (`model/task/resumes.py breaker_task`). So the landing of a part finds a
read on record (`model/landing/propose_criteria.py unread`) of the criteria it holds
(`app/landing/pr_unread.py`), and needs no second read and no second yes. A read of other texts
than the approved ones keeps its own mark, so a part shows the change that read missed, as its
feature would. The owner's skip of the read goes with his approval in the same way.
"""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.model.criteria import digest
from lem.model.landing import propose_criteria
from lem.model.task import parts
from lem.records.criteria import Criteria

if TYPE_CHECKING:
    from lem.records.approvals import Approval, PersonaRead
    from lem.records.criterion import Criterion
    from lem.records.task import Task


def numbered(criteria: tuple[Criterion, ...]) -> tuple[Criterion, ...]:
    """A part's criteria, numbered from 1: the whole set of its own task, under no heading."""
    return tuple(
        replace(criterion, number=number, part=None)
        for number, criterion in enumerate(criteria, start=1)
    )


def read_of(
    read: PersonaRead | None, approval: Approval, mark: str
) -> tuple[PersonaRead, ...]:
    """The feature's newest read as the part keeps it: with the part's mark when it read the
    approved texts, else with its own. Its counts stay those of the feature's criteria, which
    nobody split by part, and the part's pull request says whose they are
    (`app/landing/pr_read.py`)."""
    if read is None:
        return ()
    digest_kept = mark if read.digest == approval.digest else read.digest
    return (replace(read, digest=digest_kept, changes=0),)


def skipped(task: Task, criteria: Criteria) -> Criteria:
    """The part's criteria with the owner's skip of the read, when his approval made it
    count for the feature."""
    kept = task.criteria
    if kept.skip != "yes" or kept.skip_approval is None:
        return criteria
    return replace(criteria, skip="yes", skip_at=kept.skip_at, skip_approval=1)


def carried(
    feature: Task, approval: Approval, criteria: tuple[Criterion, ...]
) -> Criteria:
    """What the part knows of its criteria: the heading's criteria, the feature's approval as
    its first, and the feature's read or the owner's skip of it. The feature's wait for his
    yes stays the feature's: the part's pull request names the approval as the feature's
    (`app/landing/pr_approval.py`)."""
    own = numbered(criteria)
    mark = digest.of_texts(approval.size, own)
    copy = replace(
        approval, number=1, digest=mark, criteria=own, how=None, replaces=None
    )
    made = Criteria(
        size=approval.size,
        why=approval.why,
        criteria=own,
        digest=digest.of_tests(approval.size, own),
        approvals=(copy,),
        reads=read_of(propose_criteria.newest(feature), approval, mark),
    )
    return skipped(feature, made)


def marks(feature: str, approval: Approval) -> dict[str, str]:
    """The mark each part of the approved criteria takes at the split, by the part's slug."""
    found = parts.parts_of(feature, approval.criteria)
    return {
        part.slug: digest.of_texts(approval.size, numbered(part.criteria))
        for part in found
    }
