"""The due step of a landing (`model/landing/phases.py`), derived from the record's evidence
and the world now (`landing.md` C): in `preparing` the first row that does not hold, in `open`
the reconcile, the forge's merge, a new round, the read and the merge, then the bookkeeping, the
cleanup and the end; and what the record alone decides, with no look at the world."""

from typing import TYPE_CHECKING

import pytest
from msgspec.structs import replace

from lem.model.landing import phases
from lem.model.landing.merge_standing import digest_of
from lem.model.landing.world import Due, Rules
from lem.records.landing.merge import MergeAccepted, Refused
from lem.records.landing.propose import MergeRead, Standing
from lem.records.landing.review import Counts
from lem.records.task import Shape
from unit.landing.merges import (
    INTENT,
    MOVED,
    MOVED_TREE,
    alone,
    facing,
    moved,
    opened,
)
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
            task(
                **{
                    **PREPARED,
                    "reviews": (
                        replace(
                            REVIEWED, findings=(), counts=Counts(must_fix=1), to_file=()
                        ),
                    ),
                }
            ),
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
    assert step_of(phases.due(task("open", **OPENED), facing())) == (
        "merge-review",
        None,
    )
    assert step_of(phases.due(opened(), facing())) == ("merge", "merger")
    call = opened(reads=(replace(READ, verdict="call"),))
    assert step_of(phases.due(call, facing())) == ("merge", "owner")
    owner = facing(rules=Rules(base="main", land="owner", commands=("true",)))
    assert step_of(phases.due(opened(), owner)) == ("merge", "owner")


def test_a_read_covers_one_base_by_its_tree_and_a_moved_base_is_read_first() -> None:
    assert phases.due(opened(), moved()).step == "merge-review"
    assert step_of(phases.due(opened(), facing(base=MOVED))) == ("merge", "merger")
    safe = MergeRead(
        tip=TIP,
        base=MOVED,
        base_tree=MOVED_TREE,
        verdict="merge",
        base_call="safe",
        why="a document moved",
        at=MOMENT,
    )
    assert step_of(phases.due(opened(reads=(READ, safe)), moved())) == (
        "merge",
        "merger",
    )
    again = moved(base="d" * 40, base_tree="0" * 40)
    assert phases.due(opened(reads=(READ, safe)), again).step == "merge-review"
    reverted = facing(base="d" * 40)
    assert step_of(phases.due(opened(reads=(READ, safe)), reverted)) == (
        "merge",
        "merger",
    )


def test_a_verdict_of_another_base_gives_no_authority_on_this_one() -> None:
    called = MergeRead(
        tip=TIP,
        base=MOVED,
        base_tree=MOVED_TREE,
        verdict="call",
        base_call="safe",
        why="the owner reads it",
        at=MOMENT,
    )
    later = MergeRead(
        tip=TIP,
        base="d" * 40,
        base_tree="0" * 40,
        verdict="merge",
        base_call="safe",
        why="fine",
        at=MOMENT,
    )
    back = opened(reads=(READ, called, later))
    assert step_of(phases.due(back, moved())) == ("merge", "owner")


def test_a_refusal_lem_kept_of_the_merge_agents_merge_waits_for_the_owner() -> None:
    refused = Refused(
        tip=TIP,
        source="lem",
        kind="tip",
        line="the head moved; read it",
        by="merger",
        at=MOMENT,
    )
    due = phases.due(opened(refused=refused), facing())
    assert step_of(due) == ("merge", "owner")
    assert "Lem refused the merge agent's merge of this tip: the head moved" in due.why


def test_a_merge_on_github_during_a_new_round_is_bookkept_first() -> None:
    merged = facing(pull=replace(SEEN, state="merged"))
    record = task("landing", **{**PREPARED, "pull": OPENED["pull"]})
    assert phases.due(record, merged).step == "merged"
    assert phases.due(task("landing", **PREPARED), merged).step != "merged"


def test_a_read_that_says_another_round_makes_a_new_round_due() -> None:
    round_read = MergeRead(
        tip=TIP,
        base=MOVED,
        base_tree=MOVED_TREE,
        verdict="merge",
        base_call="another round",
        why="the moved base renamed a function the change calls",
        at=MOMENT,
    )
    due = phases.due(opened(reads=(READ, round_read)), moved())
    assert due.step == "start"
    assert "another round" in due.why


