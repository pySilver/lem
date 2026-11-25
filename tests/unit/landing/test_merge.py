"""The merge (`model/landing/merge.py`, `merge_asked.py`, `merge_evidence.py`): who may merge,
what is read again under the merge lock before the intent, the owner's word for the tip he saw,
his standing merge, GitHub's refusal of a tip, the subject of a squash, and what a refusal for a
moved base keeps (`landing.md` C, D, E and H 2)."""

from typing import TYPE_CHECKING

import pytest
from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.landing import merge, merge_call, merge_standing
from lem.model.landing.merge_asked import Asked
from lem.model.landing.world import Rules
from lem.records.landing.merge import MergeIntent, Refused
from lem.records.landing.propose import MergeRead, Standing
from lem.records.landing.review import Finding
from lem.records.task import Shape
from unit.landing.merges import (
    BY_MERGER,
    BY_OWNER,
    MOVED,
    MOVED_TREE,
    SUBJECT,
    alone,
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
MUST = Finding(
    id="r1.2", level="must-fix", where="a.py", title="no", what="it", against="over"
)


def test_the_merge_agent_merges_a_green_request_on_its_reads_merge() -> None:
    made = merge.decide(opened(), facing(), BY_MERGER, TREE)
    assert isinstance(made, merge_call.Merging)
    assert made.intent == MergeIntent(tip=TIP, by="merger", via="server", at=MOMENT)
    assert (made.method, made.subject) == ("squash", SUBJECT)
    assert made.body == "Lem task: fix-the-login"


@pytest.mark.parametrize(
    ("landing", "shape", "rules", "why"),
    [
        ({"reviews": (replace(REVIEWED, findings=(MUST,)),)}, None, None, "not green"),
        (
            {"proposed": replace(OPENED["proposed"], careful=True)},
            None,
            None,
            "careful",
        ),
        ({}, ("money",), None, "not green"),
        ({"reviews": (replace(REVIEWED, careful=None),)}, None, None, "careful call"),
        ({}, None, Rules(base="main", land="owner", commands=("true",)), "branch.land"),
        ({"reads": (replace(READ, verdict="call"),)}, None, None, "calls the owner"),
        ({"reads": ()}, None, None, "calls the owner"),
    ],
    ids=[
        "not green",
        "careful proposal",
        "careful shape",
        "no careful call",
        "the owner lands",
        "the read calls him",
        "no read",
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
    assert isinstance(merge.decide(record, world, BY_OWNER, TREE), merge_call.Merging)


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
    assert isinstance(on_safe, merge_call.Merging)
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
    assert isinstance(
        merge.decide(opened(), empty, BY_MERGER, TREE), merge_call.Merging
    )


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
    assert isinstance(made, merge_call.Merging)
    assert (made.method, made.subject, made.body) == ("rebase", "", "")


def test_after_githubs_refusal_only_the_owners_word_merges_that_tip() -> None:
    refused = Refused(
        tip=TIP, source="github", kind="rule", line="checks", by="merger", at=MOMENT
    )
    record = opened(refused=refused)
    assert code_of(merge.decide(record, facing(), BY_MERGER, TREE)) == "github"
    assert isinstance(
        merge.decide(record, facing(), BY_OWNER, TREE), merge_call.Merging
    )
    lems = replace(refused, source="lem", kind="base")
    assert isinstance(
        merge.decide(opened(refused=lems), facing(), BY_MERGER, TREE),
        merge_call.Merging,
    )


def test_only_the_owners_own_word_refused_for_the_base_keeps_his_merge_standing() -> (
    None
):
    record = opened()
    refusal = merge.decide(record, moved(), BY_OWNER, TREE)
    assert code_of(refusal) == "base"
    assert isinstance(refusal, Refusal)
    held = merge_standing.kept(record, refusal, BY_OWNER, MOMENT)
    assert held is not None
    refused, standing = held
    assert (refused.source, refused.kind, refused.by, refused.tip) == (
        "lem",
        "base",
        "owner",
        TIP,
    )
    assert standing == Standing(
        tip=TIP, reasons_digest=merge_standing.digest_of(()), by_act="board", at=MOMENT
    )
    server = Asked(by="owner", via="server", standing=True, subject=SUBJECT)
    for asked in (BY_MERGER, server, replace(BY_OWNER, via="server")):
        found = merge_standing.kept(record, refusal, asked, MOMENT)
        assert found is None or found[1] is None, asked


def test_a_stale_tap_or_a_standing_merge_with_none_is_refused_before_the_base() -> None:
    stale = merge.decide(opened(), moved(), replace(BY_OWNER, tip=OTHER), TREE)
    assert code_of(stale) == "tip"
    server = Asked(by="owner", via="server", standing=True, subject=SUBJECT)
    assert code_of(merge.decide(opened(), moved(), server, TREE)) == "tip"


def test_the_merge_agents_refusals_by_lems_rules_are_kept_for_its_tip() -> None:
    record = opened()
    moved_head = merge.decide(
        record, facing(pull=replace(SEEN, head=OTHER)), BY_MERGER, TREE
    )
    assert isinstance(moved_head, Refusal)
    held = merge_standing.kept(record, moved_head, BY_MERGER, MOMENT)
    assert held is not None
    assert (held[0].kind, held[0].by, held[1]) == ("tip", "merger", None)
    assert moved_head.fix in held[0].line
    rule = merge.decide(alone(), facing(), BY_MERGER, TREE)
    assert isinstance(rule, Refusal)
    kept_rule = merge_standing.kept(alone(), rule, BY_MERGER, MOMENT)
    assert kept_rule is not None
    assert kept_rule[0].kind == "rule"
    assert merge_standing.kept(record, moved_head, BY_OWNER, MOMENT) is None


def test_under_the_lock_a_push_of_another_commit_or_another_pull_request_is_refused() -> (
    None
):
    pushed = opened(pushed=OTHER)
    assert code_of(merge.decide(pushed, facing(), BY_OWNER, TREE)) == "tip"
    elsewhere = facing(pull=replace(SEEN, url="https://github.com/other/repo/pull/1"))
    assert code_of(merge.decide(opened(), elsewhere, BY_OWNER, TREE)) == "no-pull"


def test_the_merge_agent_reads_its_greenness_again_under_the_lock() -> None:
    record = alone()
    kept = record.landing
    assert kept is not None
    still = replace(record, landing=replace(kept, proposed=OPENED["proposed"]))
    assert code_of(merge.decide(still, facing(), BY_MERGER, TREE)) == "merger-rule"


def test_the_brief_says_who_merges_by_the_rules_before_any_verdict() -> None:
    first = opened(reads=())
    assert merge.authority(first, facing()) is not None
    assert merge.authority(first, facing(), verdict=False) is None
    assert merge.authority(alone(reads=()), facing(), verdict=False) is not None


def test_the_owners_standing_merge_goes_while_its_reasons_are_the_same() -> None:
    record = alone()
    proposed = record.landing.proposed if record.landing else None
    assert proposed is not None
    standing = Standing(
        tip=TIP,
        reasons_digest=merge_standing.digest_of(proposed.reasons),
        by_act="board",
        at=MOMENT,
    )
    stands = alone(standing=standing)
    server = Asked(by="owner", via="server", standing=True, subject=SUBJECT)
    made = merge.decide(stands, facing(), server, TREE)
    assert isinstance(made, merge_call.Merging)
    assert made.intent.by == "owner"
    other = replace(standing, reasons_digest=merge_standing.digest_of(("another",)))
    ended = alone(standing=other)
    assert code_of(merge.decide(ended, facing(), server, TREE)) == "tip"
    assert merge_standing.standing_of(ended) is None


def test_the_owners_word_merges_a_request_that_is_not_green() -> None:
    red = alone()
    assert code_of(merge.decide(red, facing(), BY_MERGER, TREE)) == "merger-rule"
    made = merge.decide(red, facing(), BY_OWNER, TREE)
    assert isinstance(made, merge_call.Merging)
    assert made.intent.by == "owner"
