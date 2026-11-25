"""The change of the criteria from the owner's note, above the whole criteria that wait for his
yes again (`board_task.change_block` and `board_model.change_of` on `main`): his note, and each
changed criterion's text before beside its new text, a removed one with its text before and an
added one with its new text."""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.board.inputs.task.criteria import Change, Pair, Side
from lem.model.criteria import waits

if TYPE_CHECKING:
    from lem.records.criteria import Pair as Paired
    from lem.records.criterion import Criterion
    from lem.records.task import Task

EACH = (
    " Each changed criterion shows its text before beside its new text; the whole criteria "
    "follow."
)
# The sides of each kind of pair, as their labels say them.
SIDES = MappingProxyType(
    {
        "changed": (("before", "Before"), ("after", "Now")),
        "removed": (("before", "Removed"),),
        "added": (("after", "Added"),),
    }
)


def side_of(label: str, criterion: Criterion) -> Side:
    """One side of a pair: its label with the criterion's number, its sentence, its steps."""
    named = f"{label} · criterion {criterion.number}"
    return Side(label=named, text=criterion.text, steps=criterion.case)


def pair_of(paired: Paired) -> Pair:
    """A criterion changed, removed or added, with its sides."""
    sides = sides_of(paired)
    return Pair(change=paired.change, sides=tuple(sides))


def sides_of(paired: Paired) -> list[Side]:
    """Each side of a pair, before first."""
    shown = {"before": paired.before, "after": paired.after}
    sides: list[Side] = []
    for key, label in SIDES[paired.change]:
        one = shown[key]
        if one is not None:
            sides.append(side_of(label, one))
    return sides


def change_of(task: Task) -> Change | None:
    """The change from his note while the criteria wait for his yes again after it, or
    None."""
    hold = waits.hold_of(task)
    change = task.criteria.change
    if hold is None or hold.line != waits.CHANGED or change is None:
        return None
    note = f" “{change.words}”" if change.words else ""
    said = f"Lem changed them from your note{note}.{EACH}"
    pairs = tuple(map(pair_of, change.pairs))
    return Change(said=said, pairs=pairs)
