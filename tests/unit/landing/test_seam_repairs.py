"""Evidence at the joins of checks, review, proposal and merge."""

from datetime import timedelta
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest
from msgspec.structs import replace

from lem.app.criteria.show import kept
from lem.app.landing import checks_criteria, merge_step, pr_criteria, propose_made
from lem.app.tasks.move import change
from lem.kernel.errors import Refusal
from lem.model.criteria import read, standing
from lem.model.decisions.changes import changes_of
from lem.model.landing import (
    checks,
    filing,
    merge,
    merge_standing,
    phases,
    propose,
    review,
)
from lem.records.landing.checks import CriterionCheck
from lem.records.landing.propose import Standing
from lem.records.landing.review import Counts, Filed
from lem.records.red import Inputs
from lem.records.work import Plan
from unit.landing.merges import BY_MERGER, BY_OWNER, code_of, facing, opened
from unit.landing.proposals import FACTS, full, with_landing
from unit.landing.worlds import (
    BASE,
    BASED,
    CHECKED,
    MOMENT,
    NIT,
    PREPARED,
    PROPOSED,
    PULL,
    REVIEWED,
    RULES,
    SEEN,
    TIP,
    TREE,
    task,
    world,
)

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.record import Record

NEW = "3" * 40
AFTER = MOMENT + timedelta(seconds=1)
SCRIPT = "sh tests/b.sh"


def sheet(command: str, size: str) -> str:
    """The acceptance criteria with the named test."""
    return (
        f"## Acceptance criteria\n\nSize: {size}, because one word\n\n"
        f"1. The login works.\n   - test: `sh tests/{command}.sh` in `tests/{command}.sh`\n"
    )


def recorded(record: Record, command: str, *, small: bool) -> Record:
    parsed = read.sheet_of(sheet(command, "small" if small else "full"), "plan.md")
    seen = standing.shown_of(
        "fix-the-login", "plan.md", parsed, changes_of(record.task), small=small
    )
    return kept(record, seen=seen)


def test_the_review_limit_sends_an_unread_tip_to_the_owner() -> None:
    prior = replace(
        REVIEWED, attempt=2, kind="round", findings=(), counts=Counts(), to_file=()
    )
    record = task(
        **{
            **PREPARED,
            "based": replace(BASED, tip=NEW),
            "checked": replace(CHECKED, tip=NEW),
            "reviews": (REVIEWED, prior),
        }
    )
    current = world(tip=NEW)
    assert phases.due(record, current).step == "propose"
    decision = propose.decide(record, current, FACTS, "Fix the login")
    assert isinstance(decision, propose.Proposal)
    assert decision.proposed.who_acts == "owner"
    assert not decision.proposed.green
    assert any(
        "nobody reviewed what changed after it" in line
        for line in decision.proposed.reasons
    )

    kept_open = opened().landing
    assert kept_open is not None and kept_open.proposed is not None
    stale = opened(
        checked=replace(CHECKED, tip=NEW),
        proposed=replace(kept_open.proposed, tip=NEW),
        pushed=NEW,
        reviews=(REVIEWED, prior),
    )
    assert (
        code_of(
            merge.decide(
                stale, facing(tip=NEW, pull=replace(SEEN, head=NEW)), BY_MERGER, TREE
            )
        )
        == "merger-rule"
    )


def test_checks_refuse_a_live_plan_whose_tests_differ_from_the_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "plan.md"
    record = recorded(full(plan=Plan(path=path.name)), "a", small=False)
    path.write_text(sheet("b", "full"))
    found = Inputs(tip=TIP, base=BASE, plan=path.name)
    monkeypatch.setattr(checks_criteria, "inputs", lambda *_: found)
    monkeypatch.setattr(checks_criteria, "worktree_of", lambda *_: tmp_path)
    monkeypatch.setattr(checks_criteria, "checked", Mock())
    monkeypatch.setattr(
        checks_criteria.checks_git,
        "raw",
        lambda *_: Mock(returncode=0, stdout=path.read_bytes()),
    )
    monkeypatch.setattr(checks_criteria.checks_git, "listed", lambda *_: (path.name,))
    monkeypatch.setattr(checks_criteria.checks_red_places, "laid", lambda *_: ())
    with pytest.raises(Refusal, match="the criteria"):
        checks_criteria.prepared(Mock(checkout=tmp_path), record)


