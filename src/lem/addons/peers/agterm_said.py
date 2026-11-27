"""What agterm's words on a session of another Mac mean for the owner: each failure a refusal that
names its fix, and the check of a session id before any command takes it.

The words are agterm's own (agterm be92bc63, read 2026-11-27): ssh's text, which agterm passes on
("Connection refused", "Connection reset by peer"); the far shell's for a command it does not
find (exit 127); "zmx is unavailable in this instance" from an agterm outside Live sessions;
"the remote did not return a readable session list", "the remote agterm is too old to report its
zmx endpoint" and the far parser's "Unexpected argument" from an older agterm there; "the running
app is too old" from an older agterm here.
"""

import re

from lem.kernel.errors import Refusal

# A session's id, as agterm makes it: a UUID, in any case.
SESSION_ID = re.compile(
    r"[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}"
)
NO_COMMAND = ("exited with 127", "command not found", "agtermctl: not found")
NO_SSH = (
    "exited with 255",
    "could not start ssh",
    "permission denied",
    "could not resolve",
    "connection refused",
    "connection reset",
    "connection closed",
    "host key verification failed",
    "timed out",
    "no route to host",
)
NOT_LIVE = ("does not run live sessions", "zmx is unavailable")
FAR_OLD = (
    "too old",
    "readable session list",
    "unknown subcommand",
    "unexpected argument",
    "unknown option",
)
NO_CODE = 127
SSH_CODE = 255


def far(peer: str, host: str, said: str, code: int | None) -> Refusal:
    """The refusal for the far Mac's answer to `zmx tree HOST` or `zmx attach HOST`."""
    words = said.lower()
    if code == NO_CODE or any(word in words for word in NO_COMMAND):
        return Refusal(
            "peer-agtermctl",
            f"ssh reaches {host}, and finds no agtermctl there",
            f"on {peer}, the owner installs agterm's command line tool, from agterm's "
            "Help menu or its Homebrew cask",
        )
    if code == SSH_CODE or any(word in words for word in NO_SSH):
        return no_ssh(host, said)
    if any(word in words for word in NOT_LIVE):
        return not_live(peer)
    if any(word in words for word in FAR_OLD):
        return Refusal(
            "peer-agterm-old",
            f"the agterm on {peer} is too old to list its sessions for another Mac: {said}",
            f"on {peer}, the owner updates agterm",
        )
    return unknown(peer, said)


def here_old(what: str, said: str) -> Refusal:
    """This Mac's agterm is too old for `what`."""
    return Refusal(
        "agterm-old",
        f"the agterm on this Mac is too old to {what}: {said}",
        "on this Mac, the owner updates agterm",
    )


def no_ssh(host: str, said: str) -> Refusal:
    """ssh from this Mac does not reach the far Mac."""
    return Refusal(
        "peer-ssh",
        f"ssh from this Mac to {host} did not connect: {said}",
        f"the owner makes `ssh {host} true` work from this Mac with a key; for "
        f"another name, a `Host {host}` alias in ~/.ssh/config names it",
    )


def not_live(peer: str) -> Refusal:
    """The far agterm keeps no session for another Mac to attach."""
    return Refusal(
        "peer-agterm-live",
        f"the agterm on {peer} does not run Live sessions, and another Mac attaches only a "
        "live session (this Mac's agterm needs no Live sessions)",
        f"on {peer}, the owner sets Restore sessions to Live sessions in agterm's "
        "Settings, General, and restarts agterm",
    )


def gone(peer: str, session: str) -> Refusal:
    """The task's session is no longer on the far Mac."""
    return Refusal(
        "peer-session-gone",
        f"the session {session} of the task is gone on {peer}",
        f"the owner opens a session of the task again from the board of {peer}",
    )


def unknown(peer: str, said: str) -> Refusal:
    """agterm refused with words no rule here reads."""
    return Refusal(
        "peer-agterm",
        f"agterm did not show the session of {peer}: {said}",
        "the owner tries File, Attach Remote in agterm, which says the same step in "
        "its own words",
    )


def checked_id(session: str) -> str:
    """`session` when it is an agterm session id, before any command takes it."""
    if SESSION_ID.fullmatch(session) is None:
        raise Refusal(
            "session-id",
            f"{session!r} is no agterm session id",
            "the owner opens the task's page again and uses its Open the session",
        )
    return session
