"""`lem land polish SLUG --done`: the check of what the polish pass committed, and the pass
kept (`land.cmd_polish` on `main`). A refusal goes back to a builder with the same job and the
step's message."""

from functools import partial
from typing import TYPE_CHECKING

from lem.app.landing import (
    changes,
    checks_criteria,
    checks_diff,
    checks_plan,
    checks_ready,
    checks_record,
)
from lem.model.landing import checks_red, polish
from lem.records.landing.start import PassRun, Polished

# Each commit of the pass with the paths it changed.
type ByCommit = dict[str, tuple[str, ...]]

if TYPE_CHECKING:
    from lem.app.landing import frame
    from lem.records.record import Record


def kept(record: Record, *, polished: Polished) -> Record:
    """The record with the pass done, and its span ended."""
    changed = changes.landing(record, polished=polished)
    return checks_record.closed(changed, name="polish", at=polished.at)


def touched(context: frame.Context, before: str, tip: str) -> tuple[str, ...]:
    """Each file of the contract the pass changed, with the commits that changed it."""
    worktree = context.worktree
    differs = set(checks_diff.paths(worktree, before, tip))
    commits = context.ports.git.commits(worktree, before, tip)
    by_commit = {one.sha: checks_diff.touched(worktree, one.sha) for one in commits}
    return tuple(
        named_by(path, by_commit)
        for path in polish.frozen(context.record)
        if path in differs
    )


def named_by(path: str, by_commit: ByCommit) -> str:
    """A file of the contract with the commits that changed it."""
    shas = (sha for sha, paths in by_commit.items() if path in paths)
    listed = ", ".join(sha[: polish.SHORT] for sha in shas)
    return f"{path} (by {listed})"


def run_of(context: frame.Context, commits: int) -> PassRun | None:
    """The pass's run of the criteria's tests, when it committed anything; refused when they
    do not hold."""
    if not commits:
        found = checks_criteria.inputs(context.workspace, context.record)
        checks_plan.verified(context.worktree, context.record, found)
        return None
    red = checks_criteria.red(context.workspace, context.record, context.world.now)
    refused = checks_red.failed(red)
    if refused is not None:
        raise polish.unheld(refused.why)
    digest = checks_criteria.digest(red.inputs)
    return PassRun(inputs=digest, outcome="passed", tip=red.inputs.tip)


def filed_of(context: frame.Context, before: str, tip: str) -> tuple[str, ...]:
    """The backlog items the pass added."""
    folder = f"{polish.BACKLOG}/"
    added = checks_diff.added(context.worktree, before, tip)
    return tuple(path for path in added if path.startswith(folder))


def before_of(context: frame.Context) -> str:
    """The tip the pass started at, once what the pass did may be kept."""
    record = context.record
    refused = polish.small(record) or polish.unstarted(
        record, clean=context.world.clean
    )
    if refused is not None:
        raise refused
    landing = record.landing
    before = landing.polished.before if landing and landing.polished else ""
    tip = context.world.tip or ""
    if not context.ports.git.is_ancestor(context.worktree, before, tip):
        raise polish.rewritten(before)
    refused = polish.kept_back(touched(context, before, tip))
    if refused is not None:
        raise refused
    return before


def finished(context: frame.Context) -> Polished:
    """Check what the pass committed, and keep it, with its span ended."""
    before = before_of(context)
    tip = context.world.tip or ""
    commits = len(context.ports.git.commits(context.worktree, before, tip))
    done = Polished(
        before=before,
        after=tip,
        commits=commits,
        filed=filed_of(context, before, tip),
        run=run_of(context, commits),
        at=context.world.now,
    )
    checks_ready.written(context, partial(kept, polished=done))
    return done
