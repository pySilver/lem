"""`lem init`: the team's settings of a repository, and the ignore rules of what one machine
keeps in `.lem/`.

An import uses the old settings as defaults and keeps any values the team's file names. The
draft is checked as the team's file before it is written. An existing team's file without an
import, an origin outside GitHub and an unnamed base are refused.
"""

from typing import TYPE_CHECKING

from lem.app.init import draft, origin
from lem.app.init.checkout import locked, main_checkout
from lem.app.init.legacy import Migration
from lem.kernel import files, folders
from lem.kernel.errors import Refusal
from lem.records.base import Frozen
from lem.settings import places
from lem.settings.load import base_of

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

# What git never sees of `.lem/`: one machine's own settings, and Lem's state.
IGNORED = ("settings.local.toml", "state/")
NO_ORIGIN = (
    "this repository has no remote origin yet; Lem lands through GitHub pull requests, so add "
    "it (git remote add origin git@github.com:OWNER/REPO.git) before the first landing"
)


class Initialized(Frozen, frozen=True, kw_only=True):
    """What init wrote: the settings file, its base and reviewer, the ignore file, and what
    the owner must still do."""

    settings: str
    base: str
    reviewer: str
    ignore: str
    said: tuple[str, ...] = ()
    migration: Migration | None = None


def ignored(lem: Path) -> Path:
    """`.lem/.gitignore` with the lines of IGNORED it lacked."""
    ignore = lem / ".gitignore"
    known = ignore.read_text(encoding="utf-8").splitlines() if ignore.is_file() else []
    missing = [line for line in IGNORED if line not in known]
    if missing:
        lines = "\n".join([*known, *missing, ""])
        files.write_whole(ignore, lines.encode("utf-8"))
    return ignore


def inside(checkout: Path, relative: Path) -> Path:
    """`relative` in `checkout`, refused when a link leads it out of the checkout: init writes
    nowhere else."""
    path = checkout / relative
    if not path.parent.resolve().is_relative_to(checkout.resolve()):
        raise Refusal(
            "lem-folder",
            f"{path.parent} leads out of {checkout}",
            f"make {path.parent} a folder of the checkout, then run init again",
        )
    folders.inside_test_root(path.parent.resolve())
    return path


def initialized(
    folder: Path, base: str | None, codex: str, environ: Mapping[str, str]
) -> Initialized:
    """Write the team's settings of the repository `folder` is in."""
    checkout = main_checkout(folder)
    with locked(checkout):
        return initialized_in(checkout, base, codex, environ)


def initialized_in(
    checkout: Path, base: str | None, codex: str, environ: Mapping[str, str]
) -> Initialized:
    """Check and write the settings under the checkout's init lock."""
    path = inside(checkout, places.TEAM)
    old = checkout / places.LEGACY_TEAM
    if not (old.exists() or old.is_symlink()):
        old = None
    blocked = path.exists() and (old is None or not path.is_file())
    if path.is_symlink() or blocked:
        raise Refusal(
            "settings-exist", f"{path} already exists", f"edit {places.TEAM} by hand"
        )
    url = origin.origin_url(checkout, environ)
    origin.on_github(url)
    made = draft.prepared(path, old, base, codex, environ)
    return written(path, old, made, url)


def written(
    path: Path, old: Path | None, made: draft.Draft, url: str | None
) -> Initialized:
    """Publish the checked replacement before removing the old file."""
    base = base_of(made.team)
    path.parent.mkdir(exist_ok=True)
    ignore = ignored(path.parent)
    files.write_whole(path, made.text.encode("utf-8"))
    if old is not None:
        old.unlink(missing_ok=True)
        files.sync_folder(path.parent)
    return Initialized(
        settings=str(path),
        base=base,
        reviewer=made.team.seats.reviewer,
        ignore=str(ignore),
        said=() if url else (NO_ORIGIN,),
        migration=made.migration,
    )
