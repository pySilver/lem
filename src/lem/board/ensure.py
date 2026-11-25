"""`lem serve ensure` and `lem serve stop`: one board server for this machine, under the serve
lock, `serve.lock` in Lem's home folder, which spaces two starts at one moment.

`LEM_SERVE=off` makes `ensure` start nothing and end nothing: a test sets it, and a test that
starts a server on purpose leaves it out for that one call.
"""

import os
import time
from contextlib import contextmanager
from typing import TYPE_CHECKING

from lem.board import client, install, machine, start
from lem.board.facts import Facts, Shown, Stopped
from lem.kernel import locks, paths
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping
    from pathlib import Path

LOCK = "serve.lock"
# The most a call waits for another start: its stop and its start.
LOCK_WAIT = client.STOP_WAIT + start.START_WAIT
NO_START = "off"


@contextmanager
def serve_lock(home: Path) -> Iterator[None]:
    """Hold the serve lock, waiting at most LOCK_WAIT for another start."""
    home.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + LOCK_WAIT
    path = home / LOCK
    with path.open("a+", encoding="utf-8") as stream:
        while not locks.taken(stream):
            if time.monotonic() > deadline:
                raise Refusal(
                    "serve-lock",
                    f"another start of the board server holds {path} for over "
                    f"{LOCK_WAIT:g} s",
                    "wait a moment, then run this again",
                )
            time.sleep(start.POLL)
        yield


def shown(facts: Facts | None, *, started: bool, said: str | None = None) -> Shown:
    """What `ensure` prints of the server that runs, or of none."""
    if facts is None:
        return Shown(running=False, started=False, said=said)
    return Shown(
        running=True,
        started=started,
        pid=facts.pid,
        url=facts.url,
        host=facts.host,
        install=facts.install,
        said=said,
    )


def held(port: int, home: Path, environ: Mapping[str, str]) -> Shown:
    """`ensure` with the serve lock held: keep the server that runs unless this install
    replaces it, else end it and start one of this install."""
    found = client.ask(port, home)
    if environ.get("LEM_SERVE") == NO_START:
        return shown(
            found,
            started=False,
            said="LEM_SERVE=off is set: no server starts and none ends",
        )
    mine = install.install_of()
    if found is not None and not install.replaces(
        mine, found.install, settings_differ=found.door is not None
    ):
        said = None if found.install == mine else "another install of Lem serves"
        return shown(found, started=False, said=said)
    if found is not None:
        client.stop(port, home, found)
    return shown(start.started(port, home, environ), started=True)


def ensure(environ: Mapping[str, str] = os.environ) -> Shown:
    """Make sure one board server runs for this machine, and say which."""
    home = paths.home(environ)
    port = machine.port_of(home, environ)
    with serve_lock(home):
        return held(port, home, environ)


def stop(environ: Mapping[str, str] = os.environ) -> Stopped:
    """End the board server of this home folder, if one runs on its port."""
    home = paths.home(environ)
    port = machine.port_of(home, environ)
    with serve_lock(home):
        found = client.ask(port, home)
        if found is None:
            return Stopped(stopped=False, said=f"no board server runs on port {port}")
        client.stop(port, home, found)
    return Stopped(stopped=True, pid=found.pid, version=found.install.version)
