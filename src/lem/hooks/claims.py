"""The claim of one message for one judgment: a hook registered twice judges each message once.

Claude Code starts one copy of a hook for each place that registers it (the plugin's, and an entry
in a settings file), at the same moment. The first copy claims the message, the session and the
words, with an atomic create in `corrections-claims/` of the state folder, and a later copy of the
same message hands nothing on. The owner's ruling: "A correction hook registered twice judges each
message once."
"""

import os
import time

# How long a claim of one message holds. The copies of a hook registered twice start for the same
# event: Claude Code runs an event's hooks in parallel, each under its own timeout from its own
# start (code.claude.com/docs/en/hooks, read 2026-11-17), and that timeout is 10 seconds in
# `hooks/hooks.json`. A copy claims before that timeout ends it, so two claims of one event are
# less than 10 seconds apart. Twice that is a guess at the margin, for copies that start late on a
# loaded machine. The same words typed again in one session inside it count as one message.
CLAIM_SECONDS = 20
CLAIMS = "corrections-claims"
# Three tries: for copies that replace a stale claim of the same words together.
TRIES = 3
# A claim is made only where none is, never through a link, and read by the owner alone.
CREATE = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
OWNER_FILE = 0o600


def name_of(session: str, prompt: str) -> str:
    """The claim's name: a digest of the session and the words, so that no words of the owner
    are in a name."""
    import hashlib

    words = f"{session}\0{prompt}".encode("utf-8", "surrogatepass")
    return hashlib.sha256(words).hexdigest()


def stale(path: str) -> bool:
    """Whether the claim `path` is older than CLAIM_SECONDS; a claim that is gone is stale."""
    try:
        made = os.lstat(path).st_mtime
    except FileNotFoundError:
        return True
    return time.time() - made >= CLAIM_SECONDS


def set_aside(path: str) -> bool:
    """Remove the claim `path` when it is stale: True when it is gone, False for a fresh one. It
    is moved aside before its age is read, so that a claim another copy made at that moment is
    never removed by a look at the one before it: a fresh claim moved aside goes back."""
    from pathlib import Path

    mark = f"aside-{os.getpid()}-{time.monotonic_ns()}"
    aside = Path(f"{path}.{mark}")
    try:
        Path(path).rename(aside)
    except FileNotFoundError:
        return True
    if not stale(str(aside)):
        aside.rename(path)
        return False
    aside.unlink(missing_ok=True)
    return True


def swept(claims: str) -> None:
    """Remove the stale claims of the folder `claims`, so that it holds a few files at most."""
    with os.scandir(claims) as entries:
        held = [entry.path for entry in entries]
    for path in held:
        if stale(path):
            set_aside(path)


def claim(state: str, session: str, prompt: str) -> str | None:
    """Claim one message for this copy of the hook: the claim's path, or None when another copy
    claimed the same words of the same session less than CLAIM_SECONDS ago. Of two copies that
    look at the same moment one wins. OSError when no claim can be made."""
    from lem.hooks import marker

    claims = marker.own_folder(state, CLAIMS)
    swept(claims)
    path = f"{claims}/{name_of(session, prompt)}"
    for _ in range(TRIES):
        try:
            os.close(os.open(path, CREATE, OWNER_FILE))
        except FileExistsError:
            if not stale(path) or not set_aside(path):
                return None
        else:
            return path
    return None
