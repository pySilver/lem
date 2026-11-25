"""The line of each act's result, kept by a token that the address of the page after the act
carries (`?note=TOKEN`), so that a refresh of that page, and every morph of it, still says what
came of the act (`serve.Notes` on `main`).

A merge runs on after its answer: its note says that it runs until it ends, and a second press
of the same task finds the first by its token. The notes live in the server's memory, an hour
each; the server holds no truth, and a note it lost is a line the page no longer shows.
"""

import secrets
import threading
import time
from typing import Literal

from msgspec.structs import replace

from lem.records.base import Frozen

type State = Literal["running", "done", "refused", "stands", "uncertain"]
type Merging = tuple[str, str]

# How long a note stays, in seconds: long enough for a second look on the phone, short enough
# that the server keeps few lines (`serve.NOTE_SECONDS` on `main`, a guess).
NOTE_SECONDS = 3600
# The bytes of a token.
TOKEN_BYTES = 6


class Note(Frozen, frozen=True, kw_only=True):
    """What came of an act: its task, the act, its state, and the line the page shows."""

    task: str | None = None
    act: str
    state: State
    said: str


class Notes:
    """The notes by token, each with the moment it was put, and the token of each task's merge
    that runs, by workspace and task."""

    def __init__(self) -> None:
        """Hold no note yet."""
        self.lock = threading.Lock()
        self.kept: dict[str, tuple[float, Note]] = {}
        self.merging: dict[Merging, str] = {}

    def put(self, note: Note) -> str:
        """Keep `note`, and give its token; drop the notes that are over an hour old."""
        token = secrets.token_hex(TOKEN_BYTES)
        moment = time.monotonic()
        with self.lock:
            fresh = {
                name: kept
                for name, kept in self.kept.items()
                if moment - kept[0] < NOTE_SECONDS
            }
            fresh[token] = (moment, note)
            self.kept = fresh
        return token

    def change(self, token: str, state: State, said: str) -> None:
        """Give the note of `token` a new state and line."""
        with self.lock:
            found = self.kept.get(token)
            if found is not None:
                changed = replace(found[1], state=state, said=said)
                self.kept[token] = (time.monotonic(), changed)

    def get(self, token: str | None) -> Note | None:
        """The note of `token`, while it is fresh."""
        with self.lock:
            found = self.kept.get(token or "")
        if found is None or time.monotonic() - found[0] >= NOTE_SECONDS:
            return None
        return found[1]

    def started(self, merging: Merging, note: Note) -> tuple[str, bool]:
        """The token of the task's merge that runs, or of a new one this call starts (True)."""
        with self.lock:
            running = self.merging.get(merging)
        if running is not None:
            return running, False
        token = self.put(note)
        with self.lock:
            running = self.merging.setdefault(merging, token)
        return running, running == token

    def running(self, merging: Merging) -> str | None:
        """The token of the task's merge that runs, or None."""
        with self.lock:
            return self.merging.get(merging)

    def ended(self, merging: Merging) -> None:
        """The task's merge ended."""
        with self.lock:
            self.merging.pop(merging, None)


# The server's one set of notes, which the pages read by the token of their address.
NOTES = Notes()
