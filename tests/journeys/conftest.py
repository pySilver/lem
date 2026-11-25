"""Each journey has a home folder of Lem of its own, with the load gate taken away.

The entry gives each pytest process one home (`tests/conftest.py`). The load gate keeps the
machine's line and its last start there (`app/landing/checks_gate.py`), so one journey could
wait behind another on the same worker. Each journey starts with a home of its own whose
`machine.toml` sets `[load] start = 0`. A journey that tests the gate sets its own number there
(`tests/journeys/landing/test_checks.py`, `machine`).
"""

import os
import socket
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from lem.board import machine
from lem.kernel import folders

if TYPE_CHECKING:
    from collections.abc import Callable

NO_GATE = "[load]\nstart = 0\n"


@pytest.fixture(autouse=True)
def own_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A home folder of Lem for this journey alone, whose machine has no load gate."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "own-config"))
    home = folders.home_for_writing({"XDG_CONFIG_HOME": str(tmp_path / "own-config")})
    (home / "machine.toml").write_text(NO_GATE)
    return home


@pytest.fixture
def free_port() -> Callable[[], int]:
    """Give each server a loopback port the tests keep for it until the run ends."""
    claims = Path(os.environ[folders.TEST_ROOT]) / "journey-ports"
    claims.mkdir(exist_ok=True)

    def claim() -> int:
        # The child takes a port number, so the socket closes before the child binds.
        # Claim the number while the socket is bound so another worker cannot take it.
        while True:
            with socket.socket() as sock:
                sock.bind(("127.0.0.1", 0))
                port = sock.getsockname()[1]
                if port in {machine.PORT, machine.DOOR_PORT}:
                    continue
                try:
                    (claims / str(port)).touch(exist_ok=False)
                except FileExistsError:
                    continue
                return port

    return claim
