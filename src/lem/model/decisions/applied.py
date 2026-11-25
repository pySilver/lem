"""The criteria a change of the build gives: the approved ones with each recorded change applied
in order, each checked against the text it names (`decisions.applied` on `main`). Texts are
compared with each run of spaces as one, as a criterion written over two lines reads; they are
kept as typed, so a wrong record never enters."""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.model.criteria import digest

if TYPE_CHECKING:
    from lem.records.approvals import Approval
    from lem.records.decisions import CriterionChanged

CODE = "criterion-change"
STAND = "lem decisions changes SLUG gives the criteria as they stand"


def applied(criteria: tuple[str, ...], change: CriterionChanged) -> tuple[str, ...]:
    """The criteria after one change; a change whose criterion is not the text it names, or
    whose number is not among them, is refused."""
    number, found = change.criterion, list(criteria)
    last = len(found) + int(change.how == "added")
    if not 1 <= number <= last:
        raise Refusal(
            CODE,
            f"there is no criterion {number}: the criteria are 1 to {len(found)} after "
            "every earlier change",
            STAND,
        )
    if change.how == "added":
        found.insert(number - 1, change.now or "")
        return tuple(found)
    was = found[number - 1]
    if not digest.same(was, change.was or ""):
        raise Refusal(
            CODE,
            f"criterion {number} is {was!r} after every earlier change, and --was says "
            f"{change.was!r}",
            STAND,
        )
    if change.how == "changed":
        found[number - 1] = change.now or ""
    else:
        found.pop(number - 1)
    return tuple(found)


def expected_of(
    approval: Approval, changes: tuple[CriterionChanged, ...]
) -> tuple[str, ...]:
    """The criteria of `approval` with `changes` applied in order."""
    expected = tuple(digest.whole(one) for one in approval.criteria)
    for change in changes:
        expected = applied(expected, change)
    return expected
