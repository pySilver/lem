"""The plugin's SessionStart hook: start the board server of this machine when a Claude Code session
starts in a repository that uses Lem.

It reads the hook's event on stdin for the session's folder (`cwd`), finds the main checkout of its
repository, and when that holds `.lem/project.toml` it starts `serve.py --ensure` as a process of its
own, in a new session, with its output appended to the server's log in Lem's home folder, and
returns at once: the session never waits for the server. Anywhere else it does nothing. It prints
nothing, since Claude Code takes a SessionStart hook's output as context, and it exits 0 whatever
happens, a failure too: the board server is no part of a session.

The plugin starts it through `lem_python.py` beside this file, which runs it under a Python of 3.11
or newer when the first `python3` is older, and leaves the session silent when the machine has none.
"""

import sys

# How long git may take to name the main checkout. A guess: it answers in milliseconds, and a stuck
# git must not hold the hook.
GIT_TIMEOUT = 2


def main() -> None:
    import json
    import os
    import subprocess
    from pathlib import Path

    here = Path(__file__).resolve().parent
    sys.path.insert(0, str(here))
    import lem_state

    try:
        event = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        event = {}
    folder = event.get("cwd") if isinstance(event, dict) and isinstance(event.get("cwd"), str) else None
    folder = folder or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    try:
        root = lem_state.main_checkout(Path(folder), timeout=GIT_TIMEOUT)
    except lem_state.StateError:
        return
    if not (root / ".lem" / "project.toml").is_file():
        return
    home = lem_state.config()
    home.mkdir(parents=True, exist_ok=True)
    with (home / lem_state.SERVE_LOG).open("ab") as log:
        subprocess.Popen([sys.executable, "-B", str(here / "serve.py"), "--ensure"], stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                         start_new_session=True, close_fds=True, cwd=str(home))


if __name__ == "__main__":
    try:
        main()
    except BaseException:  # noqa: BLE001 - a hook that fails must not fail the session
        pass
    sys.exit(0)
