"""Read and edit the machine's peer table under the settings lock."""

import os
from typing import TYPE_CHECKING

from lem.kernel import folders, locks
from lem.kernel.errors import Refusal
from lem.settings import edit, places, reading
from lem.settings.load import machine_of

if TYPE_CHECKING:
    from pathlib import Path


def read(home: Path) -> dict[str, int]:
    """Read the checked table, before any call to a peer."""
    folders.inside_test_root(home)
    return machine_of(home, os.environ).peers


def change(home: Path, name: str, port: int | None) -> dict[str, int]:
    """A join or leave preserves the rest of the owner's settings."""
    folders.home_marked(home)
    path = home / places.MACHINE
    chosen = edit.Edit(
        scope=places.Scope.machine,
        path=path,
        lock=path.with_suffix(".lock"),
        table="peers",
        key=name,
        given=port,
    )
    where = reading.Where(checkout=None, home=home, environ=os.environ)
    with locks.held(chosen.lock):
        before = read(home)
        if port is None and name not in before:
            raise Refusal("peer-absent", f"{name} is not joined", "run lem serve peers")
        return edit.written(chosen, where).settings.peers
