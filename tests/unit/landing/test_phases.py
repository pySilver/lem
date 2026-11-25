"""The due step of a landing (`model/landing/phases.py`), derived from the record's evidence
and the world now (`landing.md` C): in `preparing` the first row that does not hold, in `open`
the reconcile, the forge's merge, a new round, the read and the merge, then the bookkeeping, the
cleanup and the end."""

from typing import TYPE_CHECKING

import pytest
from msgspec.structs import replace

from lem.model.landing import mergeread, phases
from lem.model.landing.world import Due, Rules
from lem.records.landing.merge import MergeAccepted, MergeIntent
from lem.records.landing.propose import MergeRead
from lem.records.landing.review import Finding
from lem.records.task import Shape
from unit.landing.worlds import (
    BASE,
    MERGED,
    MOMENT,
    OPENED,
    OTHER,
    PREPARED,
    READ,
    REVIEWED,
    SEEN,
    TIP,
    TREE,
    task,
    world,
)

if TYPE_CHECKING:
    from lem.records.record import Record

MUST = Finding(
    id="r1.2", level="must-fix", where="a.py", title="no", what="it", against="over"
)


def step_of(due: Due) -> tuple[str, str | None]:
    return due.step, due.by


@pytest.mark.parametrize(
    ("record", "facts", "step"),
    [
        (task("building"), {}, "none"),
        (task("ready"), {}, "start"),
        (task(**{**PREPARED, "started": None}), {}, "start"),
        (task(**PREPARED), {"clean": False}, "start"),
        (task(**PREPARED), {"tip": None}, "start"),
        (task(**PREPARED), {"rules": Rules(base="main")}, "start"),
        (task(**PREPARED), {"rebasing": True}, "base"),
        (task(**PREPARED), {"base": OTHER}, "base"),
        (task(**PREPARED), {"remote": OTHER}, "base"),
        (task(**{**PREPARED, "based": None}), {}, "base"),
        (task(**{**PREPARED, "checked": None}), {}, "checks"),
        (task(**PREPARED), {"tip": OTHER}, "checks"),
        (task(**PREPARED), {"rules": Rules(base="main", commands=("make",))}, "checks"),
        (task(**{**PREPARED, "reviews": ()}), {}, "read"),
        (
            task(**{**PREPARED, "reviews": (replace(REVIEWED, findings=(MUST,)),)}),
            {},
            "read",
        ),
        (task(**{**PREPARED, "filed": ()}), {}, "file"),
        (task(**PREPARED), {}, "propose"),
        (task(**{**PREPARED, "pushed": TIP}), {"pull": SEEN, "remote": TIP}, "propose"),
    ],
)
def test_in_preparing_the_first_row_that_does_not_hold_is_due(
    record: Record, facts: dict[str, object], step: str
) -> None:
    assert phases.due(record, world(**facts)).step == step


def test_the_standard_track_has_its_polish_pass_before_the_checks() -> None:
    record = task(**{**PREPARED, "checked": None})
    full = replace(
        record,
        task=replace(record.task, shape=Shape(type="feat", why="w", track="full")),
    )
    assert phases.due(full, world()).step == "polish"


def test_a_red_run_on_this_tip_keeps_the_checks_due() -> None:
    red = replace(PREPARED["checked"], outcome="red")
    assert phases.due(task(**{**PREPARED, "checked": red}), world()).step == "checks"


def test_in_open_the_read_then_the_merge_by_whom_the_read_and_settings_say() -> None:
    opened = world(pull=SEEN, remote=TIP)
    assert step_of(phases.due(task("open", **OPENED), opened)) == ("merge-review", None)
    read = task("open", **{**OPENED, "reads": (READ,)})
    assert step_of(phases.due(read, opened)) == ("merge", "merger")
    call = task("open", **{**OPENED, "reads": (replace(READ, verdict="call"),)})
    assert step_of(phases.due(call, opened)) == ("merge", "owner")
    owner = world(
        pull=SEEN,
        remote=TIP,
        rules=Rules(base="main", land="owner", commands=("true",)),
    )
    assert step_of(phases.due(read, owner)) == ("merge", "owner")
    moved = world(pull=SEEN, remote=TIP, base=OTHER)
    assert phases.due(read, moved).step == "merge-review"


def test_in_open_an_intent_is_reconciled_first_and_a_forge_merge_is_bookkept() -> None:
    intent = MergeIntent(tip=TIP, by="merger", via="session", at=MOMENT)
    opened = world(pull=SEEN, remote=TIP)
    assert (
        phases.due(task("open", **{**OPENED, "intent": intent}), opened).step == "merge"
    )
    merged = world(pull=replace(SEEN, state="merged"), remote=TIP)
    assert phases.due(task("open", **OPENED), merged).step == "merged"
    queued = MergeAccepted(tip=TIP, at=MOMENT, queued="the merge queue")
    assert (
        phases.due(task("open", **{**OPENED, "accepted": queued}), opened).step
        == "merged"
    )
    assert (
        phases.due(task("open", **OPENED), world(pull=SEEN, tip=OTHER)).step == "start"
    )


def test_after_the_merge_its_bookkeeping_the_cleanup_and_the_end() -> None:
    merged = {**OPENED, "phase": "merged", "merged": MERGED}
    assert phases.due(task("open", **merged), world()).step == "merged"
    assert phases.due(task("landed", **merged), world()).step == "clean"
    ended = {**merged, "phase": "ended"}
    assert phases.due(task("landed", **ended), world()).step == "done"


def test_a_read_of_another_base_or_tip_is_not_usable_but_names_its_base() -> None:
    landing = task("open", **{**OPENED, "reads": (replace(READ, base=OTHER),)}).landing
    assert landing is not None
    assert mergeread.usable(landing, world()) is None
    assert mergeread.read_of(landing) == replace(READ, base=OTHER)
    old = MergeRead(tip=OTHER, base=BASE, base_tree=TREE, verdict="merge", at=MOMENT)
    other = task("open", **{**OPENED, "reads": (old,)}).landing
    assert other is not None
    assert mergeread.read_of(other) is None
