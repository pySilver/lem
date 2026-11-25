"""The machine's yes to the correction queue: `collect = true` under `[corrections]` of Lem's
home `machine.toml`, in a home folder this Lem made. The switch is the machine's alone (the
owner's ruling): no file of a repository holds it, and `lem settings set corrections.collect
yes --machine` writes it. A file that does not read, or a home of the Lem before, is a no: a
message leaves the machine only on his yes."""

from typing import TYPE_CHECKING

from lem.kernel import folders, paths
from lem.kernel.errors import Refusal
from lem.settings.load import machine_of
from lem.settings.places import TEAM

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path


def says_yes(environ: Mapping[str, str]) -> bool:
    """Whether this machine collects the owner's corrections now."""
    try:
        return collects(environ)
    except Refusal:
        return False


def collects(environ: Mapping[str, str]) -> bool:
    """Whether the machine's file says yes in a home folder this Lem made; refused for a
    relative home or a file that does not read."""
    home = paths.home(environ)
    if folders.form(home, frozenset()) != "new":
        return False
    return machine_of(home, environ).corrections.collect


def repository_uses_lem(checkout: Path) -> bool:
    """Whether the checkout still has the team file the correction hook required."""
    return (checkout / TEAM).is_file()
