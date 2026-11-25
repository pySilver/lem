"""Records and worlds for the cases of the merge's end of the landing: an open pull request with
its read, the trees a merge is judged by, a moved base, and what the forge shows after a call."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.landing import green
from lem.model.landing.merge_asked import Asked
from lem.model.landing.reconcile import Trees
from lem.records.landing.merge import MergeIntent
from unit.landing.worlds import (
    BASE,
    MERGE,
    MOMENT,
    OPENED,
    READ,
    SEEN,
    TIP,
    TREE,
    task,
    world,
)

if TYPE_CHECKING:
    from lem.model.landing.world import World
    from lem.records.record import Record

# origin's base after a teammate's merge: another commit, another tree.
MOVED = "a" * 40
MOVED_TREE = "f" * 40
SUBJECT = "docs: the login works"
INTENT = MergeIntent(tip=TIP, by="merger", via="server", at=MOMENT)
BY_MERGER = Asked(by="merger", via="server", subject=SUBJECT)
BY_OWNER = Asked(by="owner", via="board", tip=TIP, subject=SUBJECT)
# The trees of a merge onto the checks' own base.
SAME = Trees(checks=TREE, parent=TREE)
DONE = replace(
    SEEN, state="merged", merge_commit=MERGE, merged_head=TIP, base_parent=BASE
)


def opened(**landing: object) -> Record:
    """An open task whose read says merge, with the landing's `landing` over it."""
    return task("open", **{**OPENED, "reads": (READ,), **landing})


def facing(**fields: object) -> World:
    """The world of an open pull request at the proposed tip, with `fields` over it."""
    return world(**{"pull": SEEN, "remote": TIP, **fields})


def moved(**fields: object) -> World:
    """The world after origin's base moved to another tree."""
    return facing(**{"base": MOVED, "base_tree": MOVED_TREE, **fields})


def code_of(found: object) -> str:
    """The code of a refusal; a case fails on anything else."""
    assert isinstance(found, Refusal), found
    return found.code


def alone(**landing: object) -> Record:
    """An open task whose criteria the owner did not approve (it ran without him): not green,
    with the proposal saying so as it was proposed."""
    record = opened(**landing)
    criteria = record.task.criteria
    approvals = tuple(replace(one, by="alone") for one in criteria.approvals)
    task = replace(record.task, criteria=replace(criteria, approvals=approvals))
    made = replace(record, task=task)
    reasons = green.reasons(made)
    proposed = replace(OPENED["proposed"], reasons=reasons, green=False)
    kept = made.landing
    assert kept is not None
    return replace(made, landing=replace(kept, proposed=proposed))
