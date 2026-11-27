"""A polish builder keeps the approved tests, the plan, and the commits it started from."""

import pytest
from msgspec.structs import replace

from lem.app.landing import polish_brief
from lem.model.landing import polish
from lem.records.criterion import Criterion, CriterionTest
from lem.records.landing.start import Polished
from lem.records.work import Plan
from unit.landing.worlds import MOMENT, TIP, task


@pytest.mark.parametrize("plan", [None, Plan(path="docs/login.md")])
def test_the_polish_brief_protects_each_test_file_once_and_the_plan_if_set(
    plan: Plan | None,
) -> None:
    case = CriterionTest(command="pytest", files=("tests/z.py", "tests/a.py"))
    other = CriterionTest(command="pytest -k login", files=("tests/z.py", "tests/b.py"))
    criteria = (
        Criterion(number=1, text="The login works.", tests=(case, other)),
        Criterion(number=2, text="The error shows.", tests=(other,)),
    )
    record = task()
    shaped = replace(
        record.task,
        criteria=replace(record.task.criteria, criteria=criteria),
        plan=plan,
    )
    expected = ("tests/a.py", "tests/b.py", "tests/z.py")
    if plan is not None:
        expected = (*expected, "docs/login.md")
    assert polish.frozen(replace(record, task=shaped)) == expected


def test_a_rewritten_branch_names_the_commit_the_pass_must_keep() -> None:
    refused = polish.rewritten(TIP)
    assert (refused.code, refused.why, refused.fix) == (
        "rewritten",
        (
            "the branch no longer holds 111111111, the tip the polish pass started at: its "
            "builder rewrote the task's commits, which no builder of the pass does"
        ),
        "put the branch back on its own commits (git reflog names them), then run this again",
    )


def test_a_polish_regression_names_the_failed_criterion_and_asks_for_a_revert() -> None:
    refused = polish.unheld("criterion 2 failed on the branch")
    assert (refused.code, refused.why, refused.fix) == (
        "criteria",
        "after the polish pass the tests of the criteria do not hold: criterion 2 failed on the branch",
        (
            "the pass changes no behavior: a builder finds the commit of the pass that broke it "
            "and takes it out, and this step runs again"
        ),
    )


def test_only_a_standard_track_has_a_polish_pass() -> None:
    fast = task()
    refused = polish.small(fast)
    assert refused is not None
    assert refused.code == "fast-track"
    assert refused.why == (
        "the fast track has no polish pass: its builder judged what it saw outside the change "
        "by the bar of rule 6 of the builder's standing rules, in commits of its own, and the "
        "review reads every line of it"
    )
    assert refused.fix == "`lem land checks fix-the-login` is the next step"
    assert fast.task.shape is not None
    assert polish.small(replace(fast, task=replace(fast.task, shape=None))) is not None
    full = replace(
        fast, task=replace(fast.task, shape=replace(fast.task.shape, track="full"))
    )
    assert polish.small(full) is None


def test_polish_can_finish_only_once_on_a_clean_worktree() -> None:
    started = Polished(before=TIP, at=MOMENT)
    record = task(polished=started)
    dirty = polish.unstarted(record, clean=False)
    assert dirty is not None
    assert dirty.code == "dirty"
    assert dirty.why == "the task's worktree has changes nobody committed"
    assert (
        dirty.fix
        == "the polish builder commits them or removes them, then `--done` runs again"
    )

    before = polish.unstarted(task(), clean=True)
    assert before is not None
    assert (before.code, before.why, before.fix) == (
        "not-started",
        "no polish pass started for this landing",
        "`lem land polish fix-the-login` starts it and prints what its builder gets",
    )

    assert polish.unstarted(record, clean=True) is None
    done = polish.unstarted(task(polished=replace(started, after=TIP)), clean=True)
    assert done is not None
    assert (done.code, done.why, done.fix) == (
        "done",
        "the polish pass of this landing is done already, at 111111111",
        "a builder of the landing after it has the same list in its brief",
    )


def test_polish_requires_each_commit_that_touched_the_contract_to_be_reverted() -> None:
    assert polish.kept_back(()) is None
    refused = polish.kept_back(("tests/login.py (ab1234)", "docs/login.md (ef6789)"))
    assert refused is not None
    assert refused.code == "frozen"
    assert refused.why == (
        "the polish pass changed what it may not: tests/login.py (ab1234); "
        "docs/login.md (ef6789). A criterion's test and the plan "
        "are the task's contract, and the pass changes no behavior"
    )
    assert (
        refused.fix
        == "a builder reverts those commits (`git revert`), and this step runs again"
    )


def test_the_polish_removes_a_tracked_item_and_never_a_reviewers_item_in_git() -> None:
    assert (
        polish_brief.tracked("docs/backlog/the-item.md") == "docs/backlog/the-item.md"
    )
    assert polish_brief.tracked(".lem/state/backlog/the-item.md") is None
    assert polish_brief.tracked(None) is None