def test_a_first_unusable_answer_keeps_the_read_due_and_the_second_settles_it() -> None:
    first = MergeRead(
        tip=TIP, base=BASE, base_tree=TREE, attempts=1, why="no verdict", at=MOMENT
    )
    record = task("open", **{**OPENED, "reads": (first,)})
    assert phases.due(record, facing()).step == "merge-review"
    second = replace(first, attempts=2, why="the merge agent twice gave no verdict")
    settled = task("open", **{**OPENED, "reads": (first, second)})
    assert step_of(phases.due(settled, facing())) == ("merge", "owner")


def test_in_open_an_intent_is_reconciled_first_and_a_forge_merge_is_bookkept() -> None:
    due = phases.due(opened(intent=INTENT), facing())
    assert step_of(due) == ("merge", "merger")
    assert due.why == "a merge call is on record: it is reconciled first"
    merged = facing(pull=replace(SEEN, state="merged"))
    assert phases.due(opened(), merged).step == "merged"
    closed = facing(pull=replace(SEEN, state="closed"))
    assert phases.due(opened(), closed).step == "merged"
    queued = MergeAccepted(tip=TIP, at=MOMENT, queued="the merge queue")
    assert phases.due(opened(accepted=queued), facing()).step == "merged"
    assert phases.due(opened(), facing(tip=OTHER)).step == "start"


def test_githubs_refusal_of_this_tip_waits_for_the_owners_word() -> None:
    refused = Refused(
        tip=TIP, source="github", kind="rule", line="checks", by="merger", at=MOMENT
    )
    due = phases.due(opened(refused=refused), facing())
    assert step_of(due) == ("merge", "owner")
    assert "GitHub refused the merge of this tip: checks" in due.why
    older = replace(refused, tip=OTHER)
    assert step_of(phases.due(opened(refused=older), facing())) == ("merge", "merger")


def test_a_merge_into_another_base_waits_with_its_line() -> None:
    refused = Refused(
        tip=TIP,
        source="lem",
        kind="target",
        line="it went into release",
        by="owner",
        at=MOMENT,
    )
    merged = facing(pull=replace(SEEN, state="merged", base="release"))
    assert phases.due(opened(refused=refused), merged) == Due(
        step="wait", why="it went into release"
    )


def test_the_owners_standing_merge_is_the_servers_to_carry_out() -> None:
    record = alone()
    proposed = record.landing.proposed if record.landing else None
    assert proposed is not None
    standing = Standing(
        tip=TIP,
        reasons_digest=digest_of(proposed.reasons, proposed.contract),
        by_act="board",
        at=MOMENT,
    )
    stands = alone(standing=standing)
    due = phases.due(stands, facing())
    assert step_of(due) == ("merge", "owner")
    assert "--standing" in due.why
    other = replace(standing, reasons_digest=digest_of(("another",), proposed.contract))
    assert "--standing" not in phases.due(alone(standing=other), facing()).why


def test_after_the_merge_its_bookkeeping_the_cleanup_and_the_end() -> None:
    merged = {**OPENED, "phase": "merged", "merged": MERGED}
    assert phases.due(task("open", **merged), world()).step == "merged"
    assert phases.due(task("landed", **merged), world()).step == "clean"
    ended = {**merged, "phase": "ended"}
    assert phases.due(task("landed", **ended), world()).step == "done"


def test_a_dropped_or_answered_task_is_cleaned_once_then_done() -> None:
    for status in ("dropped", "answered"):
        assert phases.due(task(status), world()).step == "clean"
        assert phases.due(task(status, phase="ended"), world()).step == "done"


@pytest.mark.parametrize(
    ("record", "step"),
    [
        (task("building"), "none"),
        (task("dropped"), "clean"),
        (task("landed", **{**OPENED, "phase": "merged", "merged": MERGED}), "clean"),
        (task("open", **{**OPENED, "phase": "merged", "merged": MERGED}), "merged"),
        (task("landed", **{**OPENED, "phase": "ended"}), "done"),
        (task("open", **OPENED), None),
        (task("ready"), None),
    ],
)
def test_the_record_alone_decides_after_the_merge_and_for_a_task_not_landing(
    record: Record, step: str | None
) -> None:
    found = phases.settled(record)
    assert (found.step if found else None) == step
