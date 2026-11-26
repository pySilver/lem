"""The owner's careful decision applies to the proposal and to new merge calls."""

from msgspec.structs import replace

from lem.app.landing import pr_text
from lem.model.decisions import log
from lem.model.landing import (
    careful,
    careful_words,
    merge,
    merge_standing,
    propose,
    review,
    review_due,
    review_said,
)
from lem.records.landing.propose import Standing
from lem.records.landing.record import Landing
from lem.records.landing.review import Reviewed
from unit.landing.merges import BY_MERGER, code_of, facing, opened
from unit.landing.proposals import FACTS, small, with_landing
from unit.landing.worlds import MOMENT, PROPOSED, REVIEWED, TIP, TREE, world

OWNER_SAYS = "the owner says so"
CAREFUL = log.Logged(
    by="owner",
    what="whether the task is careful",
    chose="careful until its merge",
    why="it reaches the invoice",
)


def test_an_owner_careful_decision_survives_the_reviewers_negative_call() -> None:
    record = log.logged(with_landing(small(), reviews=()), asked=CAREFUL, now=MOMENT)
    assert record.task.owner_careful == MOMENT
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
    changed = log.logged(record, asked=CAREFUL, now=MOMENT)
    assert code_of(merge.decide(changed, facing(), BY_MERGER, TREE)) == "merger-rule"


def test_a_late_careful_decision_changes_the_reasons_of_a_fast_track_standing_merge() -> (
    None
):
    standing = Standing(
        tip=TIP,
        reasons_digest=merge_standing.digest_of((), PROPOSED.contract),
        by_act="board",
        at=MOMENT,
    )
    record = opened(standing=standing, reviews=(replace(REVIEWED, kind="full"),))
    assert merge_standing.standing_of(record) == standing
    changed = log.logged(record, asked=CAREFUL, now=MOMENT)
    assert merge_standing.standing_of(changed) is None


def test_an_agent_decision_does_not_set_the_owners_careful_word() -> None:
    agent = replace(CAREFUL, by="lem")
    record = log.logged(small(), asked=agent, now=MOMENT)
    assert record.task.owner_careful is None
    assert careful.reasons(record, careful.Edits()) == ()


def test_the_latest_call_stands_when_the_record_has_only_resolution_reads() -> None:
    old = replace(REVIEWED, of="resolution", careful=True, careful_why="charges a card")
    past = replace(old, attempt=2, careful_why="changes the account")
    kept = Landing(reviews=(old, past))
    assert careful_words.review_reason(kept) == (
        "the review says so: changes the account",
    )
    no = replace(past, careful=False)
    assert careful_words.review_reason(replace(kept, reviews=(old, no))) == ()
