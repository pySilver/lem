"""`polish`: the standard track's polish pass, and its check when it is done (`landing.md` C,
row 3; `land.cmd_polish` on `main`; `stages/polish.md`).

The pass reads the task's own commits and fixes what they left around them; it changes no
behavior. What it may not change is the task's contract: the files of the criteria's tests and
the plan that names them. Its start keeps the tip it starts at, so that a run cut off, or a
second start, never takes the builder's first commits for the task's own.
"""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.records.criterion import Criterion
    from lem.records.record import Record

SHORT = 9
# The backlog's one place in a repository (`land.backlog_of` on `main`).
BACKLOG = "docs/backlog"


def small(record: Record) -> Refusal | None:
    """The fast track has no polish pass."""
    shape = record.task.shape
    if shape is not None and shape.track == "full":
        return None
    slug = record.task.slug
    return Refusal(
        "fast-track",
        "the fast track has no polish pass: its builder judged what it saw outside the change "
        "by the bar of rule 6 of the builder's standing rules, in commits of its own, and the "
        "review reads every line of it",
        f"`lem land checks {slug}` is the next step",
    )


def frozen(record: Record) -> tuple[str, ...]:
    """What the pass may not change: each file that holds a criterion's test, and the plan."""
    tests = record.task.criteria.criteria
    names = {name for criterion in tests for name in test_files(criterion)}
    plan = record.task.plan
    if plan is None:
        return tuple(sorted(names))
    return (*sorted(names), plan.path)


def test_files(criterion: Criterion) -> set[str]:
    """The files that hold one criterion's tests."""
    return {name for test in criterion.tests for name in test.files}


def unstarted(record: Record, *, clean: bool) -> Refusal | None:
    """`--done` with no pass started, with the pass done already, or with changes nobody
    committed in the worktree."""
    slug = record.task.slug
    polish = (record.landing or Landing()).polished
    if not clean:
        return Refusal(
            "dirty",
            "the task's worktree has changes nobody committed",
            "the polish builder commits them or removes them, then `--done` runs again",
        )
    if polish is None:
        return Refusal(
            "not-started",
            "no polish pass started for this landing",
            f"`lem land polish {slug}` starts it and prints what its builder gets",
        )
    if polish.after is None:
        return None
    after = polish.after[:SHORT]
    return Refusal(
        "done",
        f"the polish pass of this landing is done already, at {after}",
        "a builder of the landing after it has the same list in its brief",
    )


def rewritten(before: str) -> Refusal:
    """The branch no longer holds the tip the pass started at."""
    short = before[:SHORT]
    return Refusal(
        "rewritten",
        f"the branch no longer holds {short}, the tip the polish pass started at: its "
        "builder rewrote the task's commits, which no builder of the pass does",
        "put the branch back on its own commits (git reflog names them), then run this again",
    )


def kept_back(touched: tuple[str, ...]) -> Refusal | None:
    """The pass changed the contract: each file with the commits that changed it."""
    if not touched:
        return None
    listed = "; ".join(touched)
    return Refusal(
        "frozen",
        f"the polish pass changed what it may not: {listed}. A criterion's test and the plan "
        "are the task's contract, and the pass changes no behavior",
        "a builder reverts those commits (`git revert`), and this step runs again",
    )


def unheld(why: str) -> Refusal:
    """After the pass, the tests of the criteria do not hold."""
    return Refusal(
        "criteria",
        f"after the polish pass the tests of the criteria do not hold: {why}",
        "the pass changes no behavior: a builder finds the commit of the pass that broke it "
        "and takes it out, and this step runs again",
    )
