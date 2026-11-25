"""The merge (`model/landing/merge.py`, `merge_asked.py`, `merge_evidence.py`): who may merge,
what is read again under the merge lock before the intent, the owner's word for the tip he saw,
his standing merge, GitHub's refusal of a tip, the subject of a squash, and what a refusal for a
moved base keeps (`landing.md` C, D, E and H 2)."""

from typing import TYPE_CHECKING

import pytest
from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.landing import merge, merge_evidence
from lem.model.landing.merge_asked import Asked
from lem.model.landing.world import Rules
from lem.records.landing.merge import MergeIntent, Refused
from lem.records.landing.propose import MergeRead, Standing
from lem.records.task import Shape
from unit.landing.merges import (
    BY_MERGER,
    BY_OWNER,
    MOVED,
    MOVED_TREE,
    SUBJECT,
    code_of,
    facing,
    moved,
    opened,
)
from unit.landing.worlds import (
    CHECKED,
    MOMENT,
    OPENED,
    OTHER,
    PREPARED,
    READ,
    REVIEWED,
    SEEN,
    TIP,
    TREE,
    task,
)

if TYPE_CHECKING:
    from lem.records.record import Record

SAFE = MergeRead(
    tip=TIP,
    base=MOVED,
    base_tree=MOVED_TREE,
    verdict="merge",
    base_call="safe",
    why="only README.md moved",
    at=MOMENT,
)
KEEP = Rules(base="main", history="keep", commands=("true",))
NOT_GREEN = ("the checks did not pass",)


def test_the_merge_agent_merges_a_green_request_on_its_reads_merge() -> None:
    made = merge.decide(opened(), facing(), BY_MERGER, TREE)
    assert isinstance(made, merge.Merging)
    assert made.intent == MergeIntent(tip=TIP, by="merger", via="server", at=MOMENT)
    assert (made.method, made.subject) == ("squash", SUBJECT)
    assert made.body == "Lem task: fix-the-login"


@pytest.mark.parametrize(
    ("landing", "shape", "rules", "why"),
    [
        (
            {"proposed": replace(OPENED["proposed"], reasons=NOT_GREEN)},
            None,
            None,
            "not green",
        ),
        (
            {"proposed": replace(OPENED["proposed"], careful=True)},
            None,
            None,
            "careful",
        ),
        ({}, ("money",), None, "careful"),
        ({"reviews": (replace(REVIEWED, careful=None),)}, None, None, "careful call"),
        ({}, None, Rules(base="main", land="owner", commands=("true",)), "branch.land"),
        ({"reads": (replace(READ, verdict="call"),)}, None, None, "calls the owner"),
        ({"reads": ()}, None, None, "calls the owner"),
    ],
)
def test_the_merge_agent_may_not_merge_what_somebody_should_look_at_first(
    landing: dict[str, object],
    shape: tuple[str, ...] | None,
    rules: Rules | None,
    why: str,
) -> None:
    record = opened(**landing)
    if shape is not None:
        careful = Shape(type="feat", why="w", track="small", careful=shape)
        record = replace(record, task=replace(record.task, shape=careful))
    world = facing(rules=rules) if rules else facing()
    found = merge.authority(record, world)
    assert found is not None
    assert why in found
    assert code_of(merge.decide(record, world, BY_MERGER, TREE)) == "merger-rule"
    assert merge.due(record, world).by == "owner"
    assert isinstance(merge.decide(record, world, BY_OWNER, TREE), merge.Merging)


@pytest.mark.parametrize(
    ("record", "facts", "code"),
    [
        (task(**PREPARED), {}, "status"),
        (opened(), {"pull": None}, "no-pull"),
        (opened(), {"pull": replace(SEEN, state="closed")}, "closed"),
        (opened(), {"pull": replace(SEEN, base="release")}, "target"),
        (opened(), {"pull": replace(SEEN, head=OTHER)}, "tip"),
        (opened(), {"tip": OTHER}, "tip"),
        (opened(checked=replace(CHECKED, outcome="red")), {}, "checks-changed"),
        (opened(checked=replace(CHECKED, tip=OTHER)), {}, "checks-changed"),
        (opened(), {"rules": Rules(base="main", commands=("make",))}, "checks-changed"),
        (
            opened(),
            {"rules": Rules(base="main", commands=("true",), protected=("main",))},
            "protected",
        ),
    ],
    ids=[
        "not open",
        "no pull request",
        "closed",
        "retargeted before the read",
        "another head",
        "local tip moved",
        "red checks",
        "checks of another tip",
        "commands changed",
        "protected base",
    ],
)
def test_a_merge_is_refused_on_the_evidence_read_again_under_the_lock(
    record: Record, facts: dict[str, object], code: str
) -> None:
    assert code_of(merge.decide(record, facing(**facts), BY_OWNER, TREE)) == code


def test_a_retarget_before_the_merge_names_the_edit_that_puts_it_back() -> None:
    found = merge.decide(
        opened(), facing(pull=replace(SEEN, base="release")), BY_OWNER, TREE
    )
    assert isinstance(found, Refusal)
    assert found.fix.startswith("gh pr edit 1 --base main")


