"""The owner's careful decision applies to the proposal and to new merge calls."""

from msgspec.structs import replace

from lem.app.landing import pr_text
from lem.model.landing import (
    careful,
    merge,
    merge_standing,
    propose,
    review,
    review_due,
    review_said,
)
from lem.model.landing.careful_words import OWNER_ASKED, OWNER_SAYS
from lem.records.landing.propose import Standing
from lem.records.landing.review import Reviewed
from unit.landing.merges import BY_MERGER, code_of, facing, opened
from unit.landing.proposals import FACTS, small, taken, with_landing
from unit.landing.worlds import MOMENT, REVIEWED, TIP, TREE, world


def test_an_owner_careful_decision_survives_the_reviewers_negative_call() -> None:
    decision = taken(1, OWNER_ASKED, "careful until its merge", "owner")
    record = with_landing(small(decisions=(decision,)), reviews=())
    independent = review.decide(
        record,
        world(),
        review_said.Said(
            attempt=1,
            tip=TIP,
            kind="full",
            answered=("claude",),
            careful=False,
            careful_why="the change reaches no configured topic",
            ran=(review_said.Named(name="full set", why=OWNER_SAYS),),
        ),
        review_due.Facts(careful=careful.reasons(record, careful.Edits())),
    )
    assert isinstance(independent, Reviewed)
    record = with_landing(record, reviews=(independent,))
    facts = replace(FACTS, notes=f"{FACTS.notes}\n## Migration\n\nnone\n")
    proposal = propose.decide(record, world(), facts, "Fix the login")
    assert isinstance(proposal, propose.Proposal)
    assert proposal.careful == (OWNER_SAYS,)
    assert proposal.proposed.careful and proposal.proposed.who_acts == "owner"
    assert not proposal.proposed.green
    assert f"careful: yes, {OWNER_SAYS}" in pr_text.body(record, proposal, facts)


def test_the_locked_call_honors_an_owner_careful_decision_after_proposal() -> None:
    record = opened(reviews=(replace(REVIEWED, kind="full"),))
    decision = taken(1, OWNER_ASKED, "careful until its merge", "owner")
    changed = replace(record, task=replace(record.task, decisions=(decision,)))
    assert code_of(merge.decide(changed, facing(), BY_MERGER, TREE)) == "merger-rule"


def test_a_late_careful_decision_changes_the_reasons_of_a_fast_track_standing_merge() -> (
    None
):
    standing = Standing(
        tip=TIP, reasons_digest=merge_standing.digest_of(()), by_act="board", at=MOMENT
    )
    record = opened(standing=standing, reviews=(replace(REVIEWED, kind="full"),))
    assert merge_standing.standing_of(record) == standing
    decision = taken(1, OWNER_ASKED, "careful until its merge", "owner")
    changed = replace(record, task=replace(record.task, decisions=(decision,)))
    assert merge_standing.standing_of(changed) is None
