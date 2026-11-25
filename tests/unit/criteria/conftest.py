"""Each case of the criteria a home folder of its own: the owner's away or back, which a case
writes there, never reaches another case of the same worker."""

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture(autouse=True)
def own_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Point Lem's home folder into the case's own folder."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
