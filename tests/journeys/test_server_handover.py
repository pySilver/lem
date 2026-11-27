"""A board server whose keg an update removed, as `brew upgrade` does: in the case's own home
folder of Lem, on a free port that is never the owner's, under a Homebrew prefix of the case's
own. The server says once that no installed Lem is there and keeps serving; once Homebrew's
`opt/lem` names the new keg, it hands over to that `lem serve ensure`, which replaces it, and
the board says once that Lem was updated, from which release.

The servers are held by the supervisor of `test_server_slice.py`, which signals a process only
while its pid, start time and command line still match.
"""

import os
import shutil
import sys
import time
from typing import TYPE_CHECKING, Any

import httpx
import pytest

from journeys.test_server_slice import (
    WAIT,
    Supervisor,
    ensured_by,
    facts_of,
    lem_home,
    make_install,
    workspace_at,
)
from lem.kernel import folders

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from pathlib import Path


@pytest.fixture
def supervisor() -> Iterator[Supervisor]:
    held = Supervisor()
    yield held
    held.end_all()
    assert held.running() == []


@pytest.fixture
def env(tmp_path: Path) -> dict[str, str]:
    """The case's environment: the entry's own HOME, a home folder of Lem of the case's own,
    and LEM_SERVE=off."""
    config = tmp_path / "config"
    (config / "lem").mkdir(parents=True)
    return {**os.environ, "XDG_CONFIG_HOME": str(config), "LEM_SERVE": "off"}


def logged(log: Path, line: str) -> str:
    """The server's log once it holds `line`."""
    deadline = time.monotonic() + WAIT
    while True:
        said = log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""
        if line in said or time.monotonic() > deadline:
            return said
        time.sleep(0.1)


def served_by(port: int, version: str) -> dict[str, Any]:
    """What the server on the port says of itself once it is of `version`."""
    deadline = time.monotonic() + WAIT
    while True:
        facts = facts_of(port)
        if facts["install"]["version"] == version or time.monotonic() > deadline:
            return facts
        time.sleep(0.1)


def brewed(keg: Path, record: Path) -> None:
    """The keg's `bin/lem`: the copy of Lem in the keg, run by this Python, which writes the
    import path it was given into `record` first."""
    command = keg / "bin" / "lem"
    command.parent.mkdir()
    command.write_text(
        "#!/bin/sh\n"
        f"printf '%s\\n' \"${{PYTHONPATH-unset}}\" >> '{record}'\n"
        f"PYTHONPATH='{keg / 'src'}' exec '{sys.executable}' -B -P -s -m lem \"$@\"\n"
    )
    command.chmod(0o755)


def test_a_server_whose_keg_an_update_removed_hands_over_and_the_board_says_lem_was_updated(
    tmp_path: Path,
    env: dict[str, str],
    supervisor: Supervisor,
    free_port: Callable[[], int],
) -> None:
    repo = workspace_at(tmp_path / "repo")
    port = free_port()
    supervisor.ports.append(port)
    home = folders.home_marked(lem_home(env))
    (home / "machine.toml").write_text(f"[serve]\nport = {port}\n")
    brew = tmp_path / "brew"
    old = brew / "Cellar" / "lem" / "1.0.0"
    first = ensured_by(make_install(old, "1.0.0"), repo, env)
    assert (first["started"], first["install"]["version"]) == (True, "1.0.0")
    [serving] = supervisor.running()

    shutil.rmtree(old)
    log = home / "serve.log"
    command = brew.resolve() / "opt" / "lem" / "bin" / "lem"
    unserved = f"No installed Lem is at {command}, so this server keeps serving"
    assert unserved in logged(log, unserved)
    assert facts_of(port)["pid"] == first["pid"]

    new = brew / "Cellar" / "lem" / "99.0.0"
    make_install(new, "99.0.0")
    record = tmp_path / "imports"
    brewed(new, record)
    (brew / "opt").mkdir()
    (brew / "opt" / "lem").symlink_to(new)

    facts = served_by(port, "99.0.0")
    assert facts["install"]["version"] == "99.0.0"
    assert facts["pid"] != first["pid"]
    assert f"It hands over to `{command} serve ensure`" in log.read_text()
    assert record.read_text().splitlines() == ["unset"]
    [replacing] = supervisor.running()
    assert replacing != serving
    assert replacing.pid == facts["pid"]
    base = f"http://127.0.0.1:{port}"
    notice = f"{base}/api/server/update"
    page = {"Origin": base}
    assert httpx.post(notice, headers=page).json() == {
        "version": "99.0.0",
        "previous_version": "1.0.0",
    }
    assert httpx.post(notice, headers=page).status_code == 204
