"""The start of a board server as a process of its own: `lem serve run` of this install, with no
terminal, its output in `serve.log` of Lem's home folder.

The child imports Lem from the package folder of the process that starts it (`PYTHONPATH`), so
that the server runs the install whose `lem serve ensure` decided to start it, whichever `lem`
comes first on the PATH.
"""

import contextlib
import os
import subprocess
import sys
import time
from typing import TYPE_CHECKING

from lem.board import client
from lem.board.facts import Facts
from lem.kernel import clock, paths
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path


LOG = "serve.log"
# The size past which the log starts again empty at a start (`serve.LOG_CAP` on `main`).
LOG_CAP = 1_000_000
# How long a start may take until the server answers, in seconds, and how often it is asked.
START_WAIT = 10.0
POLL = 0.1
# The last lines of the log that a failed start shows.
TAIL = 4


def command(port: int) -> list[str]:
    """`lem serve run --port PORT` of this interpreter, with no bytecode written, no unsafe
    folder on the path, and no user site."""
    words = ("serve", "run", "--port", str(port))
    return [sys.executable, "-B", "-P", "-s", "-m", "lem", *words]


def trimmed(log: Path) -> None:
    """Empty the log when it grew past LOG_CAP."""
    with contextlib.suppress(FileNotFoundError):
        if log.stat().st_size > LOG_CAP:
            os.truncate(log, 0)


def launched(
    port: int, home: Path, environ: Mapping[str, str]
) -> subprocess.Popen[bytes]:
    """Start the server's process in a session of its own, its output in the log."""
    home.mkdir(parents=True, exist_ok=True)
    package = str(paths.PACKAGE.parent)
    moment = clock.now().isoformat()
    trimmed(home / LOG)
    with (home / LOG).open("ab") as log:
        log.write(f"{moment} lem serve ensure: port {port}\n".encode())
        log.flush()
        return subprocess.Popen(
            command(port),
            cwd=home,
            env={**environ, "PYTHONPATH": package},
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )


def ended(code: int, home: Path) -> Refusal:
    """The refusal of a server that ended at its start, with the last lines it logged."""
    log = home / LOG
    said = " ".join(
        log.read_text(encoding="utf-8", errors="replace").splitlines()[-TAIL:]
    )
    return Refusal(
        "server-start",
        f"the board server ended at its start with status {code}: {said}",
        f"read its log, {log}, and name another port when this one is held",
    )


def started(port: int, home: Path, environ: Mapping[str, str]) -> Facts:
    """Start a server on the port and wait until it answers as itself."""
    child = launched(port, home, environ)
    deadline = time.monotonic() + START_WAIT
    while time.monotonic() < deadline:
        code = child.poll()
        if code is not None:
            raise ended(code, home)
        facts = client.ask(port, home)
        if isinstance(facts, Facts) and facts.pid == child.pid:
            # it runs on its own now: nobody waits for its status
            child.returncode = 0
            return facts
        time.sleep(POLL)
    log = home / LOG
    raise Refusal(
        "server-start",
        f"the board server (pid {child.pid}) gave no answer in {START_WAIT:g} s; it may "
        "still start, and lem serve ensure says so then",
        f"read its log, {log}",
    )
