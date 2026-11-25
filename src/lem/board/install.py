"""Which install of Lem a process runs, and whether it replaces the server that runs (the
design's part 5, "The server's replace rule").

The same install, the same package folder, keeps the rule of the proof of concept
(`serve.ensure_held`): a server whose settings differ, or whose code is older than the files of
the folder now, is replaced. Another install replaces it only when its release is higher; at an
equal or a lower one it leaves it, so that two installs on one home folder do not take turns
at each start, as they did under the rule before (seen on 2026-11-25).
"""

from typing import TYPE_CHECKING

from lem.board.facts import Install
from lem.kernel import paths, release

if TYPE_CHECKING:
    from pathlib import Path

BUILD_COMMIT = "build-commit"


def stamp(package: Path) -> int:
    """The newest change time of the package's modules, in ns: an edit of a checkout, or a
    new install into the same folder, moves it."""
    found = (module.stat().st_mtime_ns for module in package.rglob("*.py"))
    return max(found, default=0)


def install_of(package: Path = paths.PACKAGE) -> Install:
    """The install whose package folder is `package`, read once by each process at its start,
    so that a server keeps the install it started from whatever an update writes later."""
    try:
        commit = (package / BUILD_COMMIT).read_text(encoding="utf-8").strip() or None
    except FileNotFoundError:
        commit = None
    return Install(
        version=release.running(),
        commit=commit,
        package=str(package.resolve()),
        stamp=None if commit else stamp(package),
    )


def replaces(mine: Install, theirs: Install, *, settings_differ: bool) -> bool:
    """Whether the install `mine` replaces a running server of the install `theirs`."""
    if mine.package != theirs.package:
        return release.newer(mine.version, theirs.version)
    return settings_differ or mine != theirs
