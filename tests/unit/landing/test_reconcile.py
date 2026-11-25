"""What a merge call left and what the forge shows after it (`model/landing/reconcile.py`): an
intent replaced by the merge, the queue, the queue's end or the end of a closed request, and kept
while only an open pull request is visible; a merge into another base; the parent of a merge
by its method; the line of a merge on a moved base, covered or not (`landing.md` E)."""

from datetime import timedelta

import pytest
from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.landing import merge_lines, reconcile, reconcile_queue
from lem.model.landing.queue_evidence import Event
from lem.model.landing.reconcile import Trees
from lem.model.landing.world import Rules
from lem.records.landing.merge import MergeAccepted, Merged, Refused
from lem.records.landing.propose import MergeRead
from unit.landing.merges import (
    DONE,
    INTENT,
    MOVED,
    MOVED_TREE,
    SAME,
    code_of,
    facing,
    opened,
)
from unit.landing.worlds import BASE, MERGE, MERGED, MOMENT, OTHER, SEEN, TIP, TREE

SAFE = MergeRead(
    tip=TIP,
    base=MOVED,
    base_tree=MOVED_TREE,
    verdict="merge",
    base_call="safe",
    why="only README.md moved",
    at=MOMENT,
)


def test_an_intent_becomes_the_merge_the_forge_shows() -> None:
    record = opened(intent=INTENT)
    found = reconcile.reconciled(record, facing(pull=DONE), INTENT, SAME)
    assert found == replace(
        MERGED, via="server", base_read=BASE, text_updated=True, at=MOMENT
    )


def test_only_a_final_forge_result_makes_bookkeeping_due_with_an_intent() -> None:
    record = opened(intent=INTENT)
    assert record.landing is not None
    for pull in (DONE, replace(SEEN, state="closed")):
        due = reconcile.pending(record.landing, facing(pull=pull))
        assert due is not None and due.step == "merged"
    for pull in (SEEN, replace(SEEN, queued="the merge queue"), None):
        due = reconcile.pending(record.landing, facing(pull=pull))
        assert due is not None and due.step == "merge"


def test_an_intent_becomes_the_queue_its_end_or_the_end_of_a_closed_request() -> None:
    record = opened(intent=INTENT)
    added = Event(id="entry", at=MOMENT + timedelta(seconds=1), head=TIP)
    removed = Event(id="removal", at=MOMENT + timedelta(seconds=2), head=TIP)
    queued = facing(pull=replace(SEEN, queued="the merge queue", queue_event=added))
    assert reconcile.reconciled(record, queued, INTENT, SAME) == MergeAccepted(
        tip=TIP,
        at=MOMENT,
        queued="the merge queue",
        by="merger",
        via="server",
    )
    dequeued = replace(
        SEEN,
        dequeued="a required check failed",
        queue_event=removed,
        queue_entered=added,
    )
    assert reconcile.reconciled(record, facing(pull=dequeued), INTENT, SAME) == Refused(
        tip=TIP,
        source="github",
        kind="rule",
        line="a required check failed",
        by="merger",
        at=MOMENT,
    )
    closed = facing(pull=replace(SEEN, state="closed"))
    assert reconcile.reconciled(record, closed, INTENT, SAME) is None


def test_with_only_an_open_pull_request_visible_the_intent_stays_and_the_owner_checks() -> (
    None
):
    found = reconcile.reconciled(opened(intent=INTENT), facing(), INTENT, SAME)
    assert code_of(found) == "intent"
    assert isinstance(found, Refusal)
    assert "the owner checks https://github.com/o/p/pull/1 on GitHub" in found.fix
    assert f"--by owner --tip {TIP}" in found.fix


def test_a_merge_into_another_base_is_no_landing() -> None:
    elsewhere = replace(DONE, base="release")
    found = reconcile.landed(opened(), facing(), elsewhere, ("owner", "github", SAME))
    assert code_of(found) == "target"


def test_a_merge_whose_commit_the_forge_does_not_report_yet_writes_nothing() -> None:
    lagging = replace(DONE, merge_commit=None)
    found = reconcile.landed(opened(), facing(), lagging, ("owner", "github", SAME))
    assert code_of(found) == "unreported"


def test_a_merge_on_a_base_a_safe_read_covered_has_the_reads_line() -> None:
    onto = replace(DONE, base_parent=MOVED)
    trees = Trees(checks=TREE, parent=MOVED_TREE)
    world = facing(base=MOVED, base_tree=MOVED_TREE)
    found = reconcile.landed(
        opened(reads=(SAFE,)), world, onto, ("merger", "server", trees)
    )
    assert isinstance(found, Merged)
    assert (found.uncovered, found.text_updated, found.base_read) == (
        None,
        False,
        MOVED,
    )
    landing = opened(reads=(SAFE,)).landing
    assert landing is not None
    line, uncovered = reconcile.line_of(landing, found, trees, "main")
    assert not uncovered
    assert line == merge_lines.base_line("main", (BASE, MOVED), "only README.md moved")


def test_a_merge_on_github_between_the_look_and_the_call_lands_uncovered() -> None:
    onto = replace(DONE, base_parent=OTHER)
    trees = Trees(checks=TREE, parent="0" * 40)
    found = reconcile.landed(
        opened(reads=(SAFE,)), facing(), onto, ("merger", "server", trees)
    )
    assert isinstance(found, Merged)
    assert found.uncovered == merge_lines.uncovered_line("main", (BASE, OTHER), MOVED)
    assert "which no read of the merge agent covered (its read covered aaaaaaaaa)" in (
        found.uncovered or ""
    )
    assert found.text_updated is False


