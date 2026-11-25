"""What every hook reads with the `os` and `io` modules alone: its event, a file, a folder.

A hook pays for each module it imports in the session's start (the design's part 5, about 50 ms
for the whole run), so these read with `os`, `io` and `select`, never `pathlib`. The event is read
until its first whole JSON object, or for `WAIT` seconds at most: a pipe that stays open never
holds the hook. A file is read and appended to through `io.FileIO`, whose one write is one
`os.write`.
"""

import io
import json
import os
import select
import sys
import time

# A hook's event: the JSON object Claude Code writes on its stdin.
type Event = dict[str, object]

# How long a hook waits for its event on stdin. A guess: Claude Code writes the event and closes
# the pipe at once, and a stuck pipe must not hold the hook.
WAIT = 2.0
# The most of one read from stdin.
CHUNK = 65536


def event() -> Event:
    """The hook's event from stdin: its first whole JSON object, or an empty one for anything
    else."""
    deadline = time.monotonic() + WAIT
    descriptor = sys.stdin.fileno()
    received = b""
    while chunk := next_chunk(descriptor, deadline):
        received += chunk
        found = parsed(received)
        if found is not None:
            return found
    return {}


def next_chunk(descriptor: int, deadline: float) -> bytes:
    """The next bytes of `descriptor`, or none at its end or after `deadline`."""
    left = deadline - time.monotonic()
    if left <= 0:
        return b""
    ready, _, _ = select.select([descriptor], [], [], left)
    return os.read(descriptor, CHUNK) if ready else b""


def parsed(received: bytes) -> Event | None:
    """`received` as a JSON object; an empty one for JSON of another kind; None while it is
    no whole JSON yet."""
    try:
        found = json.loads(received)
    except ValueError:
        return None
    return found if isinstance(found, dict) else {}


def text(found: Event, key: str) -> str:
    """The event's `key` when it is a text, else an empty one."""
    named = found.get(key)
    return named if isinstance(named, str) else ""


def read_bytes(path: str) -> bytes:
    """The bytes of the file `path`; OSError when it does not read."""
    with io.FileIO(path) as stream:
        return stream.readall()


def append(path: str, body: bytes) -> bool:
    """Append `body` to `path`, made when it is not there, in one write; False when its folder
    does not take it."""
    try:
        with io.FileIO(path, "a") as stream:
            stream.write(body)
    except OSError:
        return False
    return True


def is_folder(path: str) -> bool:
    """Whether `path` is a folder: a name with `/.` after it is found only for a folder."""
    return os.access(f"{path}/.", os.F_OK)
