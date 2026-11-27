"""The `serve` hook: start this machine's board server when a Claude Code session starts or
resumes in a repository that uses Lem.

In a repository whose main checkout holds `.lem/settings.toml`, a fresh clone with no state
folder too, it starts `lem --repo CHECKOUT serve ensure`, the `lem` beside this hook's Python, as
a process of its own in a new session, and returns at once: the session never waits for the
server, which keeps the replace rule, and puts that main checkout on the machine's list of
workspaces, whose duties the server runs. The child's output goes into `serve.log` of Lem's
home folder, the server's own log, so that its refusal or fault is never lost; a home of this
Lem's, or one not made yet, which the hook makes as a command would. Anywhere else, in a state
folder of Lem 0.3, and with `LEM_SERVE=off`, it does nothing. It prints nothing: Claude Code
takes a SessionStart hook's output as context.
"""

import os

from lem.hooks import marker, other, raw, where

TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Mapping

TEAM = ".lem/settings.toml"
LOG = "serve.log"
APPEND = os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW


def answer(environ: Mapping[str, str], behind: str | None) -> str:
    """Start the server for a session in a repository that uses Lem; say nothing."""
    checkout = wanted(raw.event(), environ)
    if checkout is not None:
        start(other.own_command(), checkout, marker.home_of(environ))
    return ""


def wanted(found: raw.Event, environ: Mapping[str, str]) -> str | None:
    """The main checkout of the session of the event `found` when it starts the server: Lem's
    server is not off, the main checkout holds Lem's settings, and its state folder is not
    Lem 0.3's; else None."""
    if environ.get("LEM_SERVE") == "off":
        return None
    project = environ.get("CLAUDE_PROJECT_DIR")
    folder = raw.text(found, "cwd") or project or "."
    checkout = where.checkout_of(folder)
    return checkout if checkout is not None and usable(checkout) else None


def usable(checkout: str) -> bool:
    """Whether the main checkout holds Lem's settings, and its state folder holds no files of
    Lem 0.3: no marker and more than git's ignore file. An absent state folder, as in a fresh
    clone, is usable."""
    if not os.access(f"{checkout}/{TEAM}", os.F_OK):
        return False
    state = f"{checkout}/{where.STATE}"
    if marker.has(state):
        return True
    try:
        with os.scandir(state) as entries:
            held = {entry.name for entry in entries}
    except FileNotFoundError:
        return True
    return held <= marker.STATE_EMPTY


def log_of(home: str | None) -> int | None:
    """`serve.log` of Lem's home folder, open to append, the home made and marked when it is
    not there; None for a home of Lem 0.3, or one that cannot be made, or a log that does not
    open."""
    if home is None or not ours(home):
        return None
    try:
        return os.open(f"{home}/{LOG}", APPEND, raw.MODE)
    except OSError:
        return None


def ours(home: str) -> bool:
    """Whether Lem's home folder is this Lem's, made and marked now when it is not there;
    False when it cannot be made."""
    try:
        return marker.ours(home, frozenset())
    except OSError:
        return False


def start(command: str, checkout: str, home: str | None) -> None:
    """Start `command --repo CHECKOUT serve ensure` detached, with no input and its output in
    the server's log, or nowhere when there is no log to write."""
    import io
    import subprocess

    descriptor = log_of(home)
    if descriptor is None:
        started(command, checkout, subprocess.DEVNULL)
        return
    with io.FileIO(descriptor, "a") as stream:
        started(command, checkout, stream.fileno())


def started(command: str, checkout: str, output: int) -> None:
    """The detached child, its output and errors into `output`."""
    import subprocess

    subprocess.Popen(
        [command, "--repo", checkout, "serve", "ensure"],
        stdin=subprocess.DEVNULL,
        stdout=output,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        cwd="/",
    )
