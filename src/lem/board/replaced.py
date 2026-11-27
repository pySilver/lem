"""Whether the install a running board server started from was replaced, and the installed
Lem's `lem` by a path that an update keeps.

An update replaces the install of a running server in one of four ways: it removes the package
folder (`brew upgrade` removes the keg of the release before, or of the same release at a
formula's new revision), it writes another release into the folder (an upgrade of a uv tool),
it points Homebrew's `opt/lem` at another keg (`brew upgrade` with its clean-up off), or it
removes the standard library of the server's Python (`brew upgrade python@3.14` with its
clean-up: the server's process found its modules under that version's own folder). The server's
code is then of an install that is no longer there, and each step that reads a file of it can
fail: on 2026-11-27 the server of Lem 0.4.1 lost its notifications and then its duties after
`brew upgrade` to 0.4.2. `stale` is the same question asked by `lem serve ensure` of another
process: it replaces such a server whatever its release.

The installed Lem's `lem` is Homebrew's `PREFIX/opt/lem/bin/lem` for a keg, as `lem doctor`
names it, else the `lem` beside the server's Python, which an upgrade of a uv tool or of a
checkout's `.venv` keeps in its place.
"""

from pathlib import Path
from typing import TYPE_CHECKING

from lem.board import install
from lem.kernel import paths, release
from lem.kernel.errors import Fault

if TYPE_CHECKING:
    from lem.board.facts import Facts

# The part of a path that names a Homebrew keg of Lem: `PREFIX/Cellar/lem/VERSION/...`.
KEG = "/Cellar/lem/"
OPT = Path("opt") / "lem"
COMMAND = Path("bin") / "lem"


def keg_of(package: Path) -> tuple[Path, Path] | None:
    """Homebrew's prefix and the keg that hold the package folder `package`, or None."""
    prefix, keg, rest = str(package).partition(KEG)
    if not keg:
        return None
    version = rest.split("/", 1)[0]
    return Path(prefix), Path(f"{prefix}{KEG}{version}")


def moved(package: Path) -> str | None:
    """Why Homebrew's `opt/lem` names another keg than the one of `package`, or None."""
    found = keg_of(package)
    if found is None:
        return None
    prefix, keg = found
    opt = prefix / OPT
    if not opt.exists() or opt.resolve() == keg.resolve():
        return None
    return f"{opt} names {opt.resolve()} now"


def missing(package: Path, stdlib: Path) -> str | None:
    """Which of the server's two folders an update removed: its Python's standard library
    `stdlib`, or its package folder `package`; None when both are there."""
    if not stdlib.is_dir():
        return f"the standard library of its Python, {stdlib}, is gone"
    if not package.is_dir():
        return f"its package folder {package} is gone"
    return None


def replaced(
    version: str, commit: str | None, package: Path, stdlib: Path
) -> str | None:
    """Why the install of release `version` and build `commit`, whose package folder is
    `package` and whose Python's standard library is in `stdlib`, is no longer the one
    installed; None while it is."""
    gone = missing(package, stdlib)
    if gone is not None:
        return gone
    try:
        now = release.named(paths.root(package))
    except Fault as error:
        return str(error)
    if now != version:
        return f"its package folder {package} holds Lem {now} now"
    built = install.commit_of(package)
    if built != commit:
        return f"its package folder {package} holds the build {built} of Lem {now} now"
    return moved(package)


def successor(package: Path, executable: Path) -> Path:
    """The installed Lem's `lem` by a path an update keeps: Homebrew's for a keg, else the one
    beside the Python `executable`."""
    found = keg_of(package)
    if found is not None:
        return found[0] / OPT / COMMAND
    return executable.parent / "lem"


def stale(found: Facts) -> str | None:
    """Why the running server `found` serves from an install that is no longer the one
    installed, whatever its release: it says so itself, its package folder is gone, or
    Homebrew's `opt/lem` names another keg; None when none of these holds."""
    if found.replaced is not None:
        return found.replaced
    package = Path(found.install.package)
    if not package.is_dir():
        return f"its package folder {package} is gone"
    return moved(package)
