"""Green over drawn records (`model/landing/green.py`, `propose.made`; `landing.md` H 5): one
function, whose reasons are empty exactly when the proposal says green; who merges follows from
them; and the reasons the checks, the review, a careful fast task and the owner's approval
give are there whenever their cause is."""

from typing import TYPE_CHECKING

from hypothesis import given
from hypothesis import strategies as st
from msgspec.structs import replace

from lem.model.landing import green, green_words, merge, merge_standing, propose
from lem.model.landing.propose_facts import small
from lem.records.landing.record import Landing
from model.landings import LANDING, any_records, any_worlds
from unit.landing.proposals import changed, taken
from unit.landing.worlds import PREPARED, task, world

if TYPE_CHECKING:
    from lem.model.landing.world import World
    from lem.records.decisions import Level
    from lem.records.record import Record

PLAIN = world()
PLAIN_RECORD = task(**PREPARED)
CAREFUL = st.sampled_from(((), ("the login",), ("the login", "the plan says so")))


@LANDING
@given(any_records(), any_worlds(), CAREFUL)
def test_a_proposal_is_green_exactly_when_green_gives_no_reason(
    record: Record, world: World, careful: tuple[str, ...]
) -> None:
    made = propose.made(record, world, careful)
    assert made.reasons == green.reasons(record, careful)
    assert made.green == (not made.reasons)
    assert made.careful == bool(careful)
    if made.who_acts == "merger":
        assert made.green
        assert not careful
        assert world.rules.land == "agent"
    else:
        assert careful or made.reasons or world.rules.land == "owner"


@LANDING
@given(any_records(), CAREFUL)
def test_each_cause_of_not_green_gives_its_reason(
    record: Record, careful: tuple[str, ...]
) -> None:
    landing = record.landing or Landing()
    reasons = green.reasons(record, careful)
    checked = landing.checked
    if checked is None or checked.outcome != "passed":
        assert "the checks did not pass" in reasons
    last = green.newest(landing)
    if last is not None and green.must_fix(last):
        assert any("must-fix" in reason for reason in reasons)
    if careful and small(record):
        assert reasons[0].startswith("careful on the fast track")
    approvals = record.task.criteria.approvals
    if approvals and approvals[-1].by == "alone":
        assert any("did not approve the criteria" in reason for reason in reasons)


@LANDING
@given(any_records())
def test_the_merge_reads_again_green_s_own_reasons_and_the_proposal_s_fast_lines(
    record: Record,
) -> None:
    now = merge_standing.reasons_now(record)
    plain = green.reasons(record, ())
    assert now[len(now) - len(plain) :] == plain
    fast = now[: len(now) - len(plain)]
    assert all(reason.startswith("careful on the fast track") for reason in fast)
    proposed = (record.landing or Landing()).proposed
    not_green = merge.authority(record, PLAIN) == merge.NOT_GREEN
    assert not_green == (proposed is None or bool(now))


def test_a_criterion_changed_with_no_decision_behind_it_is_a_reason_in_its_own_words() -> (
    None
):
    change = changed(2, "changed", 1, "the login takes a code.")
    record = replace(PLAIN_RECORD, task=replace(PLAIN_RECORD.task, decisions=(change,)))
    assert "criterion 1 changed during the build: the login takes a code." in (
        green.reasons(record, ())
    )


@LANDING
@given(
    by=st.sampled_from(("owner", "lead", "dialectic")),
    on_breaker=st.booleans(),
)
def test_a_change_the_owner_s_help_on_a_breaker_made_is_his_and_no_reason(
    by: Level, *, on_breaker: bool
) -> None:
    decision = taken(
        3, "where the code goes", "a field", by, breaker=1 if on_breaker else None
    )
    change = changed(4, "changed", 1, "the login takes a code.", decision=3)
    made = replace(
        PLAIN_RECORD, task=replace(PLAIN_RECORD.task, decisions=(decision, change))
    )
    his = by == "owner" and on_breaker
    why = green_words.change_why(made, change)
    assert ("the owner's help on breaker 1" in why) == his
    assert why.endswith('took "a field"')
    assert (not green.changed(made)) == his
