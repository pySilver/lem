"""The one JSON document every command prints."""

from typing import Literal

import msgspec

type Act = Literal["run", "spawn", "wait", "tell", "done"]


class Next(msgspec.Struct, frozen=True, kw_only=True, omit_defaults=True):
    """What comes next: a command to run, a builder's job, a wait, a line, or the end."""

    act: Act = msgspec.field(name="do")
    command: str | None = None
    job: str | None = None
    paths: tuple[str, ...] = ()
    until: str | None = None
    line: str | None = None
    why: str | None = None


class Refused(msgspec.Struct, frozen=True, kw_only=True):
    """A refusal as printed: exit 1."""

    code: str
    why: str
    fix: str


class Failed(msgspec.Struct, frozen=True, kw_only=True):
    """A fault as printed: exit 3."""

    line: str
    log: str


class Envelope(msgspec.Struct, frozen=True, kw_only=True, omit_defaults=True):
    """`ok`, then the outcome, a line for the owner, and what comes next."""

    ok: bool
    outcome: msgspec.Raw | None = msgspec.field(default=None, name="result")
    say: str | None = None
    following: Next | None = msgspec.field(default=None, name="next")
    refusal: Refused | None = None
    fault: Failed | None = None
