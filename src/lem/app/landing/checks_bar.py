"""Where the change lowers the bar, and its size for the review (`land.check_bar`,
`shebang_kinds` and the size of `land.checks_body` on `main`; the rule is
`model/landing/bar.py`)."""

from pathlib import Path
from typing import TYPE_CHECKING

from lem.app.landing import checks_diff
from lem.model.landing import bar
from lem.records.landing.checks import ChangeSize, Lowered

if TYPE_CHECKING:
    from lem.app.landing import frame

# How many changed lines one reader takes as one piece; a larger change is read task by task,
# in the plan's own cuts. A guess (2026-11-15), not a measurement (`READ_AT` on `main`).
READ_AT = 800
type Paths = tuple[str, ...]


def plan_of(context: frame.Context) -> tuple[str, str]:
    """The plan's file and its text; the fast track has none, and gives no reason."""
    plan = context.record.task.plan
    if plan is None:
        return "", ""
    return plan.path, (context.worktree / plan.path).read_text(encoding="utf-8")


def kinds_of(worktree: Path, tip: str, files: Paths) -> dict[str, str]:
    """Each changed file with the suffix whose marks a file with no suffix is read with, from
    the interpreter its first line names, else "": one read of git for each such file."""
    found = dict.fromkeys(files, "")
    for name in files:
        if Path(name).suffix:
            continue
        found[name] = bar.shebang_suffix(checks_diff.first_line(worktree, tip, name))
    return found


def lowered_of(context: frame.Context, base: str, tip: str) -> bar.BarRead:
    """Where the change lowers the bar, each with the reason the plan gives for that file."""
    worktree = context.worktree
    where, text = plan_of(context)
    diff = checks_diff.diff(worktree, base, tip)
    kinds = kinds_of(worktree, tip, checks_diff.paths(worktree, base, tip))
    return bar.bar_of(
        diff, checks_diff.rows(worktree, base, tip), text, kinds, where=where
    )


def kept_marks(found: bar.BarRead) -> tuple[Lowered, ...]:
    """The lowered bar as the record keeps it."""
    return tuple(
        Lowered(path=mark.path, how=mark.what, reason=mark.reason)
        for mark in found.lowered
    )


def size_of(context: frame.Context, base: str, tip: str) -> ChangeSize:
    """The change's size, in files and changed lines, for the review."""
    stat = context.ports.git.diff_stat(context.worktree, base, tip)
    lines = stat.added + stat.removed
    return ChangeSize(files=len(stat.paths), lines=lines, in_parts=lines > READ_AT)
