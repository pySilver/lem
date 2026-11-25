"""What each stage of the plain landing decides from the record and the world, and what it refuses
(`landing.md` F), with the code of the step that builds what the plain path leaves out."""

from typing import TYPE_CHECKING

import pytest
from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.landing import (
    base,
    checks,
    clean,
    green,
    invariants,
    merge,
    mergeread,
    phases,
    propose,
    reconcile,
    start,
)
from lem.model.landing.world import Rules
from lem.records.criterion import CriterionTest
from lem.records.landing.merge import MergeAccepted, Merged, MergeIntent, Refused
from lem.records.landing.review import Finding
from lem.records.task import Shape
from unit.landing.worlds import (
    BASE,
    CHECKED,
    MERGE,
    MERGED,
    MOMENT,
    OPENED,
    OTHER,
    PREPARED,
    READ,
    REVIEWED,
    RULES,
    SEEN,
    TIP,
    task,
    world,
)

if TYPE_CHECKING:
    from lem.model.landing.world import Merger
    from lem.records.record import Record

INTENT = MergeIntent(tip=TIP, by="merger", via="session", at=MOMENT)


def code_of(found: object) -> str:
    """The code of a refusal; a case fails on anything else."""
    assert isinstance(found, Refusal), found
    return found.code


def test_start_takes_a_ready_task_and_refuses_the_rest_by_its_code() -> None:
    started = start.decide(task("ready"), world(), conflicting=False)
    assert not isinstance(started, Refusal)
    assert (started.round, started.branch, started.base_ref) == (
        1,
        "docs/fix-the-login",
        "main",
    )
    assert (
        code_of(start.decide(task("building"), world(), conflicting=False)) == "status"
    )
    assert (
        code_of(start.decide(task("ready"), world(clean=False), conflicting=False))
        == "dirty"
    )
    assert (
        code_of(start.decide(task("ready"), world(tip=None), conflicting=False))
        == "no-worktree"
    )
    bare = world(rules=Rules(base="main"))
    assert code_of(start.decide(task("ready"), bare, conflicting=False)) == "no-checks"
    conflicting = start.decide(task("ready"), world(), conflicting=True)
    assert code_of(conflicting) == "not-built"
    assert isinstance(conflicting, Refusal)
    assert "land-base" in conflicting.fix


def test_base_rebases_only_a_tip_without_origins_base_and_refuses_a_teammates_commit() -> (
    None
):
    record = task(**PREPARED)
    assert base.decide(record, world()) == "onto"
    assert base.decide(record, world(base_in_tip=False)) == "rebase"
    assert code_of(base.decide(record, world(rebasing=True))) == "rebase-in-progress"
    assert code_of(base.decide(record, world(remote=OTHER))) == "teammate"
    assert base.decide(record, world(remote=TIP, remote_in_tip=True)) == "onto"
    pushed = task(**{**PREPARED, "pushed": OTHER})
    assert base.decide(pushed, world(remote=OTHER, base_in_tip=False)) == "rebase"


def test_checks_refuse_serial_commands_and_a_red_tip_as_later_steps() -> None:
    assert checks.decide(task(**PREPARED), world()) is None
    serial = world(rules=Rules(base="main", commands=("true",), serial=("e2e",)))
    assert code_of(checks.decide(task(**PREPARED), serial)) == "not-built"
    red = task(**{**PREPARED, "checked": replace(CHECKED, outcome="red")})
    assert code_of(checks.decide(red, world())) == "not-built"
    assert checks.left(clean=True) is None
    assert code_of(checks.left(clean=False)) == "not-built"
    assert checks.inputs(RULES) != checks.inputs(Rules(base="main", commands=("make",)))


def test_green_names_each_reason_it_is_not() -> None:
    assert green.reasons(task(**PREPARED)) == ()
    must = Finding(
        id="r1.2", level="must-fix", where="a", title="t", what="w", against="over"
    )
    careful = replace(REVIEWED, careful=True, careful_why="money", findings=(must,))
    red = replace(CHECKED, outcome="red")
    record = task(**{**PREPARED, "reviews": (careful,), "checked": red})
    test = CriterionTest(command="pytest", files=("t.py",))
    tested = replace(record.task.criteria.criteria[0], no_test=None, tests=(test,))
    criteria = replace(record.task.criteria, criteria=(tested,), approvals=())
    record = replace(record, task=replace(record.task, criteria=criteria))
    assert green.reasons(record) == (
        "the checks did not pass",
        "criterion 1's test was not seen to fail on the base and pass on the tip",
        "nobody approved the criteria",
        "the review left 1 must-fix",
        "the change is careful: money",
    )


