"""The merge (`model/landing/merge.py`, `merge_asked.py`, `merge_evidence.py`): who may merge,
what is read again under the merge lock before the intent, the owner's word for the tip he saw,
his standing merge, GitHub's refusal of a tip, the subject of a squash, and what a refusal for a
moved base keeps (`landing.md` C, D, E and H 2)."""

from datetime import timedelta
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest
from inline_snapshot import snapshot
from msgspec.structs import replace

from lem.app.landing import merge as merge_app
from lem.app.landing import merge_called, merge_world
from lem.kernel.errors import Refusal
from lem.model.landing import merge, merge_asked, merge_call, merge_standing, propose
from lem.model.landing.merge_asked import Asked
from lem.model.landing.queue_evidence import Event
from lem.model.landing.world import Rules
from lem.records.landing.merge import MergeIntent, Refused
from lem.records.landing.propose import MergeRead, OwnerMerge, Standing
from lem.records.landing.review import Counts
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


def refusal_words(found: object) -> tuple[str, str, str]:
    """The refusal and its exact way on for the owner."""
    assert isinstance(found, Refusal), found
    return found.code, found.why, found.fix


def test_the_merge_agent_merges_a_green_request_on_its_reads_merge() -> None:
    made = merge.decide(opened(), facing(), BY_MERGER, TREE)
    assert isinstance(made, merge_call.Merging)
    assert made.intent == MergeIntent(
        tip=TIP, by="merger", via="server", at=MOMENT, queue_before=""
    )
    assert (made.method, made.subject) == ("squash", SUBJECT)
    assert made.body == "Lem task: fix-the-login"


