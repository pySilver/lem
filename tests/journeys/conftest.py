"""Each journey has a home folder of Lem of its own, with the load gate taken away.

The entry gives a whole run one home (`tests/conftest.py`), and the load gate keeps the
machine's line and its last start there (`app/landing/checks_gate.py`): a run of the checks in
one journey would wait at the gate behind the start of another journey's run, a minute on the
real clock, and on whatever load the machine has. So each journey starts with a home of its own
whose `machine.toml` sets `[load] start = 0`, no gate; a journey that tests the gate sets its own
number there (`tests/journeys/landing/test_checks.py`, `machine`).
"""

from typing import TYPE_CHECKING

import pytest

from lem.kernel import folders

if TYPE_CHECKING:
    from pathlib import Path

NO_GATE = "[load]\nstart = 0\n"


@pytest.fixture(autouse=True)
def own_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A home folder of Lem for this journey alone, whose machine has no load gate."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "own-config"))
    home = folders.home_for_writing({"XDG_CONFIG_HOME": str(tmp_path / "own-config")})
    (home / "machine.toml").write_text(NO_GATE)
    return home