def test_an_empty_commit_on_the_base_is_no_move() -> None:
    onto = replace(DONE, base_parent=OTHER)
    found = reconcile.landed(opened(), facing(), onto, ("owner", "github", SAME))
    assert isinstance(found, Merged)
    assert (found.uncovered, found.text_updated, found.parent) == (None, True, OTHER)


@pytest.mark.parametrize("tree", [TREE, MOVED_TREE], ids=["same tree", "safe read"])
def test_an_owner_call_lands_with_a_warning_if_the_actual_parent_missed_checks(
    tree: str,
) -> None:
    call = replace(INTENT, by="owner", via="board")
    pull = replace(DONE, base_parent=MOVED)
    record = opened(intent=call, reads=(SAFE,))
    found = reconcile.reconciled(
        record, facing(pull=pull), call, Trees(checks=TREE, parent=tree)
    )
    assert isinstance(found, Merged)
    assert (found.by, found.via, found.base_checked, found.parent) == (
        "owner",
        "board",
        BASE,
        MOVED,
    )
    assert found.uncovered is not None
    assert BASE[:9] in found.uncovered and MOVED[:9] in found.uncovered
    assert not found.text_updated


def test_the_queue_that_ends_keeps_githubs_words_and_a_waiting_one_is_refused() -> None:
    accepted = MergeAccepted(tip=TIP, at=MOMENT, queued="the merge queue")
    record = opened(accepted=accepted)
    waiting = reconcile_queue.queued(
        record, facing(pull=replace(SEEN, queued="the merge queue"))
    )
    assert code_of(waiting) == "queued"
    removed = Event(id="removal", at=MOMENT + timedelta(seconds=1), head=TIP)
    ended = reconcile_queue.queued(
        record,
        facing(pull=replace(SEEN, dequeued="a check failed", queue_event=removed)),
    )
    assert isinstance(ended, Refused)
    assert (ended.source, ended.line, ended.tip, ended.by) == (
        "github",
        "a check failed",
        TIP,
        "merger",
    )


def test_the_parent_is_the_forges_word_for_either_method() -> None:
    keep = facing(rules=Rules(base="main", history="keep", commands=("true",)))
    replayed = replace(DONE, merge_commit=MERGE, base_parent=BASE)
    found = reconcile.landed(opened(), keep, replayed, ("owner", "board", SAME))
    assert isinstance(found, Merged)
    assert (found.parent, found.base_merged) == (BASE, BASE)


def test_a_removal_without_a_head_cannot_end_an_accepted_call() -> None:
    accepted = MergeAccepted(tip=TIP, at=MOMENT, queued="the merge queue")
    removed = Event(id="removal", at=MOMENT + timedelta(seconds=1))
    pull = replace(SEEN, head=TIP, dequeued="a check failed", queue_event=removed)
    found = reconcile_queue.queued(opened(accepted=accepted), facing(pull=pull))
    assert code_of(found) == "queued"


def test_a_different_head_merged_after_a_lost_reply_is_external_and_uncovered() -> None:
    record = opened(intent=INTENT)
    other = replace(DONE, head=OTHER, merged_head=OTHER)
    found = reconcile.reconciled(record, facing(pull=other), INTENT, SAME)

    assert isinstance(found, Merged)
    assert (found.by, found.via) == ("owner", "github")
    assert found.uncovered is not None
    assert TIP in found.uncovered and OTHER in found.uncovered
    assert not found.text_updated


def test_a_queue_entry_at_a_different_head_does_not_answer_the_intent() -> None:
    added = Event(id="entry", at=MOMENT + timedelta(seconds=1), head=OTHER)
    other = replace(SEEN, head=OTHER, queued="the merge queue", queue_event=added)
    found = reconcile.reconciled(
        opened(intent=INTENT), facing(pull=other), INTENT, SAME
    )

    assert code_of(found) == "intent"


def test_a_queue_entry_carries_its_own_head() -> None:
    added = Event(id="entry", at=MOMENT + timedelta(seconds=1), head=OTHER)
    pull = replace(SEEN, queued="the merge queue", queue_event=added)
    found = reconcile.reconciled(opened(intent=INTENT), facing(pull=pull), INTENT, SAME)

    assert code_of(found) == "intent"


def test_a_removal_after_the_call_cannot_match_an_entry_from_before_it() -> None:
    prior = Event(id="prior-entry", at=MOMENT - timedelta(seconds=1), head=TIP)
    removed = Event(id="removal", at=MOMENT + timedelta(seconds=1), head=TIP)
    pull = replace(
        SEEN, dequeued="a check failed", queue_event=removed, queue_entered=prior
    )
    found = reconcile.reconciled(opened(intent=INTENT), facing(pull=pull), INTENT, SAME)

    assert code_of(found) == "intent"


def test_a_queue_entry_already_visible_in_the_same_second_cannot_answer_the_call() -> (
    None
):
    entry = Event(id="visible-entry", at=MOMENT, head=TIP)
    intent = replace(INTENT, queue_before=entry.id)
    pull = replace(SEEN, queued="the merge queue", queue_event=entry)
    found = reconcile.reconciled(opened(intent=intent), facing(pull=pull), intent, SAME)

    assert code_of(found) == "intent"
