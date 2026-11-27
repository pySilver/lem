"""What `agtermctl --json` says when it refuses: with `--json` it prints agterm's own reply to
standard output, `{"ok": false, "error": "..."}`, and exits other than 0; its own parser refuses
words it does not know on standard error with exit 64 (agterm be92bc63, `SocketClient.swift`,
`printResponse`, read 2026-11-27).

A refusal is `Refused`: agterm's words, the exit, and whether this Mac's agtermctl did not know
the words at all (an older agterm here). The peers' rules read it (`addons/peers/agterm_said.py`).
"""

from typing import TYPE_CHECKING

import msgspec

from lem.adapters.agterm_ctl import TOOL, ctl
from lem.ports.faults import Unanswered

if TYPE_CHECKING:
    import subprocess
    from collections.abc import Mapping

# The exit of Swift's argument parser for words it does not know.
USAGE = 64


class Refused(Unanswered):
    """A call of agtermctl that exited other than 0: what it said, its exit, and whether its
    own parser refused the words."""

    def __init__(self, said: str, code: int, *, usage: bool = False) -> None:
        """Keep the words, the exit and the parser's refusal."""
        super().__init__(TOOL, said)
        self.code = code
        self.usage = usage


class Failure(msgspec.Struct, frozen=True, kw_only=True):
    """agterm's reply to a call it refused."""

    ok: bool = True
    error: str | None = None


def error_of(printed: str) -> str | None:
    """agterm's own words in a reply it printed, or None when the reply holds none."""
    try:
        reply = msgspec.json.decode(printed.strip() or "{}", type=Failure)
    except msgspec.DecodeError:
        return None
    return None if reply.ok else (reply.error or "").strip() or None


def refused_by(ran: subprocess.CompletedProcess[str]) -> Refused:
    """The refusal of a call that exited other than 0."""
    replied = error_of(ran.stdout)
    printed = (ran.stderr or ran.stdout).strip()
    told = replied or printed or f"exit {ran.returncode}"
    usage = replied is None and ran.returncode == USAGE
    return Refused(told, ran.returncode, usage=usage)


def asked(environ: Mapping[str, str], *words: str, window: bool = True) -> str:
    """What `agtermctl WORDS` printed; `Refused` when it exits other than 0."""
    ran = ctl(environ, *words, window=window)
    if ran.returncode:
        raise refused_by(ran)
    return ran.stdout


def decoded[Shape](printed: str, shape: type[Shape], call: str) -> Shape:
    """agterm's answer to `call`; `Unanswered` for one that is not of its form."""
    try:
        return msgspec.json.decode(printed, type=shape)
    except msgspec.DecodeError as error:
        raise Unanswered(
            TOOL, f"{call} printed no answer of its form ({error})"
        ) from error


def checked[Shape](
    ran: subprocess.CompletedProcess[str], shape: type[Shape], call: str
) -> Shape:
    """agterm's answer to `call` that ran; `Refused` when it exited other than 0."""
    if ran.returncode:
        raise refused_by(ran)
    return decoded(ran.stdout, shape, call)
