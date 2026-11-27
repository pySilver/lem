"""The team's settings draft, checked before init replaces either file."""

from typing import TYPE_CHECKING

from lem.app.init import legacy, origin, template
from lem.kernel import paths
from lem.records.base import Frozen
from lem.settings import files, places, reading
from lem.settings.team import Team

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path


class Draft(Frozen, frozen=True, kw_only=True):
    """The text, the settings reported by init, and the result of any import."""

    text: str
    team: Team
    migration: legacy.Migration | None = None


def prepared(
    path: Path,
    old: Path | None,
    base: str | None,
    codex: str,
    environ: Mapping[str, str],
) -> Draft:
    """Refuse a draft that the normal reader for the team's file would refuse."""
    text, migration = (
        (template.written(origin.base_of(path.parent.parent, base), codex), None)
        if old is None
        else legacy.migrated(path, old, base, codex)
    )
    where = reading.Where(
        checkout=path.parent.parent, home=paths.home(environ), environ=environ
    )
    name = str(places.TEAM)
    if old is not None:
        name = f"{name} draft from {places.LEGACY_TEAM}"
    tables = files.decoded(text.encode("utf-8"), name)
    reading.check(tables, places.Scope.team, name, where)
    return Draft(
        text=text, team=files.converted(tables, Team, name), migration=migration
    )
