"""The read-only part of the question overlay's agterm adapter."""

from typing import TYPE_CHECKING

import msgspec

from lem.adapters import agterm_ctl
from lem.hooks import agterm_process
from lem.kernel.errors import Fault
from lem.ports.faults import Unanswered

if TYPE_CHECKING:
    from collections.abc import Mapping

# agterm's pageExitCode (SocketClient.swift at 01489b93).
PAGE_EXITS = (("submitted", 0), ("pending", 1), ("dismissed", 2))


class PageRefused(Fault):
    """agterm answered the result request with a refusal."""


class PageOutcome(msgspec.Struct, frozen=True, kw_only=True):
    """What the owner did on the overlay, if agterm has an end for it."""

    kind: str | None = msgspec.field(name="outcome", default=None)
    payload: str | None = msgspec.field(name="value", default=None)


class OutcomeFields(msgspec.Struct, frozen=True, kw_only=True):
    """The part of the reply that names the page and the owner's act."""

    page: str | None = msgspec.field(name="pageID", default=None)
    id: str | None = None
    outcome: PageOutcome = msgspec.field(name="pageOutcome", default=PageOutcome())


class Reply(msgspec.Struct, frozen=True, kw_only=True):
    """agtermctl's JSON reply to an overlay request."""

    ok: bool = True
    error: str | None = None
    answer: OutcomeFields | None = msgspec.field(name="result", default=None)

    def accepts(self, verb: str, status: int) -> bool:
        """A result read uses the page state as its exit status."""
        if not self.ok or self.error:
            return True
        if verb != "result":
            return status == 0
        kind = self.answer.outcome.kind if self.answer else None
        return (kind, status) in PAGE_EXITS


def reply(environ: Mapping[str, str], *words: str, window: bool = True) -> Reply:
    """Ask agterm for a reply in its wire form."""
    ran = agterm_ctl.ctl(
        environment(environ), "session", "overlay", *words, "--json", window=window
    )
    try:
        decoded = msgspec.json.decode(ran.stdout, type=Reply)
    except msgspec.DecodeError as error:
        said = (ran.stderr or ran.stdout).strip() or f"exit {ran.returncode}"
        raise Unanswered(agterm_ctl.TOOL, said) from error
    if not decoded.accepts(words[0], ran.returncode):
        raise Unanswered(
            agterm_ctl.TOOL, f"unexpected {words[0]} exit {ran.returncode}"
        )
    return decoded


def outcome(environ: Mapping[str, str], page: str) -> PageOutcome:
    """Read a page's act, or say why agterm gave no result."""
    told = reply(environ, "result", "--page", page, window=False)
    if not told.ok or told.error or told.answer is None:
        why = told.error or "the page state is unknown"
        raise PageRefused(f"{agterm_ctl.TOOL}: {why}")
    return told.answer.outcome


def environment(environ: Mapping[str, str]) -> Mapping[str, str]:
    """Use the folder of the executable the owner named with AGTERMCTL, when set."""
    try:
        return agterm_process.ask_environment(environ)
    except ValueError as error:
        raise Unanswered(agterm_ctl.TOOL, str(error)) from error
