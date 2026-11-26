"""The facts that admit an owner-approved change after its base moves."""

import pytest
from msgspec.structs import replace

from lem.app.landing import checks_kept
from lem.app.landing.checks_verdict import Verdict
from lem.kernel.errors import Refusal
from lem.model.criteria import contract
from lem.model.landing import merge, merge_recheck, merge_standing, proposal_carry
from lem.model.landing.merge_asked import Asked
from lem.model.landing.world import Due
from lem.records.journal.landing import CheckEnd
from lem.records.landing.merge import Refused
from lem.records.landing.propose import MergeRead, OwnerMerge, Standing
from unit.landing.merges import (
    BY_MERGER,
    MOVED,
    MOVED_TREE,
    SUBJECT,
    facing,
    moved,
    opened,
)
from unit.landing.worlds import BASE, CHECKED, MOMENT, OTHER, REVIEWED, TIP, TREE, task


def test_the_passed_checks_must_name_the_current_base_commit() -> None:
    found = opened()
    assert not merge_recheck.priority(found, BASE)
    assert merge_recheck.priority(found, MOVED)
    assert merge_recheck.priority(found, None)
    assert merge_recheck.priority(task("open"), BASE)
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
    assert refused == Refused(
        tip=OTHER, source="lem", kind="rule", by="owner", line=end.say, at=MOMENT
    )
    assert found.landing is not None
    assert merge_recheck.red(found.landing, run, end) is None
    assert merge_recheck.red(replace(approved.landing, proposed=None), run, end) is None
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


def test_a_standing_approval_on_an_old_base_says_which_checks_to_run() -> None:
    approval = Standing(tip=TIP, reasons_digest="d", by_act="board", at=MOMENT)
    record = opened(standing=approval)
    assert record.landing is not None
    assert merge_recheck.due(record.landing, moved()) == Due(
        step="start", why="the approval stands: rebase and run the checks again"
    )
    refused = merge_recheck.refusal(record, moved())
    assert refused is not None
    assert (refused.code, refused.why, refused.fix) == (
        "base",
        "the base moved after the checks ran: the approved change needs checks on its new base",
        "lem land next fix-the-login names the steps to rebase and check it",
    )
    assert not merge_recheck.moved(None, BASE)


def test_the_approval_stands_during_rechecks_then_uses_the_current_review() -> None:
    record = opened()
    approval = Standing(
        tip=TIP,
        reasons_digest=merge_standing.digest_of((), contract.mark(record.task)),
        by_act="board",
        at=MOMENT,
    )
    open_without_checks = opened(standing=approval, checked=None)
    assert merge_standing.standing_of(open_without_checks) is None
    assert open_without_checks.landing is not None
    preparing = replace(
        open_without_checks,
        landing=replace(open_without_checks.landing, phase="preparing"),
    )
    assert merge_standing.standing_of(preparing) == approval
    moved_tip = moved(tip=OTHER)
    assert merge_standing.standing_of(opened(standing=approval), moved_tip) is None


def test_an_approval_ended_by_the_proposal_cannot_resume() -> None:
    record = opened()
    assert record.landing is not None and record.landing.proposed is not None
    proposed = record.landing.proposed
    approval = Standing(
        tip=TIP,
        reasons_digest=merge_standing.digest_of(proposed.reasons, proposed.contract),
        by_act="board",
        at=MOMENT,
    )
    ended = replace(
        proposed, owner_merge=OwnerMerge(state="ended", why="the criteria changed")
    )
    assert merge_standing.standing_of(opened(standing=approval, proposed=ended)) is None


def test_a_fast_tracks_careful_reason_stays_until_the_new_proposal() -> None:
    record = opened()
    assert record.landing is not None and record.landing.proposed is not None
    still = (
        "careful on the fast track (money): it took the fast track, with no interview, "
        "no personas' read of its criterion and no plan, so a person reads it"
    )
    proposed = replace(record.landing.proposed, careful=True, reasons=(still,))
    assert merge_standing.reasons_now(opened(proposed=proposed)) == (still,)


def test_a_standing_call_checks_the_review_again_before_it_uses_the_approval() -> None:
    record = opened()
    approval = Standing(
        tip=TIP,
        reasons_digest=merge_standing.digest_of((), contract.mark(record.task)),
        by_act="board",
        at=MOMENT,
    )
    approved = opened(standing=approval)
    asked = Asked(by="owner", via="server", standing=True, subject=SUBJECT)
    stale = facing(tip=OTHER)
    refused = merge.decide(approved, stale, asked, TREE)
    assert isinstance(refused, Refusal)
    assert refused.code == "tip"
    assert refused.why == (
        f"no merge of the owner's stands for {TIP}: the proposal ended it: nothing was merged"
    )
    assert "--standing" not in merge.due(approved, stale).why


def test_the_existing_owner_approval_requires_checks_on_the_new_base_for_any_caller() -> (
    None
):
    record = opened()
    approved = Standing(
        tip=TIP,
        reasons_digest=merge_standing.digest_of((), contract.mark(record.task)),
        by_act="board",
        at=MOMENT,
    )
    safe = MergeRead(
        tip=TIP,
        base=MOVED,
        base_tree=MOVED_TREE,
        verdict="merge",
        base_call="safe",
        why="a doc changed",
        at=MOMENT,
    )
    record = opened(standing=approved, reads=(safe,))
    refused = merge.decide(record, moved(), BY_MERGER, TREE)
    assert isinstance(refused, Refusal)
    assert refused.code == "base"
    assert "the approved change needs checks on its new base" in refused.why
