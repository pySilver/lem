"""Where an adapter works, which `bind(place)` of each adapter module takes."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path


@dataclass(frozen=True, kw_only=True, slots=True)
class Place:
    """The workspace's main checkout, Lem's home folder, and the environment the command
    started with."""

    checkout: Path
    home: Path
    environ: Mapping[str, str]
