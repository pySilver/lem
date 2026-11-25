"""What the board's app serves with, beside the server's facts: Lem's home folder, the server's
environment, the address of the main listener, the door when it is open, the stop, and the two
things that live as long as the server, the counts of the workspaces and the watcher of the
board's notifications."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from lem.adapters.notify_push import PushNotifier
from lem.board.counts import Counts
from lem.board.push.watch import Watcher

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from pathlib import Path

    from lem.board.door import Door

# What the app's state holds of it, which the routes read.
SHARED = ("home", "environ", "stop", "counts", "watcher")


@dataclass(kw_only=True)
class Serving:
    """What the app serves with; `stop` ends the server after the answer that calls it."""

    home: Path
    environ: Mapping[str, str]
    listen: str
    stop: Callable[[], None]
    door: Door | None = None
    counts: Counts = field(default_factory=Counts)
    watcher: Watcher = field(init=False)

    def __post_init__(self) -> None:
        """Make the watcher, with the notifier of the home folder."""
        notifier = PushNotifier(self.home, self.environ)
        self.watcher = Watcher(home=self.home, notifier=notifier)
