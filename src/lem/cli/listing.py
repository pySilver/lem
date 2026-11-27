"""The machine's list of workspaces, from every command of `lem`: a command that runs in a
repository whose main checkout has `.lem/settings.toml` puts that checkout there before it
runs. The board server's duties (its look at GitHub, the merge, the wakes, the queue and the
guard) run only for a workspace on the list (`board/workspaces.py`), so a task whose workspace
the list lacks would wait with nothing to tell the owner so; with the list written here, at the
one door every command passes, no path of a task can miss it.

It comes after Click read the command's words, so a wrong call writes nothing, and before the
command's own work, so a list that cannot be written is a refusal before any effect. A linked
worktree puts its main checkout there, never itself; a checkout on the list already is no
change. `help`, `version`, `doctor` and `uninstall` take no part: they do no work in a
repository, and `doctor` names the move of a home folder of Lem 0.3, which this write refuses.
"""

import copy
import os
from functools import partial
from typing import TYPE_CHECKING

from lem.board import workspaces
from lem.cli import place
from lem.kernel import paths
from lem.kernel.errors import Refusal
from lem.store import places

if TYPE_CHECKING:
    from collections.abc import Callable

    import click

# The commands that list nothing.
UNLISTED = frozenset(("help", "version", "doctor", "uninstall"))
SETTINGS = ".lem/settings.toml"


def first(name: str, command: click.Command) -> click.Command:
    """`command`, which puts its repository on the list before its own work; the command
    itself for one of `UNLISTED` and for one with no callback."""
    if name in UNLISTED or command.callback is None:
        return command
    made = copy.copy(command)
    made.callback = partial(listed_then, command.callback)
    return made


def listed_then(leaf: Callable[..., object], **given: object) -> object:
    """The command's own callback `leaf` on its words, once its repository is on the list."""
    noted()
    return leaf(**given)


def noted() -> None:
    """Put the main checkout of the command's folder on the list, when Lem is set up there."""
    folder = place.folder()
    try:
        checkout = places.checkout_of(folder)
    except Refusal:
        return
    if (checkout / SETTINGS).is_file():
        workspaces.noted(paths.home(os.environ), folder)