@pytest.mark.parametrize(
    ("landing", "shape", "rules", "why"),
    [
        (
            {
                "reviews": (
                    replace(
                        REVIEWED, findings=(), counts=Counts(must_fix=1), to_file=()
                    ),
                )
            },
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
    assert refusal_words(found) == snapshot(
        (
            "target",
            "the pull request https://github.com/o/p/pull/1 is on release on GitHub, not on main, the base of the task: its base was changed there; nothing was merged",
            "gh pr edit 1 --base main, then lem land merge fix-the-login again",
        )
    )


@pytest.mark.parametrize(
    ("changes", "code"),
    [
        ({"pull": replace(SEEN, base="release")}, "target"),
        ({"pull": replace(SEEN, head=OTHER)}, "tip"),
        ({"tip": OTHER}, "tip"),
    ],
)
def test_a_moved_base_cannot_hide_a_wrong_destination_or_head(
    changes: dict[str, object], code: str
) -> None:
    record = opened()
    refused = merge.decide(record, moved(**changes), BY_OWNER, TREE)
    assert isinstance(refused, Refusal)
    assert refused.code == code
    assert merge_standing.kept(record, refused, BY_OWNER, MOMENT) is None
    if code == "target":
        assert refused.fix.startswith("gh pr edit 1 --base main")


def test_a_moved_base_merges_only_on_a_safe_read_that_covers_it_now() -> None:
    assert refusal_words(merge.decide(opened(), moved(), BY_OWNER, TREE)) == snapshot(
        (
            "base",
            "the base moved after the checks ran: the approved change needs checks on its new base",
            "lem land next fix-the-login names the steps to rebase and check it",
        )
    )
    rules = replace(moved().rules, base="stable")
    assert refusal_words(
        merge.decide(opened(), moved(rules=rules), BY_MERGER, TREE)
    ) == snapshot(
        (
            "base",
            "origin's main moved after the checks ran, and no read of the merge agent covers main at aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa as safe: nothing was merged",
            "lem land merge-review fix-the-login writes the brief of what moved; a fresh merge agent reads it, and on `Base: safe.` the merge goes on that base",
        )
    )
    on_safe = merge.decide(opened(reads=(READ, SAFE)), moved(), BY_MERGER, TREE)
    assert isinstance(on_safe, merge_call.Merging)
    assert (
        code_of(merge.decide(opened(reads=(READ, SAFE)), moved(), BY_OWNER, TREE))
        == "base"
    )
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
    assert code_of(merge.decide(opened(), empty, BY_OWNER, TREE)) == "base"


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
    assert refusal_words(merge.decide(opened(), keep, BY_OWNER, TREE)) == snapshot(
        (
            "message",
            'branch.history is "keep": the branch\'s own commits land, with no subject',
            "run it again with no --message",
        )
    )
    made = merge.decide(opened(), keep, replace(BY_OWNER, subject=None), TREE)
    assert isinstance(made, merge_call.Merging)
    assert (made.method, made.subject, made.body) == ("rebase", "", "")
    assert made.intent == MergeIntent(
        tip=TIP, by="owner", via="board", at=MOMENT, queue_before=""
    )


def test_after_githubs_refusal_only_the_owners_word_merges_that_tip() -> None:
    refused = Refused(
        tip=TIP, source="github", kind="rule", line="checks", by="merger", at=MOMENT
    )
    record = opened(refused=refused)
    assert refusal_words(merge.decide(record, facing(), BY_MERGER, TREE)) == snapshot(
        (
            "github",
            "GitHub refused the merge of 1111111111111111111111111111111111111111: checks; it is not tried again unasked",
            "the owner acts on GitHub, then merges it on his word",
        )
    )
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
    assert (refused.source, refused.kind, refused.by, refused.tip, refused.at) == (
        "lem",
        "base",
        "owner",
        TIP,
        MOMENT,
    )
    assert standing == Standing(
        tip=TIP,
        reasons_digest=merge_standing.digest_of((), OPENED["proposed"].contract),
        by_act="board",
        at=MOMENT,
    )
    server = Asked(by="owner", via="server", standing=True, subject=SUBJECT)
    for asked in (BY_MERGER, server, replace(BY_OWNER, via="server")):
        found = merge_standing.kept(record, refusal, asked, MOMENT)
        assert found is None or found[1] is None, asked


def test_a_stale_tap_or_a_standing_merge_with_none_is_refused_before_the_base() -> None:
    stale = merge.decide(opened(), moved(), replace(BY_OWNER, tip=OTHER), TREE)
    assert refusal_words(stale) == snapshot(
        (
            "tip",
            "the owner's merge names 9999999999999999999999999999999999999999, and the proposal is 1111111111111111111111111111111111111111: nothing was merged",
            "the owner reads the pull request as it is now (lem land next fix-the-login), and merges the tip he saw",
        )
    )
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
    assert (
        merge_standing.kept(
            replace(record, landing=None), moved_head, BY_MERGER, MOMENT
        )
        is None
    )
    assert (
        merge_standing.kept(opened(proposed=None), moved_head, BY_MERGER, MOMENT)
        is None
    )
    lost_reply = Refusal("intent", "a reply went missing", "check GitHub")
    assert merge_standing.kept(record, lost_reply, BY_MERGER, MOMENT) is None


def test_under_the_lock_a_push_of_another_commit_or_another_pull_request_is_refused() -> (
    None
):
    pushed = opened(pushed=OTHER)
    assert refusal_words(merge.decide(pushed, facing(), BY_OWNER, TREE)) == snapshot(
        (
            "tip",
            "the task's branch is at 1111111111111111111111111111111111111111 and Lem pushed 9999999999999999999999999999999999999999 last, not the proposed 1111111111111111111111111111111111111111",
            "lem land next fix-the-login names the new round",
        )
    )
    elsewhere = facing(pull=replace(SEEN, url="https://github.com/other/repo/pull/1"))
    assert refusal_words(merge.decide(opened(), elsewhere, BY_OWNER, TREE)) == snapshot(
        (
            "no-pull",
            "the forge shows https://github.com/other/repo/pull/1, not the pull request on record",
            "lem land next fix-the-login",
        )
    )


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
        reasons_digest=merge_standing.digest_of(proposed.reasons, proposed.contract),
        by_act="board",
        at=MOMENT,
    )
    stands = alone(standing=standing)
    server = Asked(by="owner", via="server", standing=True, subject=SUBJECT)
    made = merge.decide(stands, facing(), server, TREE)
    assert isinstance(made, merge_call.Merging)
    assert made.intent.by == "owner"
    other = replace(
        standing,
        reasons_digest=merge_standing.digest_of(("another",), proposed.contract),
    )
    ended = alone(standing=other)
    assert code_of(merge.decide(ended, facing(), server, TREE)) == "tip"
    assert merge_standing.standing_of(ended) is None


def test_the_owners_word_merges_a_request_that_is_not_green() -> None:
    red = alone()
    assert code_of(merge.decide(red, facing(), BY_MERGER, TREE)) == "merger-rule"
    made = merge.decide(red, facing(), BY_OWNER, TREE)
    assert isinstance(made, merge_call.Merging)
    assert made.intent.by == "owner"


def approved_with_hardware_key(record: Record) -> Record:
    criteria = record.task.criteria
    approved = criteria.approvals[-1]
    lines = (
        replace(approved.criteria[0], text="The login works with a hardware key."),
    )
    later = replace(approved, number=2, criteria=lines)
    updated = replace(criteria, approvals=(*criteria.approvals, later), criteria=lines)
    return replace(record, task=replace(record.task, criteria=updated))


def test_a_carried_standing_merge_ends_when_the_approved_criteria_change() -> None:
    proposal = OPENED["proposed"]
    before = opened()
    refused = merge.decide(before, moved(), BY_OWNER, TREE)
    assert isinstance(refused, Refusal) and refused.code == "base"
    kept = merge_standing.kept(before, refused, BY_OWNER, MOMENT)
    assert kept is not None and kept[1] is not None
    carried = replace(
        proposal, owner_merge=OwnerMerge(state="stands", why="the rebase carried")
    )
    authorization = replace(kept[1], tip=OTHER)
    record = opened(
        standing=authorization,
        proposed=carried,
        reads=(READ, SAFE),
        checked=replace(CHECKED, base=MOVED),
    )
    server = Asked(by="owner", via="server", standing=True, subject=SUBJECT)
    assert isinstance(merge.decide(record, moved(), server, TREE), merge_call.Merging)
    changed = approved_with_hardware_key(record)
    assert code_of(merge.decide(changed, moved(), server, TREE)) == "tip"


def test_a_stale_standing_merge_stops_before_the_forge_call() -> None:
    before = opened()
    refused = merge.decide(before, moved(), BY_OWNER, TREE)
    assert isinstance(refused, Refusal) and refused.code == "base"
    kept = merge_standing.kept(before, refused, BY_OWNER, MOMENT)
    assert kept is not None and kept[1] is not None
    record = opened(
        standing=kept[1], reads=(READ, SAFE), checked=replace(CHECKED, base=MOVED)
    )
    server = Asked(by="owner", via="server", standing=True, subject=SUBJECT)
    assert isinstance(merge.decide(record, moved(), server, TREE), merge_call.Merging)
    changed = approved_with_hardware_key(record)
    context = Mock(record=changed, world=moved())
    context.write.return_value = changed
    with (
        patch.object(merge_world, "checks_tree", return_value=TREE),
        patch.object(merge_called, "answered"),
        pytest.raises(Refusal, match="no merge of the owner's stands") as stopped,
    ):
        merge_app.locked(context, server)
    assert stopped.value.code == "tip"
    context.ports.forge.merge.assert_not_called()
    context.write.assert_not_called()


@pytest.mark.parametrize(
    ("changed", "delay"),
    [(True, timedelta()), (True, timedelta(seconds=1)), (False, timedelta(seconds=1))],
    ids=("changed-in-the-same-second", "changed-later", "same-criteria-approved-again"),
)
def test_the_merge_agent_needs_the_criteria_the_proposal_used(
    delay: timedelta, *, changed: bool
) -> None:
    record = opened()
    landing = record.landing
    assert landing is not None
    proposal = propose.made(record, facing(), ())
    record = replace(record, landing=replace(landing, proposed=proposal))
    assert isinstance(
        merge.decide(record, facing(), BY_MERGER, TREE), merge_call.Merging
    )
    criteria = record.task.criteria
    text = "The login works with a hardware key."
    approved = criteria.approvals[-1]
    lines = (
        (replace(approved.criteria[0], text=text),) if changed else approved.criteria
    )
    later = replace(approved, number=2, at=proposal.at + delay, criteria=lines)
    again = replace(criteria, approvals=(*criteria.approvals, later), criteria=lines)
    current = replace(record, task=replace(record.task, criteria=again))
    decided = merge.decide(current, facing(), BY_MERGER, TREE)
    if changed:
        assert code_of(decided) == "merger-rule"
        assert merge.authority(current, facing()) == merge.MOVED
    else:
        assert isinstance(decided, merge_call.Merging)


def test_the_squash_refusal_names_the_subject_from_the_report() -> None:
    asked = replace(BY_OWNER, subject=None)
    assert refusal_words(merge.decide(opened(), facing(), asked, TREE)) == (
        "message",
        'branch.history is "squash": the one commit takes the subject of the report',
        "pass --message with the commit subject of the builder's report",
    )


def test_a_merge_call_cannot_claim_the_queue_entry_that_already_exists() -> None:
    entry = Event(id="prior-entry", at=MOMENT, head=TIP)
    world = facing(pull=replace(SEEN, queue_event=entry))
    made = merge.decide(opened(), world, BY_MERGER, TREE)
    assert isinstance(made, merge_call.Merging)
    assert made.intent.queue_before == "prior-entry"


def test_closed_pull_no_pull_or_red_checks_name_the_next_step() -> None:
    closed = facing(pull=replace(SEEN, state="closed"))
    assert refusal_words(merge.decide(opened(), closed, BY_OWNER, TREE)) == snapshot(
        (
            "closed",
            "the pull request https://github.com/o/p/pull/1 is closed on GitHub: nothing was merged",
            "lem land merged fix-the-login writes it down first",
        )
    )
    assert refusal_words(
        merge.decide(opened(), facing(pull=None), BY_OWNER, TREE)
    ) == snapshot(
        (
            "no-pull",
            "the forge shows no pull request, not the pull request on record",
            "lem land next fix-the-login",
        )
    )
    red = opened(checked=replace(CHECKED, outcome="red"))
    assert refusal_words(merge.decide(red, facing(), BY_OWNER, TREE)) == snapshot(
        (
            "checks-changed",
            "no passed run of the checks covers 1111111111111111111111111111111111111111 with the checks as they are now: the checks of this tip are red",
            "lem land next fix-the-login names the step that runs them",
        )
    )
    wrong_head = facing(pull=replace(SEEN, head=OTHER))
    assert refusal_words(
        merge.decide(opened(), wrong_head, BY_OWNER, TREE)
    ) == snapshot(
        (
            "tip",
            "the pull request's head is 9999999999999999999999999999999999999999, not the proposed 1111111111111111111111111111111111111111",
            "lem land next fix-the-login names the new round",
        )
    )


def test_a_blank_subject_cannot_reach_the_forge_for_a_squash() -> None:
    asked = replace(BY_OWNER, subject="")
    assert refusal_words(merge.decide(opened(), facing(), asked, TREE)) == (
        "message",
        'branch.history is "squash": the one commit takes the subject of the report',
        "pass --message with the commit subject of the builder's report",
    )
    kept = merge.decide(opened(), facing(rules=KEEP), asked, TREE)
    assert isinstance(kept, merge_call.Merging)
    assert (kept.method, kept.subject) == ("rebase", "")


def test_the_owner_list_uses_the_proposals_authority_until_it_has_current_settings() -> (
    None
):
    proposal = replace(OPENED["proposed"], who_acts="owner")
    record = opened(proposed=proposal)
    assert merge.authority(record) == (
        'branch.land is "owner" in .lem/settings.toml: the owner merges every task'
    )
    assert merge.authority(record, land="agent") is None
    assert merge.authority(opened()) is None


def test_the_merge_refusal_of_a_closed_task_names_its_status_and_next_step() -> None:
    assert refusal_words(merge.decide(task("ready"), facing(), BY_OWNER, TREE)) == (
        "status",
        "fix-the-login is ready, with no open pull request",
        "lem land next fix-the-login",
    )


def test_a_merge_agents_refusal_tells_the_owner_who_can_merge() -> None:
    record = opened(reads=(replace(READ, verdict="call"),))
    assert refusal_words(merge.decide(record, facing(), BY_MERGER, TREE)) == (
        "merger-rule",
        "the merge agent may not merge: the merge agent's read of this tip and base calls the owner",
        "the owner merges it, on his word",
    )


def test_an_old_safe_read_does_not_go_into_the_squash_on_the_checks_base() -> None:
    record = opened(reads=(READ, SAFE))
    made = merge.decide(record, facing(), BY_OWNER, TREE)
    assert isinstance(made, merge_call.Merging)
    assert made.body == "Lem task: fix-the-login"


def test_a_stale_merge_word_without_any_proposal_can_merge_nothing() -> None:
    record = task("ready")
    refused = merge_asked.tip_refusal(record, BY_OWNER, facing())
    assert refused is not None
    assert refused.why == (
        f"the owner's merge names {TIP}, and the proposal is None: nothing was merged"
    )
