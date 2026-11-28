"""`lem issue tick NAME`: the parts comment on the issue of the feature NAME, one line with a
box for each part and the last line `lem: NAME parts`, written from the records
(`model/task/parts_comment.py`; `docs/plans/2026-11-27-a-feature-in-parts.md`, "A part's ticket
step"). It runs at the split, after each part lands, and after the feature lands.

The step finds its comment by that last line, as an end's comment is found (`comment.py`): with
none it posts the comment, with one it edits it only when its text differs (`tick_due.py`). It
writes no ticket step: a run again, or one after a tick that a stop cut off after its edit, finds
the same text and writes nothing.
"""

from typing import TYPE_CHECKING

from lem.app.tasks.issues import tick_due, tick_run
from lem.app.tasks.issues.results import enveloped
from lem.model.task import feature_parts, parts_comment

if TYPE_CHECKING:
    import msgspec

    from lem.app.tasks.issues.run import Run
    from lem.app.wiring import Ports
    from lem.kernel.envelope import Envelope
    from lem.records.task import Task
    from lem.store.places import Workspace

STEP = "tick"


def said(run: Run, parts: tuple[Task, ...]) -> str:
    """The line for the owner: what the step did, and how many parts landed."""
    count = f"{parts_comment.landed(parts)} of {len(parts)} parts landed"
    if run.did:
        return f"{run.did[0]} on {run.named}: {count}"
    return f"the parts comment on {run.named} says it already: {count}"


def tick(ports: Ports, where: Workspace, slug: str) -> Envelope | msgspec.Struct:
    """The parts comment of the feature `slug` on its issue, as the records give it."""
    run = tick_run.feature_run(ports, where, slug)
    every = (one.task for one in run.every)
    parts = feature_parts.parts_of(run.record.task, every)
    body = parts_comment.text(run.record.task, parts)
    tick_due.written(run, body, parts_comment.marker(slug))
    return enveloped(run.stepped(STEP, None), said(run, parts))
