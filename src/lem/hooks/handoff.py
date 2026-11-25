"""The hand-off of the owner's message to the worker that asks Jev, and the queue's log.

The hook writes the message as one correction, the JSON object of `records.corrections.Correction`
with the keys msgspec writes for it (`at`, `session`, `cwd`, `owner`, `previous`; Jev's
probability is the worker's), into a file of its own in `corrections-waiting/` of the state
folder, readable by the owner alone. Then it starts `lem corrections worker PATH`, the `lem` beside
this hook's Python, as a process of its own in a new session, and returns: the session never waits
for Jev. A failure goes to `corrections.log` beside the queue, never to the conversation.
"""

import io
import json
import os
import time

from lem.hooks import marker, raw, transcript

WAITING = "corrections-waiting"
LOG = "corrections.log"
# The text of `previous` when the transcript holds no agent text (`main`'s worker).
NO_PREVIOUS = "(no agent message before this one)"
# A file of its own for each message, never through a link, and read by the owner alone.
CREATE = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
OWNER_FILE = 0o600


def moment() -> str:
    """Now, in UTC, as a record writes a moment."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def correction(session: str, cwd: str, prompt: str, talk: str) -> bytes:
    """The correction of the message `prompt`, typed in `cwd` in the Claude Code session
    `session`, after the agent's last text in the transcript `talk`."""
    body = {
        "at": moment(),
        "session": session,
        "cwd": cwd,
        "owner": prompt,
        "previous": transcript.last_text(talk) or NO_PREVIOUS,
    }
    return json.dumps(body).encode()


def handed(state: str, body: bytes, command: str) -> bool:
    """Write the correction `body` into a file of its own, and start the worker `command` on
    it; False, with no file left, when either fails."""
    name = f"{time.time_ns()}-{os.getpid()}.json"
    try:
        path = f"{marker.own_folder(state, WAITING)}/{name}"
    except OSError:
        return False
    try:
        written(path, body)
    except OSError:
        gone(path)
        return False
    try:
        started(command, path)
    except OSError:
        # no worker reads it: the owner's words do not stay in a file nobody removes
        gone(path)
        return False
    return True


def written(path: str, body: bytes) -> None:
    """Write `body` into the new file `path`, in a folder only the owner reads."""
    descriptor = os.open(path, CREATE, OWNER_FILE)
    with io.FileIO(descriptor, "w") as stream:
        stream.write(body)


def started(command: str, path: str) -> None:
    """Start `command corrections worker PATH` as a process of its own, in a new session, with
    no input and its output nowhere: the hook does not wait for it."""
    import subprocess

    subprocess.Popen(
        [command, "corrections", "worker", path],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        cwd="/",
    )


def gone(path: str) -> None:
    """Remove the file `path` when it is there."""
    from pathlib import Path

    Path(path).unlink(missing_ok=True)


def logged(state: str, session: str, line: tuple[str, str]) -> None:
    """Append one line of the queue's log: a `note` (the message was still handed on) or an
    `error` (it was not), with its words."""
    kind, words = line
    entry = json.dumps({"at": moment(), "session": session, kind: words})
    raw.append(f"{state}/{LOG}", f"{entry}\n".encode())
