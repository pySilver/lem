"""The row of the folders of the Lem before: Lem's home folder, and the state folder of each
workspace of the server's list and of the call, when one holds the files of Lem 0.3.

This Lem writes nothing into such a folder and reads nothing of such a state folder: each of its
commands that would refuses `old-state` (`lem.kernel.folders`). The owner's ruling: his
repositories start over, and the move of the old files is his act, at the cutover (the design's
part 10). The check only reads: it marks no folder.
"""

from pathlib import Path
from typing import TYPE_CHECKING

from lem.board.workspaces import listed
from lem.cli.doctor.checkouts import main_checkout
from lem.cli.doctor.row import REQUIRED, Row
from lem.kernel import folders, paths
from lem.kernel.errors import Refusal
from lem.store import guard
from lem.store.places import STATE

if TYPE_CHECKING:
    from lem.cli.doctor.look import Look


def states(look: Look, home: Path) -> tuple[Path, ...]:
    """The state folder of each workspace of the server's list, and of the call's, each once.
    A list of workspaces that does not read is the home folder's own, which the row names
    already when it is of the Lem before."""
    try:
        named = [Path(one) for one in listed(home)]
    except Refusal:
        named = []
    here = main_checkout(look.folder)
    checkouts = [*named, *([here] if here else [])]
    seen = dict.fromkeys(one.resolve() / STATE for one in checkouts)
    return tuple(seen)


def old_folders(look: Look) -> tuple[Path, ...]:
    """The home folder and each state folder that holds the files of the Lem before."""
    home = paths.home(look.environ)
    found = [home] if folders.form(home, frozenset()) == "old" else []
    every = states(look, home)
    found += [state for state in every if guard.form(state) == "old"]
    return tuple(found)


def old_forms_row(look: Look) -> Row:
    """Whether a folder of this machine still holds the files of the Lem before."""
    found = old_folders(look)
    without = None
    if found:
        without = (
            "each command that writes there refuses old-state until the owner's cutover "
            "moves the old files away from each folder named here (the stop of the Lem 0.3 "
            "board server first); the first write of this Lem then marks the folder as its "
            "own"
        )
    return Row(
        name="folders of Lem 0.3",
        need=REQUIRED,
        found=not found,
        detail=", ".join(map(str, found))
        or "none: each folder is this Lem's, or empty",
        used_for=(
            "Lem's home folder and each repository's .lem/state/, which this Lem writes only "
            "when they are its own or empty"
        ),
        without_it=without,
    )