def test_propose_pushes_a_tip_origin_lacks_and_adopts_only_a_request_lem_pushed() -> (
    None
):
    record = task(**PREPARED)
    made = propose.decide(record, world())
    assert not isinstance(made, Refusal)
    assert (made.push, made.adopt, made.proposed.green, made.proposed.who_acts) == (
        True,
        None,
        True,
        "merger",
    )
    pushed = task(**{**PREPARED, "pushed": TIP})
    cut = propose.decide(pushed, world(remote=TIP, candidates=(SEEN,)))
    assert not isinstance(cut, Refusal)
    assert (cut.push, cut.adopt) == (False, SEEN)
    before = world(remote=TIP, candidates=(SEEN,))
    assert code_of(propose.decide(record, before)) == "foreign-pull"
    two = world(candidates=(SEEN, replace(SEEN, number=2, head=OTHER)))
    assert code_of(propose.decide(pushed, two)) == "foreign-pull"
    guarded = world(
        rules=Rules(base="main", commands=("true",), protected=("docs/fix-the-login",))
    )
    assert code_of(propose.decide(record, guarded)) == "protected"
    owner = propose.decide(
        record, world(rules=Rules(base="main", land="owner", commands=("true",)))
    )
    assert not isinstance(owner, Refusal)
    assert owner.proposed.who_acts == "owner"


def test_a_careful_request_is_not_green_and_the_owner_merges_it() -> None:
    record = task(**PREPARED)
    shape = Shape(type="docs", why="w", track="small", careful=("money",))
    careful = replace(record, task=replace(record.task, shape=shape))
    assert green.reasons(careful) == ("the request is careful: money",)
    made = propose.decide(careful, world())
    assert not isinstance(made, Refusal)
    assert made.proposed.who_acts == "owner"


def test_a_merge_read_takes_a_verdict_for_the_tip_and_base_of_its_brief() -> None:
    record = task("open", **OPENED)
    read = mergeread.decide(record, world(), "Merge.\n\nIt holds.", (TIP, BASE))
    assert not isinstance(read, Refusal)
    assert (read.verdict, read.base, read.attempts) == ("merge", BASE, 1)
    assert (
        code_of(mergeread.decide(record, world(), "merge", (OTHER, BASE))) == "old-tip"
    )
    assert (
        code_of(mergeread.decide(record, world(base=OTHER), "merge", (TIP, BASE)))
        == "old-tip"
    )
    assert (
        code_of(mergeread.decide(record, world(), "maybe", (TIP, BASE))) == "not-built"
    )
    assert (
        code_of(mergeread.decide(task(**PREPARED), world(), "merge", (TIP, BASE)))
        == "no-pull"
    )
    assert mergeread.verdict_of("**call** the owner") == "call"
    assert mergeread.verdict_of("Verdict: merge.\nBase: safe.") == "merge"
    assert mergeread.verdict_of("**Verdict:** call. The owner reads it.") == "call"
    assert mergeread.verdict_of("") is None


@pytest.mark.parametrize(
    ("record", "facts", "by", "code"),
    [
        (task(**PREPARED), {}, "merger", "status"),
        (
            task("open", **OPENED),
            {"pull": replace(SEEN, base="release")},
            "merger",
            "not-built",
        ),
        (task("open", **OPENED), {"pull": replace(SEEN, head=OTHER)}, "merger", "tip"),
        (
            task("open", **OPENED),
            {"pull": SEEN, "rules": Rules(base="main", commands=("make",))},
            "merger",
            "checks-changed",
        ),
        (task("open", **OPENED), {"pull": SEEN}, "merger", "merger-rule"),
        (task("open", **OPENED), {"pull": SEEN}, "owner", "tip"),
        (
            task("open", **OPENED),
            {
                "pull": SEEN,
                "rules": Rules(base="main", history="keep", commands=("true",)),
            },
            "merger",
            "not-built",
        ),
    ],
)
def test_a_merge_is_refused_off_its_proposal_or_its_authority(
    record: Record, facts: dict[str, object], by: Merger, code: str
) -> None:
    decided = merge.decide(record, world(**facts), by, ("session", None))
    assert code_of(decided) == code


