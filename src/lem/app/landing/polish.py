"""`lem land polish`: the standard track's polish pass (`land.cmd_polish` on `main`;
`stages/polish.md`).

Its start keeps the tip it starts at and prints what its builder gets: the task's own commits,
the plan, the report and the defects outside the task it names, the backlog, the item the task
started from, and what the pass may not change. `--done`, after the builder, checks what it
committed: a worktree with changes nobody committed, a branch that no longer holds the start, a
change of a criterion's test or of the plan, and tests of the criteria that no longer pass on
the branch and fail on the base are each refused. Then it keeps the pass, with its run of the
criteria's tests, which `checks` takes while that run's five inputs stay the same. A feature
takes no pass: each of its parts had its own.
"""

from functools import partial
from typing import TYPE_CHECKING

from lem.app.landing import changes, checks_record, polish_brief, polish_done, step
from lem.model.landing import feature, polish
from lem.records.landing.start import Polished

if TYPE_CHECKING:
    from pathlib import Path

    from lem.app.landing import frame
    from lem.kernel.envelope import Envelope
    from lem.records.record import Record


def begun(record: Record, *, polished: Polished) -> Record:
    """The record with the pass started, and its span."""
    changed = changes.landing(record, polished=polished)
    return checks_record.begun(changed, name="polish", at=polished.at)


def started(context: frame.Context) -> polish_brief.Brief:
    """Start the pass at the tip, or keep the start of one that is not done."""
    record, world = context.record, context.world
    refused = polish.small(record) or feature.polish_refusal(record, world)
    if refused is not None:
        raise refused
    kept = record.landing.polished if record.landing else None
    if kept is None:
        kept = Polished(before=world.tip or "", at=world.now)
        context.write(record, partial(begun, polished=kept))
    return polish_brief.brief_of(context, kept)


def run(folder: Path, slug: str, *, done: bool) -> Envelope:
    """`lem land polish SLUG [--done]`."""
    act = polish_done.finished if done else started
    return step.landed(folder, slug, "polish", act)
