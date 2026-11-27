"""Whether the install a running board server started from was replaced, and the installed
Lem's `lem` by a path that an update keeps.

An update replaces the install of a running server in one of three ways: it removes the package
folder (`brew upgrade` removes the keg of the release before), it writes another release into
the folder (an upgrade of a uv tool), or it points Homebrew's `opt/lem` at another keg
(`brew upgrade` with its clean-up off). The server's code is then of a release that is no
longer the one installed, and each step that reads a file of it can fail: on 2026-11-27 the
server of Lem 0.4.1 lost its notifications and then its duties after `brew upgrade` to 0.4.2.

The installed Lem's `lem` is Homebrew's `PREFIX/opt/lem/bin/lem` for a keg, as `lem doctor`
names it, else the `lem` beside the server's Python, which an upgrade of a uv tool or of a
checkout's `.venv` keeps in its place.
"""

from pathlib import Path

from lem.board import install
from lem.kernel import paths, release
from lem.kernel.errors import Fault

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


def replaced(version: str, commit: str | None, package: Path) -> str | None:
    """Why the install of release `version` and build `commit`, whose package folder is
    `package`, is no longer the one installed; None while it is."""
    if not package.is_dir():
        return f"its package folder {package} is gone"
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
