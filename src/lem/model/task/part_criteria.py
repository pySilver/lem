"""The check of a split's criteria against the feature's (`docs/plans/2026-11-27-a-feature-in-
parts.md`, "The criteria of a part"): the file must be the feature's newest approval word for
word, each criterion's text and case and the heading it is under, on the standard track, and the
personas read it or the owner skipped the read. What a part then takes of it is
`part_carry.py`'s.
"""

from itertools import zip_longest
from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.model.criteria import digest
from lem.model.landing import propose_criteria
from lem.model.task import carried, part_carry

if TYPE_CHECKING:
    from lem.model.criteria.read import Sheet
    from lem.records.approvals import Approval
    from lem.records.criterion import Criterion
    from lem.records.record import Record
    from lem.records.task import Task

CODE = "split-differs"


def heading(criterion: Criterion) -> str:
    """The heading a criterion is under, as the owner's page shows it."""
    return criterion.part or "The whole feature"


def unlike(number: int, want: Criterion | None, have: Criterion | None) -> str | None:
    """How criterion `number` of the file, `have`, is not the approved one, `want`, or
    None."""
    if want is None or have is None:
        more = "the file" if want is None else "the approval"
        return f"{more} has criterion {number}, and the other has none"
    said, approved = digest.whole(have), digest.whole(want)
    if not digest.same(approved, said):
        return f"criterion {number} says {said!r}, and the owner approved {approved!r}"
    if want.part != have.part:
        return (
            f"criterion {number} is under {heading(have)!r}, and the owner approved it "
            f"under {heading(want)!r}"
        )
    return None


def difference(approval: Approval, sheet: Sheet) -> str | None:
    """The first way the file is not the approved criteria, said, or None. Its size is the
    approval's: a file of Size: small holds one criterion, which is no split."""
    pairs = enumerate(zip_longest(approval.criteria, sheet.criteria), start=1)
    found = (unlike(number, *pair) for number, pair in pairs)
    return next((said for said in found if said is not None), None)


def newest_of(task: Task) -> Approval:
    """The feature's newest approval, of the standard track; refused when there is none."""
    slug = task.slug
    approvals = task.criteria.approvals
    if not approvals:
        raise Refusal(
            CODE,
            f"nobody approved the criteria of {slug}, and a split copies the owner's yes",
            f"his yes comes first: lem criteria approve {slug} --file FILE",
        )
    if approvals[-1].size == "small":
        raise Refusal(
            CODE,
            f"{slug} takes the fast track, and a feature in parts takes the standard track",
            "a change that one criterion holds is one task, with no parts",
        )
    return approvals[-1]


def approval_of(record: Record, sheet: Sheet) -> Approval:
    """The feature's newest approval, when the file is its text word for word and the
    personas read it or the owner skipped the read; refused when not."""
    slug = record.task.slug
    newest = newest_of(record.task)
    said = difference(newest, sheet)
    if said is not None:
        raise Refusal(
            CODE,
            f"the file is not the criteria of {slug} the owner approved: {said}",
            f"split the text of approval {newest.number}, word for word; a change of it is "
            f"his yes again first: lem criteria approve {slug} --file FILE",
        )
    unread = propose_criteria.unread(record)
    if unread is not None:
        raise unread
    return newest


def other_than(every: tuple[Record, ...], feature: Task, newest: Approval) -> list[str]:
    """The parts of `feature` whose criteria, as they took them at the split, are not the
    ones `newest` holds under their heading: other words, or no such part any more. An
    approval of the same texts again is no change (`model/criteria/contract.py`)."""
    marks = part_carry.marks(feature.slug, newest)
    found: list[str] = []
    for record in every:
        kept = carried.approval(record)
        if kept is None or record.task.part_of != feature.slug:
            continue
        if marks.get(record.task.slug) != kept.digest:
            found.append(record.task.slug)
    return found


def stale(every: tuple[Record, ...], feature: Task) -> None:
    """Refuse a split again over parts that took another approval than the feature's newest:
    a change after the split goes into each part, never into a part made again."""
    approvals = feature.criteria.approvals
    if not approvals:
        return
    newest = approvals[-1]
    names = ", ".join(sorted(other_than(every, feature, newest)))
    if not names:
        return
    raise Refusal(
        "split-moved",
        f"{names} took the criteria of {feature.slug} at the split, and the owner's newest "
        f"approval of them, {newest.number}, words them otherwise or has no such part: a "
        "split runs once",
        "a change of a part's criteria is the part's own: lem criteria change PART --file "
        "FILE, then his yes, lem criteria approve PART --file FILE; a new part is lem task "
        f"open SLUG --part-of {feature.slug}; a part he no longer wants, he drops with "
        "/lem drop PART",
    )
