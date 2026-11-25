"""`lem init`: the team's settings of a repository written once, and the ignore rules of what
one machine keeps in `.lem/`.

It refuses a settings file that is there (an onboarding that finishes changes no setting), an
origin that is not on GitHub, and a base it cannot tell. The text is read back as the team's
file before it is written, so init never writes a file Lem would refuse. It links and moves
nothing: another tool's cast or profile stays where it is.
"""

import tomllib
from typing import TYPE_CHECKING

from lem.app.init import origin, template
from lem.app.init.checkout import main_checkout
from lem.kernel import files, paths
from lem.kernel.errors import Refusal
from lem.records.base import Frozen
from lem.settings import places, reading

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


def base_of(checkout: Path, given: str | None) -> str:
    """The base the call names, else origin's default branch; refused when neither names one."""
    base = given or origin.default_branch(checkout)
    if not base:
        raise Refusal(
            "no-base",
            f"cannot tell the base branch of {checkout}: origin names no default branch",
            "name it: lem init --base BRANCH",
        )
    return base


def ignored(lem: Path) -> Path:
    """`.lem/.gitignore` with the lines of IGNORED it lacked."""
    ignore = lem / ".gitignore"
    known = ignore.read_text(encoding="utf-8").splitlines() if ignore.is_file() else []
    missing = [line for line in IGNORED if line not in known]
    if missing:
        lines = "\n".join([*known, *missing, ""])
        files.write_whole(ignore, lines.encode("utf-8"))
    return ignore


def checked_text(checkout: Path, text: str, environ: Mapping[str, str]) -> None:
    """Refuse a text Lem would refuse as the team's file of `checkout`."""
    where = reading.Where(checkout=checkout, home=paths.home(environ), environ=environ)
    tables = tomllib.loads(text)
    reading.check(tables, places.Scope.team, places.TEAM.as_posix(), where)


def initialized(
    folder: Path, base: str | None, codex: str, environ: Mapping[str, str]
) -> Initialized:
    """Write the team's settings of the repository `folder` is in."""
    checkout = main_checkout(folder)
    path = checkout / places.TEAM
    if path.exists():
        raise Refusal(
            "settings-exist", f"{path} already exists", f"edit {places.TEAM} by hand"
        )
    url = origin.origin_url(checkout, environ)
    origin.on_github(url)
    chosen = base_of(checkout, base)
    text = template.written(chosen, codex)
    checked_text(checkout, text, environ)
    path.parent.mkdir(exist_ok=True)
    files.write_whole(path, text.encode("utf-8"))
    return Initialized(
        settings=str(path),
        base=chosen,
        reviewer=template.reviewer_of(codex),
        ignore=str(ignored(path.parent)),
        said=() if url else (NO_ORIGIN,),
    )
