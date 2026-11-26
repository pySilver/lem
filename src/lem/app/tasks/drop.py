"""The owner's drop of a task, from any status that is not ended (the design's part 11, choice
4; `landing.md` E, "Drop during a step").

It reads the record through the release stop (a drop passes it, and leaves the hold for the
resume), stops the task's checks when they run, waits for the landing's step lock, and reads the
record again under it. When the forge merged the task's pull request into its base meanwhile, the
drop is refused and the task lands; else the task is `dropped`, and its pull request stays open
for the owner.
"""

import os
import signal
from typing import TYPE_CHECKING

from lem.app.tasks import drop_pull, move_state, ports, release
from lem.kernel import clock
from lem.kernel.errors import Refusal
from lem.model.task import holds, table
from lem.store import places, steps, tasks

DROPPED = "dropped"

if TYPE_CHECKING:
    from lem.app.wiring import Ports
    from lem.records.record import Record


def stop_checks(where: places.Workspace, slug: str) -> None:
    """Stop the task's checks when they run: a term to the step that holds the lock for
    them, whose handler stops its commands and lets the lock go."""
    path = places.task_folder(where.state, slug) / steps.LOCK
    holder = steps.holder_of(path)
    if holder is not None and holder.step == "checks":
        try:
            os.kill(holder.pid, signal.SIGTERM)
        except ProcessLookupError:
            return


def merged_refusal(
    given: Ports | None, where: places.Workspace, record: Record
) -> None:
    """Refuse the drop of a task the forge merged into its recorded base. Under the step
    lock, keep a recovered pull request number so `merged` can finish the landing."""
    landing, slug = record.landing, record.task.slug
    if landing is None or (landing.pull is None and landing.pushed is None):
        return
    if landing.merged is None:
        forge = (given or ports.bound(where)).forge
        if not drop_pull.merged(forge, where, record, landing):
            return
    raise Refusal(
        "merged",
        f"the forge merged the pull request of {slug} into its base while the drop waited: "
        "only such a merge defeats a drop, and the task lands",
        f"lem land merged {slug}",
    )


def dropped(
    where: places.Workspace, slug: str, line: str, given: Ports | None = None
) -> table.Moved:
    """Drop the task `slug` with the owner's reason `line`; `given` are the ports a test
    holds."""
    before = release.checked(where.state, slug, ends=True)
    refused = table.refusal(before.task, DROPPED, None)
    if refused is not None:
        raise refused
    stop_checks(where, slug)
    now = clock.now()
    with steps.waited(where.state, slug, "drop", now):
        record = tasks.read(where.state, slug)
        refused = table.refusal(record.task, DROPPED, None)
        if refused is not None:
            raise refused
        merged_refusal(given, where, record)
        worktree = move_state.gathered(where, slug)
        tasks.update(
            where.state,
            slug,
            lambda before: move_state.noted(
                holds.moved(before, status=DROPPED, line=line, now=now), worktree
            ),
            record.revision,
        )
    return table.Moved(slug=slug, was=record.task.status, status=DROPPED)
