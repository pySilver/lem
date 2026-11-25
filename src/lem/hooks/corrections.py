"""The `corrections` hook: the owner's message, for the correction queue, on his machine's yes.

It reads the message (`prompt`) only where `collect = true` under `[corrections]` in Lem's home
`machine.toml` says yes, and only in a repository that uses Lem (`.lem/settings.toml`): with no
such line, or a file that does not read, it sends nothing, since a message leaves the machine
only on his yes. An empty message, a slash command and the text an agent's machinery puts into a
user turn are no message of his. It prints nothing.

The hand-off of a message to the queue (the claim of one message for one judgment, the detached
worker that asks Jev) is the step `sessions`'s: this hook decides which messages it would hand
on, and hands none on yet.
"""

import os
import tomllib

from lem.hooks import raw, where

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
    """Decide on the owner's message; say nothing."""
    found = raw.event()
    if typed(raw.text(found, "prompt")) and machine_says_yes(environ):
        collects(found, environ)
    return ""


def typed(prompt: str) -> bool:
    """Whether `prompt` is words the owner typed: not empty, no slash command, nothing an
    agent's machinery wrote."""
    words = prompt.strip()
    return bool(words) and not words.startswith(INJECTED)


def machine_says_yes(environ: Mapping[str, str]) -> bool:
    """Whether Lem's home `machine.toml` says `collect = true` under `[corrections]`; anything
    that does not read is a no."""
    home = home_of(environ)
    if home is None:
        return False
    try:
        machine = tomllib.loads(raw.read_bytes(f"{home}/machine.toml").decode())
    except OSError, ValueError:
        return False
    table = machine.get("corrections")
    return isinstance(table, dict) and table.get("collect") is True


def collects(found: raw.Event, environ: Mapping[str, str]) -> bool:
    """Whether the message was typed in a repository that uses Lem."""
    checkout = where.checkout_of(where.folder_of(found, environ))
    if checkout is None:
        return False
    return os.access(f"{checkout}/{TEAM}", os.F_OK)


def home_of(environ: Mapping[str, str]) -> str | None:
    """Lem's home folder, by the rule of `kernel.paths.home`; None for a relative
    XDG_CONFIG_HOME, which each folder would read as another place."""
    named = environ.get("XDG_CONFIG_HOME", "")
    if not named:
        return f"{environ.get('HOME', '')}/.config/lem"
    return f"{named}/lem" if named.startswith("/") else None
