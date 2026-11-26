"""Read a session's overlay and restore its mark through the agterm transport."""

import json
import subprocess
import time
from tempfile import gettempdir
from typing import TYPE_CHECKING, NamedTuple

from lem.hooks import agterm_process, stop_cards, where

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

# The asynchronous rechecks and the limit of one agtermctl call, in seconds, from main.
RECHECKS = (0.5, 1.5, 3, 6)
CALL_LIMIT = 2


class Terminal(NamedTuple):
    """The terminal of the hook's own pane."""

    environ: Mapping[str, str]
    session: str

    def call(self, *words: str) -> str:
        """Run one agtermctl command with a bound, or end the hook on failure."""
        ran = agterm_process.run(
            self.environ, words, window=True, stdin="", timeout=CALL_LIMIT
        )
        ran.check_returncode()
        return ran.stdout

    def current(self, folder: Path) -> stop_cards.Overlay | None:
        """The first question that this session's tree shows."""
        tree = json.loads(self.call("tree", "--json"))["result"]["tree"]
        spaces = tree["workspaces"]
        sessions = (node for space in spaces for node in space.get("sessions") or ())
        node = next(
            (
                one
                for one in sessions
                if one["id"].casefold() == self.session.casefold()
            ),
            None,
        )
        return stop_cards.shown(node, folder) if node else None

    def mark(self, words: tuple[str, ...]) -> None:
        """Restore the waiting mark, with auto-reset on the owner's next visit."""
        pane = self.environ.get("AGTERM_PANE_ID")
        target = ("--pane-id", pane) if pane else ()
        self.call(
            "session",
            "status",
            *words,
            "--auto-reset",
            "--target",
            self.session,
            *target,
        )


def restore(environ: Mapping[str, str], session: str) -> None:
    """An agterm failure ends the courtesy silently."""
    try:
        restore_open(environ, session)
    except OSError, ValueError, subprocess.SubprocessError:
        return


def restore_open(environ: Mapping[str, str], session: str) -> None:
    """Start a recheck only for a pending question with a mark."""
    terminal = Terminal(agterm_process.ask_environment(environ), session)
    folder = stop_cards.pages(gettempdir())
    pending = terminal.current(folder)
    if pending is not None and stop_cards.asking(folder, pending):
        recheck(terminal, folder, pending.id, where.task_folder({}, environ))


def recheck(terminal: Terminal, folder: Path, page: str, task: str | None) -> None:
    """Restore only this question's mark, and only until it ends or goes quiet."""
    started = time.monotonic()
    for offset in RECHECKS:
        time.sleep(max(0, started + offset - time.monotonic()))
        pending = terminal.current(folder)
        if pending is None or pending.id != page or stop_cards.ended(task, page):
            return
        words = stop_cards.asking(folder, pending)
        if not words:
            return
        if pending.status != words[0]:
            terminal.mark(words)
