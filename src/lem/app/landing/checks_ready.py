"""What the checks do before their first command (`land.checks_ready` and the gate's end in
`land.checks_run` on `main`): refuse a run with no command, give the polish pass back when the
tip lost it, and wait at the load gate, where a stop ends the run before it began. Every write
reads the record as it is now: the gate and the criteria's check write it while the step runs.
"""

from functools import partial
from typing import TYPE_CHECKING

from lem.app.landing import changes, checks_gate, checks_record
from lem.kernel import clock
from lem.kernel.errors import Refusal
from lem.model.landing import checks, checks_said
from lem.records.journal.landing import CheckEnd
from lem.store import places, tasks

if TYPE_CHECKING:
    from lem.app.landing import frame
    from lem.records.base import Moment
    from lem.records.record import Record


def written(context: frame.Context, change: tasks.Change) -> Record:
    """Write `change` over the task's record as it is now."""
    state, slug = context.workspace.state, context.record.task.slug
    return tasks.update(state, slug, change, tasks.read(state, slug).revision)


def ready(context: frame.Context) -> None:
    """Refuse a run with no command, and one whose tip lost the polish pass, which is then due
    again."""
    record = context.record
    refused = checks.decide(record, context.world)
    if refused is not None:
        raise refused
    in_tip = polish_in_tip(context)
    refused = checks.unpolished(record, in_tip=in_tip)
    if refused is not None:
        written(context, checks_record.unpolished)
        raise refused


def polish_in_tip(context: frame.Context) -> bool:
    """Whether the tip holds the last commit of a polish pass that is done, or none is."""
    landing = context.record.landing
    polish = None if landing is None else landing.polished
    if polish is None or polish.after is None:
        return True
    tip = context.world.tip or ""
    return context.ports.git.is_ancestor(context.worktree, polish.after, tip)


def stopped_before(record: Record, *, at: Moment) -> Record:
    """The record with the run's one end, stopped before its first command."""
    said = checks_said.ended(record.task.slug, "stopped")
    return changes.noted(record, CheckEnd(at=at, outcome="stopped", say=said))


def gated(context: frame.Context) -> None:
    """Wait at the load gate; a stop there ends the run before its first command."""
    workspace, slug = context.workspace, context.record.task.slug
    try:
        checks_gate.Gate(slug=slug, workspace=workspace).passed()
    except InterruptedError:
        written(context, partial(stopped_before, at=clock.now()))
        raise Refusal(
            "stopped",
            "the checks were stopped before their first command",
            f"`lem land checks {slug}` runs them again",
        ) from None
    folder = places.task_folder(workspace.state, slug)
    (folder / checks_gate.checks_waits.WAITS).unlink(missing_ok=True)
