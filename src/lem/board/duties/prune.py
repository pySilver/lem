"""A duty of the board server: the hourly keeping of the state folder (`serve.prune_once` on
`main`): what `lem prune` does, at the server's first tick for the workspace and then each
SECONDS, with the days of `state.keep_days`. A run that removed, folded, skipped and failed
nothing says nothing; any other run is one line in the server's log, with each skip and each
failure.
"""

from datetime import timedelta
from typing import TYPE_CHECKING

from lem.cli.prune import days
from lem.store.retention import run, said

if TYPE_CHECKING:
    from lem.board.duties.context import Duty

# How often the server keeps one workspace's state folder. A guess (2026-11-21): the number it
# keeps is in days, so an hour late costs nothing, and a run reads the tasks' records and walks
# the ended tasks' folders, which is quick beside an hour.
HOUR = 3600
SECONDS = timedelta(seconds=HOUR)


def tick(duty: Duty) -> None:
    """Keep the state folder when it is due."""
    pruned = duty.kept.pruned
    if pruned is not None and duty.now - pruned < SECONDS:
        return
    duty.kept.pruned = duty.now
    keep, source = days.kept(duty.checkout, None, dry=False)
    found = run.pruned(duty.state, keep, source, duty.now, dry=False)
    if not said.quiet(found):
        duty.say(said.logged(found))
