"""Settings for local board views. The peer registry reads its own table and reports its
refusal on each page that asks it for peer rows."""

from typing import TYPE_CHECKING

from lem.settings.load import loaded
from lem.settings.reading import Where

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from lem.settings.effective import Effective


def for_views(checkout: Path, home: Path, environ: Mapping[str, str]) -> Effective:
    """The local views' settings, with the peer table left to its reader."""
    return loaded(
        Where(checkout=checkout, home=home, environ=environ, read_peers=False)
    ).settings
