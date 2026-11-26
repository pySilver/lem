"""Record the stage's repair block under the task's step lock."""

from typing import TYPE_CHECKING

import msgspec

from lem.app.tasks import release
from lem.kernel import clock
from lem.kernel.envelope import Envelope
from lem.model.landing import repair_limit
from lem.store import places, steps, tasks

if TYPE_CHECKING:
    from pathlib import Path


def run(folder: Path, slug: str) -> Envelope:
    """Block the landing after the stage's two unsuccessful repairs."""
    state = places.workspace(folder).state
    tasks.read(state, slug)
    now = clock.now()
    with steps.step(state, slug, "repair-limit", now):
        record = release.checked(state, slug)
        updated = repair_limit.blocked(record, now)
        if updated is not record:
            updated = tasks.update(state, slug, lambda _: updated, record.revision)
    return Envelope(
        ok=True,
        outcome=msgspec.Raw(msgspec.json.encode(updated.task)),
        say=f"{slug}: {repair_limit.WHY}; the landing waits for the owner",
    )
