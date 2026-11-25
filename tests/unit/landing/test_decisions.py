"""What each stage of the plain landing decides from the record and the world, and what it refuses
(`landing.md` F), with the code of the step that builds what the plain path leaves out."""

from typing import TYPE_CHECKING

import msgspec
import pytest
from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.landing import (
    checks,
    clean,
    filing,
    green,
    invariants,
    merge,
    mergeread,
    phases,
    reconcile,
    review,
    review_said,
)
from lem.model.landing.world import Rules
from lem.records.landing.merge import MergeAccepted, Merged, MergeIntent, Refused
from lem.records.landing.review import Finding, Named
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


def test_checks_refuse_serial_commands_and_a_red_tip_as_later_steps() -> None:
    assert checks.decide(task(**PREPARED), world()) is None
    serial = world(rules=Rules(base="main", commands=("true",), serial=("e2e",)))
    assert code_of(checks.decide(task(**PREPARED), serial)) == "not-built"
    red = task(**{**PREPARED, "checked": replace(CHECKED, outcome="red")})
    assert code_of(checks.decide(red, world())) == "not-built"
    assert checks.left(clean=True) is None
    assert code_of(checks.left(clean=False)) == "not-built"
    assert checks.inputs(RULES) != checks.inputs(Rules(base="main", commands=("make",)))


def said(**fields: object) -> review_said.Said:
    """A record of attempt 1 for `TIP`, in the form `prompts/review.md` gives, with
    `fields` over it."""
    base_said = review_said.Said(
        attempt=1, tip=TIP, kind="read", answered=("claude",), careful=False
    )
    return replace(base_said, **fields)


OUT = review_said.Outside(
    where="a.py", title="a nit", what="it", against="under", why="small"
)


def test_a_review_is_refused_under_its_floor_without_a_careful_call_or_careful_and_not_full() -> (
    None
):
    record = task(**{**PREPARED, "reviews": ()})
    made = review.decide(record, world(), said(outside=(OUT,), nit=2))
    assert not isinstance(made, Refusal)
    assert (made.attempt, made.tip, made.to_file) == (1, TIP, ("r1.1",))
    assert [finding.id for finding in made.findings] == ["r1.c1", "r1.c2", "r1.1"]
    assert (
        code_of(review.decide(record, world(), said(careful=None))) == "no-careful-call"
    )
    assert (
        code_of(review.decide(record, world(), said(careful=True)))
        == "careful-not-full"
    )
    shape = Shape(type="docs", why="a word", track="small", careful=("money",))
    careful = replace(record, task=replace(record.task, shape=shape))
    assert review.floor(careful) == "full"
    assert code_of(review.decide(careful, world(), said())) == "under-floor"


def test_a_review_of_another_attempt_or_tip_is_refused_and_its_must_fix_is_kept() -> (
    None
):
    record = task(**{**PREPARED, "reviews": ()})
    assert code_of(review.decide(record, world(), said(attempt=2))) == "attempt"
    assert code_of(review.decide(record, world(), said(tip=OTHER))) == "tip"
    failed = review.decide(record, world(), said(must_fix=1))
    assert not isinstance(failed, Refusal)
    assert review.must_fix(failed) == 1
    after = task(**{**PREPARED, "reviews": (failed,)})
    assert phases.due(after, world()).step == "read"
    assert review.floor(after) == "round"
    assert green.reasons(after, ()) == ("the review left 1 must-fix",)
    assert code_of(review.decide(after, world(), said(attempt=2))) == "under-floor"


def test_a_review_beyond_the_plain_path_is_refused_by_the_step_that_builds_it() -> None:
    record = task(**{**PREPARED, "reviews": ()})
    lowered = said(lowered=(Named(name="t.py", why="w"),))
    assert code_of(review.decide(record, world(), lowered)) == "not-built"
    held = said(outside=(replace(OUT, open="docs/backlog/a.md"),))
    assert code_of(review.decide(record, world(), held)) == "not-built"
    two = task(**{**PREPARED, "reviews": (REVIEWED, replace(REVIEWED, attempt=2))})
    third = said(attempt=3, kind="round")
    assert code_of(review.decide(two, world(), third)) == "not-built"
    silent = replace(REVIEWED, answered=())
    again = task(**{**PREPARED, "reviews": (silent,)})
    assert (
        code_of(review.decide(again, world(), said(attempt=2, answered=())))
        == "not-built"
    )


def test_a_review_record_with_a_key_the_prompt_does_not_name_is_refused() -> None:
    form = {"attempt": 1, "tip": TIP, "kind": "read", "careful": False}
    assert msgspec.json.decode(msgspec.json.encode(form), type=review_said.Said)
    with pytest.raises(msgspec.ValidationError, match="findings"):
        msgspec.json.decode(
            msgspec.json.encode({**form, "findings": []}), type=review_said.Said
        )


def test_a_finding_under_the_bar_is_seen_and_one_over_it_is_a_later_steps_item() -> (
    None
):
    record = task(**{**PREPARED, "filed": ()})
    placed = filing.decide(record, world())
    assert not isinstance(placed, Refusal)
    assert [(found.finding, found.disposition, found.line) for found in placed] == [
        ("r1.1", "seen", "under: small")
    ]
    over = Finding(
        id="r1.1", level="should", where="a", title="t", what="w", against="over"
    )
    heavy = replace(REVIEWED, findings=(over,))
    assert (
        code_of(
            filing.decide(
                task(**{**PREPARED, "filed": (), "reviews": (heavy,)}), world()
            )
        )
        == "not-built"
    )


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
