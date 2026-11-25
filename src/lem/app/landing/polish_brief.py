"""What the polish builder gets (`land.cmd_polish` on `main`; `stages/polish.md` keeps it as
`polish.json` in the task's folder): the task's own commits, which the pass reads, and what comes
after `before` is the pass's own."""

from typing import TYPE_CHECKING

import msgspec

from lem.model.landing import polish
from lem.records.base import Frozen

if TYPE_CHECKING:
    from lem.app.landing import frame
    from lem.records.landing.start import Polished

SHORT = 9


class Brief(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """The task, its track, whether the pass is done, the tip it started at, the range and
    the subjects of the task's own commits, the plan, the report and the defects outside the
    task it names, the backlog's folder, the item the task started from, which the pass
    removes when the branch still holds it, and what the pass may not change."""

    task: str
    size: str
    done: bool
    before: str
    commits_range: str = msgspec.field(name="range")
    commits: tuple[str, ...]
    plan: str | None
    report: str | None
    outside: str | None
    backlog: str
    started_from: str | None = msgspec.field(name="item")
    frozen: tuple[str, ...]


def present(context: frame.Context, name: str) -> str | None:
    """The path of a file of the task's folder, when it is there."""
    path = context.folder / name
    return str(path) if path.is_file() else None


def subjects(context: frame.Context, since: str, until: str) -> tuple[str, ...]:
    """Each commit of the range, short, with its subject."""
    commits = context.ports.git.commits(context.worktree, since, until)
    return tuple(subject_of(one.sha, one.subject) for one in commits)


def subject_of(sha: str, subject: str) -> str:
    """A commit as `git log --format=%h %s` gives it."""
    short = sha[:SHORT]
    return f"{short} {subject}"


def brief_of(context: frame.Context, kept: Polished) -> Brief:
    """The brief of the pass that started at `kept.before`."""
    task, before = context.record.task, kept.before
    base = context.ports.git.merge_base(context.worktree, before, context.world.base)
    start = base or context.world.base
    return Brief(
        task=task.slug,
        size="small" if task.shape is None else task.shape.track,
        done=kept.after is not None,
        before=before,
        commits_range=f"{start}..{before}",
        commits=subjects(context, start, before),
        plan=None if task.plan is None else task.plan.path,
        report=present(context, "report.md"),
        outside=present(context, "outside.md"),
        backlog=polish.BACKLOG,
        started_from=task.backlog_item,
        frozen=polish.frozen(context.record),
    )