def test_a_moved_base_merges_only_on_a_safe_read_that_covers_it_now() -> None:
    assert code_of(merge.decide(opened(), moved(), BY_OWNER, TREE)) == "base"
    assert code_of(merge.decide(opened(), moved(), BY_MERGER, TREE)) == "base"
    on_safe = merge.decide(opened(reads=(READ, SAFE)), moved(), BY_MERGER, TREE)
    assert isinstance(on_safe, merge.Merging)
    assert on_safe.body.startswith(
        "The checks ran on main at bbbbbbbbb; it merged on main at aaaaaaaaa"
    )
    assert on_safe.body.endswith("only README.md moved\n\nLem task: fix-the-login")
    later = moved(base="d" * 40, base_tree="0" * 40)
    assert (
        code_of(merge.decide(opened(reads=(READ, SAFE)), later, BY_MERGER, TREE))
        == "base"
    )
    another = replace(SAFE, base_call="another round")
    assert (
        code_of(merge.decide(opened(reads=(READ, another)), moved(), BY_OWNER, TREE))
        == "base"
    )


def test_a_revert_of_the_base_or_an_empty_commit_moves_nothing() -> None:
    empty = facing(base=MOVED)
    assert isinstance(merge.decide(opened(), empty, BY_MERGER, TREE), merge.Merging)


def test_a_careful_request_with_a_safe_read_still_calls_the_owner() -> None:
    careful = opened(
        reads=(READ, SAFE), proposed=replace(OPENED["proposed"], careful=True)
    )
    assert code_of(merge.decide(careful, moved(), BY_MERGER, TREE)) == "merger-rule"


@pytest.mark.parametrize(
    ("asked", "code"),
    [
        (replace(BY_OWNER, tip=OTHER), "tip"),
        (replace(BY_OWNER, tip=None), "tip"),
        (replace(BY_OWNER, tip="1234567"), "tip"),
        (replace(BY_MERGER, tip=OTHER), "tip"),
        (replace(BY_OWNER, standing=True, tip=None), "tip"),
        (replace(BY_OWNER, subject=None), "message"),
    ],
    ids=[
        "a stale tap",
        "no tip",
        "a short tip",
        "the merger's old tip",
        "no standing",
        "no subject",
    ],
)
def test_the_merge_as_asked_is_refused_and_no_intent_is_written(
    asked: Asked, code: str
) -> None:
    assert code_of(merge.decide(opened(), facing(), asked, TREE)) == code


def test_a_merge_that_keeps_the_branchs_commits_takes_no_subject_and_rebases() -> None:
    keep = facing(rules=KEEP)
    assert code_of(merge.decide(opened(), keep, BY_OWNER, TREE)) == "message"
    made = merge.decide(opened(), keep, replace(BY_OWNER, subject=None), TREE)
    assert isinstance(made, merge.Merging)
    assert (made.method, made.subject, made.body) == ("rebase", "", "")


def test_after_githubs_refusal_only_the_owners_word_merges_that_tip() -> None:
    refused = Refused(
        tip=TIP, source="github", kind="rule", line="checks", by="merger", at=MOMENT
    )
    record = opened(refused=refused)
    assert code_of(merge.decide(record, facing(), BY_MERGER, TREE)) == "github"
    assert isinstance(merge.decide(record, facing(), BY_OWNER, TREE), merge.Merging)
    lems = replace(refused, source="lem", kind="base")
    assert isinstance(
        merge.decide(opened(refused=lems), facing(), BY_MERGER, TREE), merge.Merging
    )


def test_a_refusal_for_the_base_keeps_lems_refusal_and_the_owners_merge_standing() -> (
    None
):
    landing = opened().landing
    assert landing is not None
    refusal = merge.decide(opened(), moved(), BY_OWNER, TREE)
    assert isinstance(refusal, Refusal)
    held = merge_evidence.kept(landing, refusal, ("owner", "board"), MOMENT)
    assert held is not None
    refused, standing = held
    assert (refused.source, refused.kind, refused.by, refused.tip) == (
        "lem",
        "base",
        "owner",
        TIP,
    )
    assert standing == Standing(
        tip=TIP, reasons_digest=merge_evidence.digest_of(()), by_act="board", at=MOMENT
    )
    by_merger = merge_evidence.kept(landing, refusal, ("merger", "server"), MOMENT)
    assert by_merger is not None
    assert by_merger[1] is None
    other = Refusal("tip", "another tip", "read it")
    assert merge_evidence.kept(landing, other, ("owner", "board"), MOMENT) is None


def test_the_owners_standing_merge_goes_while_its_reasons_are_the_same() -> None:
    proposed = replace(OPENED["proposed"], reasons=NOT_GREEN, green=False)
    standing = Standing(
        tip=TIP,
        reasons_digest=merge_evidence.digest_of(NOT_GREEN),
        by_act="board",
        at=MOMENT,
    )
    stands = opened(proposed=proposed, standing=standing)
    server = Asked(by="owner", via="server", standing=True, subject=SUBJECT)
    made = merge.decide(stands, facing(), server, TREE)
    assert isinstance(made, merge.Merging)
    assert made.intent.by == "owner"
    ended = opened(
        proposed=replace(proposed, reasons=("another reason",)), standing=standing
    )
    assert code_of(merge.decide(ended, facing(), server, TREE)) == "tip"
    assert ended.landing is not None
    assert merge_evidence.standing_of(ended.landing) is None
