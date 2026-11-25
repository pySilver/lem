"""The facts that admit an owner-approved change after its base moves."""

import pytest
from msgspec.structs import replace

from lem.app.landing import checks_kept
from lem.app.landing.checks_verdict import Verdict
from lem.kernel.errors import Refusal
from lem.model.criteria import contract
from lem.model.landing import merge_recheck, merge_standing, proposal_carry
from lem.records.journal.landing import CheckEnd
from lem.records.landing.propose import Standing
from unit.landing.merges import MOVED, moved, opened
from unit.landing.worlds import BASE, CHECKED, MOMENT, OTHER, REVIEWED, TIP


def test_the_passed_checks_must_name_the_current_base_commit() -> None:
    found = opened()
    assert not merge_recheck.priority(found, BASE)
    assert merge_recheck.priority(found, MOVED)
    assert merge_recheck.priority(found, None)
    assert merge_recheck.priority(opened(checked=None), BASE)
    assert merge_recheck.priority(opened(checked=replace(CHECKED, outcome="red")), BASE)


def test_a_red_recheck_keeps_its_refusal_until_a_review_covers_the_repair() -> None:
    found = opened()
    approval = Standing(
        tip=TIP,
        reasons_digest=merge_standing.digest_of((), contract.mark(found.task)),
        by_act="board",
        at=MOMENT,
    )
    approved = opened(standing=approval)
    assert approved.landing is not None
    run = replace(CHECKED, tip=OTHER, base=MOVED, outcome="red")
    end = CheckEnd(at=MOMENT, outcome="red", say="a builder repairs it")
    refused = merge_recheck.red(approved.landing, run, end)
    assert refused is not None and refused.line == end.say
    assert merge_recheck.red(approved.landing, replace(run, base=BASE), end) is None
    assert (
        merge_recheck.red(approved.landing, replace(run, outcome="passed"), end) is None
    )
    stopped = opened(standing=approval, refused=refused, checked=None)
    assert stopped.landing is not None
    assert merge_recheck.repair(stopped.landing)
    world = moved(tip=OTHER)
    assert not proposal_carry.repaired(stopped, stopped.landing, world)
    reviewed = opened(
        standing=approval, refused=refused, reviews=(replace(REVIEWED, tip=OTHER),)
    )
    assert reviewed.landing is not None
    assert proposal_carry.repaired(reviewed, reviewed.landing, world)


@pytest.mark.parametrize(
    ("outcome", "code", "repair"),
    [
        ("refused", "criteria", True),
        ("refused", "contract-moved", False),
        ("stopped", "stopped", False),
    ],
)
def test_only_a_failed_criterion_check_marks_the_rebase_for_repair(
    outcome: str, code: str, *, repair: bool
) -> None:
    record = opened()
    approval = Standing(
        tip=TIP,
        reasons_digest=merge_standing.digest_of((), contract.mark(record.task)),
        by_act="board",
        at=MOMENT,
    )
    approved = opened(standing=approval)
    run = replace(CHECKED, tip=OTHER, base=MOVED, outcome=outcome)
    verdict = Verdict(run=run, refusal=Refusal(code, "the checks failed", "run again"))
    changed = checks_kept.kept(
        approved, world=moved(tip=OTHER), verdict=verdict, at=MOMENT
    )
    assert changed.landing is not None
    assert merge_recheck.repair(changed.landing) == repair
