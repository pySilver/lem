"""The `serve` hook: start this machine's board server when a Claude Code session starts or
resumes in a repository that uses Lem.

In a repository whose main checkout holds `.lem/settings.toml`, it starts `lem --repo CHECKOUT
serve ensure`, the `lem` beside this hook's Python, as a process of its own in a new session, and
returns at once: the session never waits for the server, which keeps the replace rule and its log,
and puts that main checkout on the machine's list of workspaces, whose duties the server runs.
Anywhere else, and with `LEM_SERVE=off`, it does nothing. It prints nothing: Claude Code takes a
SessionStart hook's output as context.
"""

import os

from lem.hooks import other, raw, where

TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Mapping

TEAM = ".lem/settings.toml"


def answer(environ: Mapping[str, str], behind: str | None) -> str:
    """Start the server for a session in a repository that uses Lem; say nothing."""
    checkout = wanted(raw.event(), environ)
    if checkout is not None:
        start(other.own_command(), checkout)
    return ""


def wanted(found: raw.Event, environ: Mapping[str, str]) -> str | None:
    """The main checkout of the session of the event `found` when it starts the server: Lem's
    server is not off, and the session's repository uses Lem; else None."""
    if environ.get("LEM_SERVE") == "off":
        return None
    checkout = where.checkout_here(found, environ)
    if checkout is None:
        return None
    return checkout if os.access(f"{checkout}/{TEAM}", os.F_OK) else None


def start(command: str, checkout: str) -> None:
    """Start `command --repo CHECKOUT serve ensure` detached, with no input and its output
    nowhere: the server writes its own log."""
    import subprocess

    subprocess.Popen(
        [command, "--repo", checkout, "serve", "ensure"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        cwd="/",
    )
