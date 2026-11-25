"""The merge agent's read (`model/landing/mergeread.py`, `merge_said.py`): the verdict and the
call on a moved base from its reply, the read that covers its brief's base by its tree, an answer
that cannot be recorded asked again once and settled the second time (`landing.md` E, "Two
unusable answers", "No answer"), and a tip whose read says another round."""

import pytest
from msgspec.structs import replace

from lem.model.landing import merge_said, mergeread
from lem.records.landing.propose import MergeRead
from lem.records.landing.record import Landing
from unit.landing.merges import MOVED, MOVED_TREE, code_of, facing, moved, opened
from unit.landing.worlds import BASE, MOMENT, OPENED, OTHER, TIP, TREE, task

OPENED_LANDING = task("open", **OPENED).landing or Landing()
UNMOVED = mergeread.Briefed(tip=TIP, base=BASE, base_tree=TREE, moved=False)
ON_MOVED = mergeread.Briefed(tip=TIP, base=MOVED, base_tree=MOVED_TREE, moved=True)


def first_read(briefed: mergeread.Briefed, reply: str | None) -> MergeRead:
    found = mergeread.decide(task("open", **OPENED), briefed, reply, MOMENT)
    assert isinstance(found, MergeRead), found
    return found


@pytest.mark.parametrize(
    ("reply", "verdict"),
    [
        ("merge\n\nOne word; the checks hold.", "merge"),
        ("Verdict: merge.\nBase: safe.", "merge"),
        ("**Verdict:** call. The owner reads it.", "call"),
        ("# call the owner", "call"),
        ("> Merge", "merge"),
        ("", None),
        ("It looks fine.\nVerdict: merge.", None),
        ("merger", None),
    ],
)
def test_the_verdict_is_the_first_line(reply: str, verdict: str | None) -> None:
    assert merge_said.verdict_of(reply) == verdict


@pytest.mark.parametrize(
    ("reply", "call"),
    [
        (
            "Verdict: merge.\nBase: safe. Only a document moved.",
            ("safe", "Only a document moved."),
        ),
        (
            "merge\n**Base:** another round, a function it calls was renamed",
            ("another round", "a function it calls was renamed"),
        ),
        ("merge\nBase: safe.", None),
        ("merge", None),
        ("merge\nIt holds.", None),
    ],
)
def test_the_call_on_a_moved_base_is_the_second_line_with_its_why(
    reply: str, call: tuple[str, str] | None
) -> None:
    assert merge_said.base_call_of(reply) == call


def test_a_verdict_is_recorded_with_its_sentence_never_the_word_alone() -> None:
    read = first_read(UNMOVED, "merge\n\nOne word; the checks hold.\n")
    assert (read.verdict, read.why, read.base, read.base_tree) == (
        "merge",
        "One word; the checks hold.",
        BASE,
        TREE,
    )
    said = first_read(UNMOVED, "Verdict: call. The criterion is not met.")
    assert (said.verdict, said.why) == ("call", "The criterion is not met.")
    bare = first_read(UNMOVED, "merge")
    assert (bare.verdict, bare.why) == ("merge", None)


def test_a_read_on_a_moved_base_keeps_its_call_and_why() -> None:
    read = first_read(ON_MOVED, "Verdict: merge.\nBase: safe. Only README.md moved.")
    assert (read.verdict, read.base_call, read.why) == (
        "merge",
        "safe",
        "Only README.md moved.",
    )


def test_an_answer_that_cannot_be_recorded_is_asked_again_once() -> None:
    first = first_read(UNMOVED, "It looks fine to me.")
    assert (first.verdict, first.attempts) == (None, 1)
    assert first.why == "its first line gave no verdict"
    assert code_of(mergeread.again(first)) == "no-verdict"
    assert not mergeread.settled(first)


def test_the_second_unusable_answer_on_an_unmoved_base_calls_the_owner_with_no_verdict() -> (
    None
):
    first = first_read(UNMOVED, "It looks fine to me.")
    record = task("open", **{**OPENED, "reads": (first,)})
    second = mergeread.decide(record, UNMOVED, "Looks good.\nVerdict: merge.", MOMENT)
    assert isinstance(second, MergeRead)
    assert (second.verdict, second.base_call, second.attempts) == (None, None, 2)
    assert second.why is not None
    assert "`Verdict: merge.`" in second.why
    assert mergeread.again(second) is None
    assert mergeread.settled(second)
    landing = replace(OPENED_LANDING, reads=(first, second))
    assert mergeread.latest(landing, facing().base_tree) == second


def test_no_answer_twice_on_an_unmoved_base_says_that_the_last_try_gave_none() -> None:
    first = first_read(UNMOVED, None)
    assert (first.no_answer, first.why) == (True, "it ended with no answer")
    record = task("open", **{**OPENED, "reads": (first,)})
    second = mergeread.decide(record, UNMOVED, None, MOMENT)
    assert isinstance(second, MergeRead)
    assert second.why == (
        "the merge agent twice gave no answer with a verdict on its first line; "
        "its last try ended with no answer"
    )


def test_the_second_unusable_answer_on_a_moved_base_is_another_round_in_lems_words() -> (
    None
):
    first = first_read(ON_MOVED, "Verdict: merge.")
    assert first.why == "its second line gave no call on the moved base"
    record = task("open", **{**OPENED, "reads": (first,)})
    second = mergeread.decide(record, ON_MOVED, None, MOMENT)
    assert isinstance(second, MergeRead)
    assert (second.verdict, second.base_call) == (None, "another round")
    assert second.why == (
        "the merge agent's answer could not be recorded twice (it ended with no answer), "
        "and in doubt the checks run again"
    )
    landing = replace(record.landing, reads=(first, second)) if record.landing else None
    assert landing is not None
    assert mergeread.another_round(landing) == second


def test_unusable_answers_count_for_their_own_tip_and_base_only() -> None:
    other = replace(first_read(UNMOVED, None), base=OTHER)
    record = task("open", **{**OPENED, "reads": (other,)})
    again = mergeread.decide(record, UNMOVED, None, MOMENT)
    assert isinstance(again, MergeRead)
    assert again.attempts == 1


def test_a_reply_of_another_tip_or_with_no_proposal_or_after_another_round_is_refused() -> (
    None
):
    record = task("open", **OPENED)
    old = replace(UNMOVED, tip=OTHER)
    assert code_of(mergeread.decide(record, old, "merge", MOMENT)) == "old-tip"
    assert (
        code_of(mergeread.decide(task("landing"), UNMOVED, "merge", MOMENT))
        == "no-pull"
    )
    said = replace(
        first_read(ON_MOVED, "merge\nBase: another round, it renamed f."), tip=TIP
    )
    after = task("open", **{**OPENED, "reads": (said,)})
    assert code_of(mergeread.decide(after, UNMOVED, "merge", MOMENT)) == "another-round"


def test_a_read_is_usable_for_the_proposed_tip_on_its_base_tree_once_it_settles() -> (
    None
):
    read = first_read(UNMOVED, "merge\nIt holds.")
    landing = opened(reads=(read,)).landing
    assert landing is not None
    assert mergeread.latest(landing, facing().base_tree) == read
    assert mergeread.latest(landing, facing(base=MOVED).base_tree) == read
    assert mergeread.latest(landing, moved().base_tree) is None
    older = replace(read, tip=OTHER)
    assert mergeread.latest(replace(landing, reads=(older,)), TREE) is None
    assert mergeread.latest(landing) == read
    assert mergeread.latest(landing, MOVED_TREE) is None
