"""Poll the Inbox beside the board's other duties, at its own interval."""

from functools import partial
from typing import TYPE_CHECKING

import anyio

from lem.addons.inbox import workspace
from lem.kernel import clock
from lem.kernel.errors import Fault, Refusal
from lem.records.base import Frozen
from lem.store.places import Workspace

if TYPE_CHECKING:
    from collections.abc import Callable


type Targets = Callable[[], tuple[Target, ...]]
type Report = Callable[[str, str | None], None]

# The Inbox poll interval on main, 2026-11-25.
INTERVAL = 10


class Target(Frozen, frozen=True, kw_only=True):
    """A real workspace and its board address."""

    where: Workspace
    url: str


def cycle(targets: Targets, report: Report) -> None:
    """One failure does not keep another workspace from its Inbox."""
    now = clock.now()
    for target in targets():
        name = target.where.checkout.name
        try:
            saved = workspace.tick(target.where, now, target.url)
        except (Fault, Refusal, OSError) as error:
            report(name, str(error))
        else:
            report(name, saved.problem)


async def run(targets: Targets, report: Report, stopping: anyio.Event) -> None:
    """Look only while the board runs, off the board's request thread."""
    while not stopping.is_set():
        with anyio.move_on_after(INTERVAL):
            await stopping.wait()
        if not stopping.is_set():
            await anyio.to_thread.run_sync(partial(cycle, targets, report))
