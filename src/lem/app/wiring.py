"""`Ports`: the seven ports a use case takes as its first argument, built at call time (the
design's part 4).

A test builds `Ports` from its fakes (`tests/fakes`), or replaces one port of the bound set
(`dataclasses.replace`). The app binds each port to its first adapter with `bound`: the module
named, imported only then, whose `bind(place)` gives the port.
"""

import importlib
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from lem.ports.forge import Forge
    from lem.ports.git import Git
    from lem.ports.harness import Harness
    from lem.ports.judge import Judge
    from lem.ports.notifier import Notifier
    from lem.ports.place import Place
    from lem.ports.terminal import Terminal
    from lem.ports.tracker import Tracker


@dataclass(frozen=True, kw_only=True, slots=True)
class Ports:
    """One field for each port."""

    git: Git
    forge: Forge
    terminal: Terminal
    harness: Harness
    tracker: Tracker
    notifier: Notifier
    judge: Judge


def adapter(module: str, place: Place) -> object:
    """The adapter of `module` bound to `place`."""
    return importlib.import_module(module).bind(place)


def bound(place: Place) -> Ports:
    """Every port bound to its first adapter for `place`."""
    return Ports(
        git=cast("Git", adapter("lem.adapters.git_cli", place)),
        forge=cast("Forge", adapter("lem.adapters.forge_gh", place)),
        terminal=cast("Terminal", adapter("lem.adapters.terminal_agterm", place)),
        harness=cast("Harness", adapter("lem.adapters.harness_claude", place)),
        tracker=cast("Tracker", adapter("lem.adapters.tracker_github", place)),
        notifier=cast("Notifier", adapter("lem.adapters.notify_push", place)),
        judge=cast("Judge", adapter("lem.adapters.judge_jev", place)),
    )
