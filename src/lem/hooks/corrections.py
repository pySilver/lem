"""The `corrections` hook: the owner's message, for the correction queue, on his machine's yes.

It reads the message (`prompt`) only where `collect = true` under `[corrections]` in Lem's home
`machine.toml` says yes, in a home folder this Lem made, and only in a repository that uses Lem
(`.lem/settings.toml`) whose state folder is this Lem's or empty: with no such line, a file that
does not read, or a folder of Lem 0.3, it sends nothing, since a message leaves the machine only on
his yes. An empty message, a slash command and the text an agent's machinery puts into a user turn
are no message of his.

A message is claimed for one judgment (`claims.py`), written as one correction and handed to the
worker that asks Jev (`handoff.py`). With no session id nothing tells this message from the same
words of another session, so it is handed on with no claim; a claim that cannot be made costs a
double judgment and a note in the queue's log, never the message. It prints nothing.
"""

import os

from lem.hooks import claims, handoff, machine_yes, marker, other, raw, where

TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Mapping

# Text an agent's own machinery puts into a user turn; none of it is the owner's words.
INJECTED = (
    "<",
    "[peer chat]",
    "[agterm mailbox",
    "Caveat:",
    "This session is being continued",
    "[Request interrupted",
    "Base directory for this skill",
    "Stop hook",
    "[SYSTEM",
    "Another Claude session",
    "/",
)
TEAM = ".lem/settings.toml"


def answer(environ: Mapping[str, str], behind: str | None) -> str:
    """Hand the owner's message on when the machine and the repository say yes; say nothing."""
    found = raw.event()
    prompt = raw.text(found, "prompt").strip()
    if not typed(prompt) or not machine_says_yes(environ):
        return ""
    state = queue_of(found, environ)
    if state is not None:
        handed(found, environ, state, prompt)
    return ""


def typed(prompt: str) -> bool:
    """Whether `prompt` is words the owner typed: not empty, no slash command, nothing an
    agent's machinery wrote."""
    words = prompt.strip()
    return bool(words) and not words.startswith(INJECTED)


def machine_says_yes(environ: Mapping[str, str]) -> bool:
    """Whether Lem's home `machine.toml` says `collect = true` under `[corrections]`, in a home
    folder this Lem made; anything that does not read, and the home of Lem 0.3, is a no."""
    import tomllib

    home = marker.home_of(environ)
    if home is None or not marker.has(home):
        return False
    try:
        machine = tomllib.loads(raw.read_bytes(f"{home}/machine.toml").decode())
    except OSError, ValueError:
        return False
    return machine_yes.said_yes(machine)


def queue_of(found: raw.Event, environ: Mapping[str, str]) -> str | None:
    """The main checkout's queue when the originating worktree uses Lem and the state is
    this Lem's or empty. A link to another place is refused."""
    from pathlib import Path

    project = environ.get("CLAUDE_PROJECT_DIR")
    cwd = raw.text(found, "cwd") or project or "."
    worktree = where.checkout_of(cwd, main=False)
    if worktree is None or not (Path(worktree) / TEAM).is_file():
        return None
    checkout = where.parent(where.common_dir(f"{worktree}/.git"))
    state = f"{checkout}/{where.STATE}"
    if os.path.realpath(state) != state:
        return None
    return state if marker.ours(state, marker.STATE_EMPTY) else None


def handed(
    found: raw.Event, environ: Mapping[str, str], state: str, prompt: str
) -> None:
    """Claim the message, write it as a correction and start the worker on it. Nothing is
    written when the app's own `lem` is not there (an app whose files are not whole), and a
    claim of a message that was not handed on is given up, so another copy may judge it."""
    command = other.own_command()
    if not other.runnable(command):
        return
    session = raw.text(found, "session_id")
    cwd = os.path.realpath(
        raw.text(found, "cwd") or environ.get("CLAUDE_PROJECT_DIR") or "."
    )
    body = handoff.correction(session, cwd, prompt, raw.text(found, "transcript_path"))
    claim = claimed(state, session, prompt)
    if claim is None:
        return
    if not handoff.handed(state, body, command):
        if claim:
            handoff.gone(claim)
        handoff.logged(
            state, session, ("error", "the hook could not hand the message on")
        )


def claimed(state: str, session: str, prompt: str) -> str | None:
    """The claim of the message (empty with no session id, or when no claim can be made), or
    None when another copy holds it."""
    if not session:
        return ""
    try:
        return claims.claim(state, session, prompt)
    except OSError as error:
        note = (
            f"the hook could not claim the message ({error}); it was handed on as usual, and "
            "a second registration of the hook may queue it twice"
        )
        handoff.logged(state, session, ("note", note))
        return ""