def test_a_merge_with_its_authority_is_an_intent_for_the_proposed_tip() -> None:
    read = task("open", **{**OPENED, "reads": (READ,)})
    by_merger = merge.decide(read, world(pull=SEEN), "merger", ("server", None))
    assert by_merger == MergeIntent(tip=TIP, by="merger", via="server", at=MOMENT)
    by_owner = merge.decide(
        task("open", **OPENED), world(pull=SEEN), "owner", ("session", TIP)
    )
    assert by_owner == MergeIntent(tip=TIP, by="owner", via="session", at=MOMENT)


def test_an_intent_becomes_the_merge_the_queue_or_a_question_for_the_owner() -> None:
    record = task("open", **{**OPENED, "intent": INTENT, "reads": (READ,)})
    done = replace(
        SEEN, state="merged", merge_commit=MERGE, merged_head=TIP, base_parent=BASE
    )
    landed = reconcile.reconciled(record, world(pull=done, base=MERGE), INTENT)
    assert landed == replace(MERGED, base_read=BASE)
    queued = reconcile.reconciled(
        record, world(pull=replace(SEEN, queued="queue")), INTENT
    )
    assert queued == MergeAccepted(tip=TIP, at=MOMENT, queued="queue")
    assert code_of(reconcile.reconciled(record, world(pull=SEEN), INTENT)) == "intent"
    closed = world(pull=replace(SEEN, state="closed"))
    assert code_of(reconcile.reconciled(record, closed, INTENT)) == "not-built"
    elsewhere = replace(done, base_parent=OTHER)
    moved = reconcile.landed(
        record, world(pull=elsewhere), elsewhere, ("owner", "github")
    )
    assert isinstance(moved, Merged)
    assert moved.uncovered is not None
    retargeted = replace(done, base="release")
    assert (
        code_of(reconcile.landed(record, world(), retargeted, ("owner", "github")))
        == "not-built"
    )


def test_clean_removes_only_what_the_forge_merged_and_keeps_a_branch_it_did_not() -> (
    None
):
    merged = task("landed", **{**OPENED, "phase": "merged", "merged": MERGED})
    sweep = clean.decide(merged, world(remote=TIP))
    assert sweep == clean.Sweep(worktree=True, branch=True, remote=True)
    gone = clean.decide(merged, world(tip=None, local=None))
    assert gone == clean.Sweep(worktree=False, branch=False, remote=False)
    later = clean.decide(merged, world(local=OTHER, remote=OTHER))
    assert isinstance(later, clean.Sweep)
    assert (later.branch, later.remote) == (False, False)
    assert later.branch_left is not None
    assert code_of(clean.decide(merged, world(clean=False))) == "dirty"
    assert code_of(clean.decide(task("open", **OPENED), world())) == "not-built"


def test_nothing_is_pushed_to_merged_from_or_deleted_on_a_protected_branch() -> None:
    rules = Rules(base="main", protected=("release",))
    assert invariants.protected("docs/x", rules, "pushes") is None
    assert invariants.protected("main", rules, "merges") is None
    assert code_of(invariants.protected("main", rules, "pushes")) == "protected"
    assert code_of(invariants.protected("release", rules, "deletes")) == "protected"


@pytest.mark.parametrize(
    ("facts", "landing", "code"),
    [
        ({"tip": OTHER}, {}, "tip"),
        ({}, {"checked": replace(CHECKED, outcome="red")}, "checks-changed"),
        ({}, {"checked": replace(CHECKED, tip=OTHER)}, "checks-changed"),
        ({"base": OTHER}, {}, "base"),
        (
            {"rules": Rules(base="main", commands=("true",), protected=("main",))},
            {},
            "protected",
        ),
    ],
    ids=[
        "local tip moved",
        "red checks",
        "checks of another tip",
        "base moved",
        "protected base",
    ],
)
def test_a_merge_is_refused_on_the_evidence_read_again_under_the_lock(
    facts: dict[str, object], landing: dict[str, object], code: str
) -> None:
    record = task("open", **{**OPENED, "reads": (READ,), **landing})
    decided = merge.decide(record, world(pull=SEEN, **facts), "owner", ("session", TIP))
    assert code_of(decided) == code


def test_githubs_refusal_of_the_proposed_tip_waits_for_the_owner() -> None:
    refused = Refused(
        tip=TIP, source="github", kind="rule", line="checks", by="merger", at=MOMENT
    )
    record = task("open", **{**OPENED, "reads": (READ,), "refused": refused})
    due = phases.due(record, world(pull=SEEN))
    assert due.step == "wait"
    assert "GitHub refused the merge of this tip: checks" in due.why


def test_a_branch_reset_under_its_recorded_base_makes_the_base_due_again() -> None:
    assert phases.due(task(**PREPARED), world(base_in_tip=False)).step == "base"
