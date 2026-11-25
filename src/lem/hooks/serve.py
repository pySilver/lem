"""The `serve` hook: start this machine's board server when a Claude Code session starts or
resumes in a repository that uses Lem.

In a repository whose main checkout holds `.lem/settings.toml`, it starts `lem serve ensure`, the
`lem` beside this hook's Python, as a process of its own in a new session, and returns at once:
the session never waits for the server, which keeps the replace rule and its log. Anywhere else,
and with `LEM_SERVE=off`, it does nothing. It prints nothing: Claude Code takes a SessionStart
hook's output as context.
"""

import os

from lem.hooks import other, raw, where

TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Mapping

TEAM = ".lem/settings.toml"


def answer(environ: Mapping[str, str], behind: str | None) -> str:
    """Start the server for a session in a repository that uses Lem; say nothing."""
    if wanted(raw.event(), environ):
        start(other.own_command())
    return ""


def wanted(found: dict[str, object], environ: Mapping[str, str]) -> bool:
    """Whether the session of the event `found` starts the server: Lem's server is not off,
    and the session's repository uses Lem."""
    if environ.get("LEM_SERVE") == "off":
        return False
    checkout = where.checkout_here(found, environ)
    if checkout is None:
        return False
    return os.access(f"{checkout}/{TEAM}", os.F_OK)


def start(command: str) -> None:
    """Start `command serve ensure` detached, with no input and its output nowhere: the
    server writes its own log."""
    import subprocess

    subprocess.Popen(
        [command, "serve", "ensure"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        cwd="/",
    )
