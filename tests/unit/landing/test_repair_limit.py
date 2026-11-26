"""What the owner sees after two builders fail to repair a run of the checks."""

from datetime import timedelta
from typing import TYPE_CHECKING

import pytest
from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.landing import phases, repair_limit
from lem.model.landing.world import Due
from lem.model.task import red_base
from lem.records.holds import Blocked, Parked
from lem.records.journal.task import StateNoted
from lem.records.landing.propose import Standing
from lem.records.landing.record import Landing
from unit.landing.worlds import CHECKED, MOMENT, TIP, task, world

if TYPE_CHECKING:
    from lem.records.landing.checks import Checked
    from lem.records.record import Record

WHY = "two builders could not repair the checks"
FIX = 'on the owner\'s word, lem task move fix-the-login ready --line "go on" clears the hold'
RED = replace(CHECKED, outcome="red")
STANDING = Standing(tip=TIP, reasons_digest="d", by_act="board", at=MOMENT)
LATER = MOMENT + timedelta(minutes=1)


@pytest.mark.parametrize("checked", [RED, replace(RED, outcome="refused")])
def test_two_failed_repairs_block_an_ordinary_landing_and_tell_the_owner(
    checked: Checked,
) -> None:
    before = replace(
        task(checked=checked),
        journal=(StateNoted(at=MOMENT, status="landing"),),
    )
    blocked = repair_limit.blocked(before, LATER)
    assert blocked.task == replace(
        before.task,
        status="ready",
        since=LATER,
        hold=Blocked(why=WHY, fix=FIX, since=LATER),
    )
    assert blocked.landing == before.landing
    assert blocked.journal == (
        *before.journal,
        StateNoted(at=LATER, status="ready", hold="blocked", line=WHY),
    )
    assert repair_limit.due(blocked.task) == Due(step="wait", why=f"{WHY}: {FIX}")
    assert repair_limit.blocked(blocked, LATER + timedelta(minutes=1)) == blocked


@pytest.mark.parametrize(
    "record",
    [
        task(),
        replace(task(), landing=Landing()),
        task(checked=CHECKED),
        task(checked=replace(RED, outcome="stopped")),
        task("open", checked=RED),
        task(checked=RED, standing=STANDING),
        replace(
            task(checked=RED), task=replace(task().task, hold=Parked(since=MOMENT))
        ),
    ],
)
def test_a_repair_wait_cannot_replace_a_hold_or_a_standing_owner_approval(
    record: Record,
) -> None:
    with pytest.raises(Refusal) as error:
        repair_limit.blocked(record, LATER)
    refused = error.value
    assert (refused.code, refused.why, refused.fix) == (
        "repair-limit",
        "only a failed check in a landing with no hold or standing approval can wait",
        "a standing approval takes the ladder; otherwise follow the checks' result",
    )


def test_the_repair_wait_is_distinct_from_a_red_base() -> None:
    blocked = Blocked(
        why="the base is red", fix="wait for its repair", after="fix-base", since=MOMENT
    )
    base_red = replace(task().task, hold=blocked)
    assert repair_limit.waiting(base_red) is None
    pending = repair_limit.due(base_red)
    assert pending == Due(
        step="wait",
        why=(
            "the base is red: after fix-base lands or on the owner's word, "
            'lem task move fix-the-login ready --line "the base is green again" clears the hold'
        ),
    )
    assert repair_limit.due(task().task) is None


def test_the_landing_waits_for_the_base_repair_before_checks_can_start() -> None:
    failed = task(checked=RED)
    repair = replace(task().task, slug="fix-base")
    blocked = red_base.blocked(failed, replace(task(), task=repair), LATER)
    assert phases.due(blocked, world()) == Due(
        step="wait",
        why=(
            "the base is red: after fix-base lands or on the owner's word, "
            'lem task move fix-the-login ready --line "the base is green again" clears the hold'
        ),
    )
