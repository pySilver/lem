"""`lem criteria show` and `lem criteria record`: a task's criteria as they stand, from its plan,
or from `criteria.md` of a fast-track task, checked against its approval and the recorded
changes (`criteria.Task.criteria` on `main`).

A task's plan comes first when it has one, and only a fast-track task is read from `criteria.md`,
which no commit holds: the criteria of a standard-track task are at the top of its plan, and such
a task with no plan is refused. `record` keeps what it read in the task's record, which the
checks and the pull request read.
"""

from functools import partial
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.criteria import activity, texts, where
from lem.app.decisions.writing import Change, written
from lem.kernel.errors import Refusal
from lem.model.criteria import plan, standing
from lem.model.decisions.changes import changes_of
from lem.settings.load import settings_of

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.record import Record


def source(here: where.Here, record: Record) -> tuple[Path, bool]:
    """The file the task's criteria come from, and whether it is the fast track's."""
    where.worktree_of(here)
    found = where.plan_of(here, record)
    if found is not None:
        return found, False
    if here.sheet.is_file():
        return here.sheet, True
    plans = here.worktree / settings_of(here.workspace.checkout).settings.paths.plans
    raise Refusal(
        "no-plan",
        f"no plan of {here.slug} in {plans}",
        f"its lead writes YYYY-MM-DD-{here.slug}.md there (lem task plan-file {here.slug}); "
        f"only a fast-track task keeps its criterion in {here.sheet}",
    )


def shown_of(here: where.Here, record: Record) -> standing.Shown:
    """The task's criteria as they stand; refused when they do not."""
    path, small = source(here, record)
    sheet = texts.sheet_at(path, "the criteria")
    changes = changes_of(record.task)
    refusal = plan.standing(sheet, changes, path.name, here.slug, small=small)
    if refusal is not None:
        raise refusal
    return standing.shown_of(here.slug, str(path), sheet, changes, small=small)


def shown(folder: Path, slug: str) -> standing.Shown:
    """`lem criteria show SLUG`."""
    here = where.here_of(folder, slug)
    return shown_of(here, here.read())


def kept(record: Record, *, seen: standing.Shown) -> Record:
    """The record with the criteria `seen` read."""
    task = record.task
    criteria = replace(
        task.criteria,
        size=seen.size,
        why=seen.why,
        criteria=seen.criteria,
        how=seen.how,
        digest=seen.digest,
    )
    return replace(record, task=replace(task, criteria=criteria))


def keeping(here: where.Here, record: Record) -> tuple[Change, standing.Shown]:
    """The write of the criteria as they stand for `record`, and what it shows."""
    seen = shown_of(here, record)
    changed = partial(kept, seen=seen)
    return partial(activity.recorded, kept=changed, seen=seen), seen


def recorded(folder: Path, slug: str) -> standing.Shown:
    """`lem criteria record SLUG`: the criteria as they stand, kept in the record."""
    here = where.here_of(folder, slug)
    return written(here.workspace.state, slug, partial(keeping, here))