def test_a_test_change_invalidates_the_checks_and_the_prs_criterion_proof() -> None:
    record = recorded(task(**PREPARED), "a", small=True)
    proof = CriterionCheck(criterion=1, red_on_base=True, green_on_tip=True)
    record = with_landing(
        record,
        checked=replace(
            CHECKED, criteria=(proof,), criteria_digest=record.task.criteria.digest
        ),
    )
    changed = recorded(record, "b", small=True)
    current = changed.task.criteria.criteria[0]
    assert (
        pr_criteria.criterion_lines(changed, current)[1]
        == f"   - `{SCRIPT}`: not checked"
    )
    assert phases.due(changed, world()).step == "checks"


def test_a_setup_only_change_refuses_the_locked_merge() -> None:
    before = RULES
    after = replace(before, setup=("false",))
    assert checks.inputs(before) != checks.inputs(after)
    record = opened(checked=replace(CHECKED, inputs=checks.inputs(before)))
    assert (
        code_of(merge.decide(record, facing(rules=after), BY_MERGER, TREE))
        == "checks-changed"
    )


def test_stale_checks_on_an_open_pr_get_a_new_round_even_after_a_refusal() -> None:
    record = opened()
    current = facing(rules=replace(RULES, commands=("new-command",)))
    denied = merge.decide(record, current, BY_MERGER, TREE)
    assert isinstance(denied, Refusal)
    assert code_of(merge.decide(record, current, BY_OWNER, TREE)) == "checks-changed"
    refused = merge_standing.refused_of(record, denied, BY_MERGER, MOMENT)
    after = opened(refused=refused)
    assert phases.due(record, current).step == "start"
    assert phases.due(after, current).step == "start"
    merge_step.allowed(Mock(record=after, world=current), "start", None)


def test_checks_of_the_same_tip_are_due_on_a_new_base_in_preparing() -> None:
    record = task(**{**PREPARED, "based": replace(BASED, base=NEW)})
    assert phases.due(record, world(base=NEW)).step == "checks"


def test_a_new_attempt_cannot_inherit_the_disposition_of_an_archived_finding() -> None:
    prior = replace(NIT, title="first defect", against="over", why=None)
    kept_filing = Filed(
        finding=prior.id,
        disposition="item",
        path="docs/backlog/first.md",
        worth="later",
    )
    record = task(
        **{
            **PREPARED,
            "reviews": (replace(REVIEWED, findings=(prior,)),),
            "filed": (kept_filing,),
        }
    )
    reset = change(
        record, status="ready", line="", start_over="reset this landing", now=MOMENT
    )
    assert reset.landing is not None
    fresh = replace(prior, title="different defect", where="other.py")
    landing = replace(reset.landing, reviews=(replace(REVIEWED, findings=(fresh,)),))
    assert tuple(finding for _, finding in filing.waiting(landing)) == (fresh,)


def test_the_new_proposal_records_a_carried_read_and_standing_approval() -> None:
    base = "4" * 40
    current = facing(tip=NEW, base=base, now=AFTER)
    previous = opened(
        standing=Standing(
            tip=TIP,
            reasons_digest=merge_standing.digest_of((), PROPOSED.contract),
            by_act="board",
            at=MOMENT,
        )
    )
    record = with_landing(
        replace(previous, task=replace(previous.task, status="landing")),
        phase="preparing",
        based=replace(BASED, tip=NEW, base=base, carried=True, at=AFTER),
        checked=replace(CHECKED, tip=NEW, base=base, at=AFTER),
    )
    decided = propose.decide(record, current, FACTS, "Fix the login")
    assert isinstance(decided, propose.Proposal)
    assert decided.proposed.merge_review == "carried"
    assert decided.proposed.owner_merge is not None
    assert decided.proposed.owner_merge.state == "stands"
    after = propose_made.opened(
        record, made=decided.proposed, pull=PULL, read=decided.read
    )
    assert after.landing is not None
    assert after.landing.reads[-1].tip == NEW
    assert (
        phases.due(after, replace(current, pull=replace(SEEN, head=NEW))).step
        == "merge"
    )
    assert review.holds(after, current).why.startswith("the newest review covers")
