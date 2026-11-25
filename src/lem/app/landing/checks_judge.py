"""What the checks judge once their commands passed (`land.checks_body` on `main`): that no
command changed the tree it judged, that each criterion's tests pass on the branch and fail on
the base (or the polish pass's run of them, when its five inputs are the same now). The bar
and the size are `checks_bar.py`.
"""

from typing import TYPE_CHECKING

from lem.app.landing import checks_criteria, checks_git
from lem.model.landing import checks, checks_ended, checks_red
from lem.records.landing.checks import CriterionCheck

if TYPE_CHECKING:
    from lem.app.landing import frame
    from lem.kernel.errors import Refusal
    from lem.records.base import Moment
    from lem.records.record import Record
    from lem.records.red import Red


def tree_refusal(context: frame.Context, tip: str) -> Refusal | None:
    """A command that changed a tracked file, or made a commit, changed the tree it judged."""
    worktree, slug = context.worktree, context.record.task.slug
    changed = checks_git.changed(worktree)
    if changed:
        return checks_ended.tree_moved(slug, str(worktree), changed)
    moved = context.ports.git.tip(worktree, "HEAD") or tip
    if moved != tip:
        return checks_ended.committed(slug, str(worktree), tip, moved)
    return None


def taken(context: frame.Context) -> str | None:
    """The commit of the polish pass whose run of the criteria's tests the checks take, when
    its five inputs are the same now (`land.taken_from_polish` on `main`); else None."""
    record = context.record
    polish = record.landing.polished if record.landing else None
    if polish is None or polish.run is None:
        return None
    now = checks_criteria.inputs(context.workspace, record)
    kept = checks.pass_kept(polish, checks_criteria.digest(now), small=small(record))
    return polish.run.tip if kept else None


def small(record: Record) -> bool:
    """Whether the task takes the fast track."""
    shape = record.task.shape
    return shape is None or shape.track == "small"


def criteria_run(context: frame.Context, now: Moment) -> tuple[Red | None, str | None]:
    """The run of the criteria's tests that the checks take: the polish pass's, with its
    commit; else a run of their own."""
    at = taken(context)
    if at is not None:
        return context.record.task.criteria.red, at
    return checks_criteria.red(context.workspace, context.record, now), None


def criteria_of(found: Red | None, taken: str | None) -> tuple[CriterionCheck, ...]:
    """Each criterion's test as the record keeps it: red on the base, green on the tip, and
    the commit of the pass it was taken from."""
    if found is None:
        return ()
    return tuple(
        CriterionCheck(
            criterion=test.criterion,
            red_on_base=bool(test.on_base),
            green_on_tip=test.on_branch == 0,
            taken_at=taken,
        )
        for test in found.tests
    )


def criteria_refusal(found: Red | None) -> Refusal | None:
    """The run of the criteria that does not hold, in the words its check gives."""
    if found is None:
        return None
    return checks_red.failed(found)
