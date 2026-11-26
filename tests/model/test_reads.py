"""The merge agent's reads over drawn replies (`model/landing/mergeread.py`, `merge_said.py`;
`landing.md` C and E, "Two unusable answers", "No answer", "Base moved, open PR"): a reply is
recorded with a verdict exactly when its first line gives one, and on a moved base a call;
the second answer that cannot be recorded for one tip and base settles it, so no third read is
due: the owner on a base that did not move, a new round on a moved one."""

from hypothesis import given
from hypothesis import strategies as st
from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.landing import merge_said, mergeread, phases
from lem.model.landing.mergeread import Briefed
from lem.records.landing.record import Landing
from model.landings import LANDING
from unit.landing.merges import MOVED, MOVED_TREE, facing, moved, opened
from unit.landing.worlds import BASE, MOMENT, TIP, TREE

LINES = st.sampled_from(
    (
        "Verdict: merge",
        "Verdict: call. The owner reads the migration.",
        "**Verdict: merge** it is one word.",
        "Base: safe. Only docs moved.",
        "Base: another round: the API moved.",
        "Merge conflicts remain.",
        "# Verdict",
        "",
        "Verdict merge",
    )
)
REPLIES = st.none() | st.lists(LINES | st.text(max_size=20), max_size=4).map("\n".join)
UNMOVED = Briefed(
    tip=TIP, base=BASE, base_tree=TREE, moved=False, by="claude/opus:high"
)
ON_MOVED = replace(UNMOVED, base=MOVED, base_tree=MOVED_TREE, moved=True)


@LANDING
@given(reply=REPLIES, on_moved=st.booleans())
def test_a_reply_is_recorded_with_a_verdict_exactly_when_it_can_be(
    reply: str | None, *, on_moved: bool
) -> None:
    briefed = ON_MOVED if on_moved else UNMOVED
    read = mergeread.made(Landing(), briefed, reply, MOMENT)
    problem = merge_said.problem_of(reply, moved=briefed.moved)
    assert (read.verdict is not None) == (problem is None)
    assert read.no_answer == (reply is None)
    if problem is None:
        assert reply is not None
        assert read.verdict == merge_said.verdict_of(reply)
        if briefed.moved:
            assert read.base_call in {"safe", "another round"}
    else:
        assert read.attempts == 1
        assert read.why == problem
        assert mergeread.again(read) is not None


@LANDING
@given(first=REPLIES, second=REPLIES, on_moved=st.booleans())
def test_two_unusable_answers_for_one_tip_and_base_settle_it_and_no_third_read_is_due(
    first: str | None, second: str | None, *, on_moved: bool
) -> None:
    briefed = ON_MOVED if on_moved else UNMOVED
    if any(
        merge_said.problem_of(one, moved=on_moved) is None for one in (first, second)
    ):
        return
    record = opened(reads=())
    seen = moved() if on_moved else facing()
    for reply in (first, second):
        assert phases.due(record, seen).step == "merge-review"
        found = mergeread.decide(record, briefed, reply, MOMENT)
        assert not isinstance(found, Refusal), found
        landing = record.landing
        assert landing is not None
        record = replace(
            record, landing=replace(landing, reads=(*landing.reads, found))
        )
    last = (record.landing.reads if record.landing else ())[-1]
    assert last.attempts == merge_said.TRIES
    assert mergeread.settled(last)
    assert mergeread.again(last) is None
    after = phases.due(record, seen)
    assert after.step != "merge-review"
    if on_moved:
        assert (after.step, last.base_call) == ("start", "another round")
        assert last.why is not None
        assert last.why.startswith(merge_said.UNRECORDED)
    else:
        assert (after.step, after.by, last.verdict) == ("merge", "owner", None)
