"""The criteria before a change of the owner's note and after it, paired by their text and not
by their number (`criteria.pairs` on `main`).

A text that stayed is not shown; a run of N criteria replaced by N is N changed pairs, one by one
in order, each with its number before and after; any other run shows its criteria removed, with
the number before, and added, with the number after. So the removal of criterion 2 of three shows
criterion 2 removed, and criterion 3 kept as the new 2.
"""

import difflib
from typing import Literal

from lem.model.criteria import digest
from lem.records.criteria import Pair
from lem.records.criterion import Criterion

EQUAL = "equal"

type Criteria = tuple[Criterion, ...]
type Side = Literal["removed", "added"]
# A run of the criteria before that a change replaced, and what replaced it.
type Run = tuple[Criteria, Criteria]


def shown(criterion: Criterion) -> Criterion:
    """A criterion as a pair shows it: its number, its sentence and its case."""
    return Criterion(number=criterion.number, text=criterion.text, case=criterion.case)


def one_side(change: Side, criterion: Criterion) -> Pair:
    """A criterion that a change removed, or added."""
    if change == "removed":
        return Pair(change=change, before=shown(criterion))
    return Pair(change=change, after=shown(criterion))


def changed(old: Criterion, new: Criterion) -> Pair:
    """One criterion changed, with its text before and after."""
    return Pair(change="changed", before=shown(old), after=shown(new))


def run_of(run: Run) -> tuple[Pair, ...]:
    """The pairs of one run that changed: changed one by one when the counts match, else
    removed and then added."""
    before, after = run
    if len(before) == len(after):
        paired = zip(before, after, strict=True)
        return tuple(changed(*both) for both in paired)
    removed = tuple(one_side("removed", old) for old in before)
    return removed + tuple(one_side("added", new) for new in after)


def cut(spans: list[int], before: Criteria, after: Criteria) -> Run:
    """The run an opcode's spans name."""
    old_from, old_to, new_from, new_to = spans
    return before[old_from:old_to], after[new_from:new_to]


def runs(before: Criteria, after: Criteria) -> list[Run]:
    """The runs of criteria a change replaced, each with what replaced it."""
    texts = (digest.flat(before), digest.flat(after))
    matcher = difflib.SequenceMatcher(None, *texts, autojunk=False)
    found: list[Run] = []
    for tag, *spans in matcher.get_opcodes():
        if tag != EQUAL:
            found.append(cut(spans, before, after))
    return found


def pairs(before: Criteria, after: Criteria) -> tuple[Pair, ...]:
    """The pairs of a change from the criteria `before` to the criteria `after`."""
    return tuple(pair for run in runs(before, after) for pair in run_of(run))
