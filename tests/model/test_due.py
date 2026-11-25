"""The due step over drawn records and worlds (`model/landing/phases.py`, `landing.md` B, C and
H 6): it is total and the same on each call, it names a step or a rest of the known set, a merge
names who merges, what the record alone decides is the same in every world, the rows of
`preparing` are taken in their order, an ended task goes only to its cleanup, and a step cut off
after its effect and before its record is due again or a later one is, never an earlier one."""

from typing import TYPE_CHECKING, get_args

from hypothesis import given, settings
from msgspec.structs import replace

from lem.model.landing import invariants, phases
from lem.model.landing.world import Due, Held, Rest, Verb
from lem.records.landing.record import Landing
from model.landings import (
    ENDED,
    LANDING,
    NEW,
    NEW_TREE,
    any_records,
    any_worlds,
    near_records,
    near_worlds,
    records,
    worlds,
)
from unit.landing.worlds import SEEN

if TYPE_CHECKING:
    from collections.abc import Callable

    from lem.model.landing.world import World
    from lem.records.record import Record

KNOWN = frozenset((*get_args(Verb.__value__), *get_args(Rest.__value__)))
# The steps and rests in the order a landing meets them: a step's effect never makes one
# before it due. `wait` comes after `merged`: an open request merged into another base waits
# for the owner.
ORDER = (
    "none",
    "start",
    "base",
    "polish",
    "checks",
    "read",
    "file",
    "propose",
    "merge-review",
    "merge",
    "merged",
    "wait",
    "clean",
    "done",
)


def unchanged(found: World) -> World:
    """A step whose effect is its record and the files it cites: the world stays."""
    return found


def rebased(found: World) -> World:
    """`base`'s rebase: a new tip on origin's base."""
    return replace(found, tip=NEW, tree=NEW_TREE, local=NEW, base_in_tip=True)


def pushed(found: World) -> World:
    """`propose`'s push and its pull request: origin's branch at the tip, and the request at
    it, the one on record edited or a new one on the branch."""
    pushed_to = replace(found, remote=found.tip, remote_in_tip=True)
    if found.tip is None:
        return pushed_to
    if found.pull is not None:
        return replace(pushed_to, pull=replace(found.pull, head=found.tip))
    return replace(pushed_to, candidates=(replace(SEEN, head=found.tip),))


def merged_on_forge(found: World) -> World:
    """`merge`'s call taken: the forge merged the request at the tip."""
    pull = found.pull or SEEN
    done = replace(
        pull,
        state="merged",
        merge_commit=NEW,
        merged_head=found.tip,
        base_parent=found.base,
    )
    return replace(found, pull=done)


def cleaned(found: World) -> World:
    """`clean`'s removal: no worktree, no local branch, no copy on the forge."""
    return replace(found, tip=None, tree=None, local=None, remote=None)


# The effect of each step on the world, before the step writes its record. `file` is not here:
# its commit of the items moves the tip, and the record that moves the checks with it
# (`items_after`) comes after, so a cut-off between them makes the checks due again, until the
# checks carry over commits that only add backlog items (`notes/land-review.md` item 11,
# `notes/land-checks.md` item 7).
EFFECTS: dict[str, Callable[[World], World]] = {
    "start": unchanged,
    "base": rebased,
    "polish": unchanged,
    "checks": unchanged,
    "read": unchanged,
    "propose": pushed,
    "merge-review": unchanged,
    "merge": merged_on_forge,
    "merged": unchanged,
    "clean": cleaned,
}


@LANDING
@given(any_records(), any_worlds())
def test_the_due_step_is_total_the_same_each_time_and_of_the_known_set(
    record: Record, world: World
) -> None:
    found = phases.due(record, world)
    assert found == phases.due(record, world)
    assert found.step in KNOWN
    assert found.why
    assert (found.by is not None) == (found.step == "merge")


@LANDING
@given(records(ENDED), worlds())
def test_an_ended_task_goes_only_to_the_merge_bookkeeping_and_its_cleanup(
    record: Record, world: World
) -> None:
    found = phases.due(record, world)
    assert found.step in {*invariants.AFTER_END, "done"}
    if found.step != "done":
        assert (
            invariants.ended(record.task.slug, record.task.status, found.step) is None
        )
    if record.task.status != "landed":
        assert found.step != "merged"


@LANDING
@given(records(("queued", "shaping", "building", "planned")), worlds())
def test_a_task_not_ready_to_land_has_no_step(record: Record, world: World) -> None:
    assert phases.due(record, world).step == "none"


@LANDING
@given(
    near_records(("landing", "landing", "landing", "ready"))
    | records(("ready", "landing")),
    near_worlds() | worlds(),
)
def test_in_preparing_every_row_before_the_due_one_holds(
    record: Record, world: World
) -> None:
    found = phases.due(record, world)
    rows = [rule(record, world) for rule in phases.PREPARING]
    landing = record.landing or Landing()
    pull = world.pull
    if landing.pull is not None and pull is not None and pull.state == "merged":
        assert found.step == "merged"
        return
    due = [row for row in rows if isinstance(row, Due)]
    if not due:
        assert found.step == "wait"
        return
    before = rows[: rows.index(due[0])]
    assert found == due[0]
    assert all(isinstance(row, Held) for row in before)


@settings(LANDING, max_examples=800)
@given(near_records() | records(), near_worlds() | worlds())
def test_a_step_cut_off_after_its_effect_is_due_again_or_a_later_one_is(
    record: Record, world: World
) -> None:
    found = phases.due(record, world)
    effect = EFFECTS.get(found.step)
    if effect is None:
        return
    again = phases.due(record, effect(world))
    assert ORDER.index(again.step) >= ORDER.index(found.step), (found, again)


@LANDING
@given(any_records(), any_worlds(), any_worlds())
def test_what_the_record_alone_decides_is_the_same_in_every_world(
    record: Record, one: World, other: World
) -> None:
    settled = phases.settled(record)
    landing = record.landing or Landing()
    lands = record.task.status in phases.LANDS and landing.phase in {
        "preparing",
        "open",
    }
    assert (settled is None) == lands
    if settled is not None:
        assert phases.due(record, one) == phases.due(record, other) == settled
