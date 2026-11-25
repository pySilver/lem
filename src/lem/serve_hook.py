"""The plugin's SessionStart hook: start the board server of this machine when a Claude
Code session starts in a repository that uses Lem.

It reads the hook's event on stdin for the session's folder (`cwd`), finds the main
checkout of its repository, and when that holds `.lem/settings.toml` it starts
`lem serve --ensure` through the package's entry, as a process of its own, in a new
session, with its output appended to the server's log in Lem's home folder, and returns
at once: the session never waits for the server. Anywhere else it does nothing. It
prints nothing, since Claude Code takes a SessionStart hook's output as context, and it
exits 0 whatever happens, a failure too: the board server is no part of a session.

The plugin starts it through Lem's app, `lem-hook serve` (`hooks.py` beside this
file).
"""

import sys

# How long git may take to name the main checkout. A guess: it answers in milliseconds,
# and a stuck git must not hold the hook.
GIT_TIMEOUT = 2


def main() -> None:
    import json
    import os
    import subprocess
    from pathlib import Path

    from lem import state as lem_state

    try:
        event = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        event = {}
    folder = (
        event.get("cwd")
        if isinstance(event, dict) and isinstance(event.get("cwd"), str)
        else None
    )
    folder = folder or os.environ.get("CLAUDE_PROJECT_DIR") or str(Path.cwd())
    try:
        root = lem_state.main_checkout(Path(folder), timeout=GIT_TIMEOUT)
    except lem_state.StateError:
        return
    if not (root / lem_state.TEAM_SETTINGS).is_file():
        return
    from lem import paths

    home = lem_state.config()
    home.mkdir(parents=True, exist_ok=True)
    with (home / lem_state.SERVE_LOG).open("ab") as log:
        subprocess.Popen(
            [sys.executable, "-B", str(paths.MAIN), "serve", "--ensure"],
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=log,
            start_new_session=True,
            close_fds=True,
            cwd=str(home),
        )
