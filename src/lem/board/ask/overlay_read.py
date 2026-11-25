"""The read-only part of the question overlay's agterm adapter."""

from pathlib import Path
from typing import TYPE_CHECKING

import msgspec

from lem.adapters import agterm_ctl
from lem.ports.faults import Unanswered

if TYPE_CHECKING:
    from collections.abc import Mapping


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
    if ran.returncode and not decoded.error:
        raise Unanswered(agterm_ctl.TOOL, f"exit {ran.returncode}")
    return decoded


def outcome(environ: Mapping[str, str], page: str) -> PageOutcome:
    """Read a page's act, or say why agterm gave no result."""
    told = reply(environ, "result", "--page", page, window=False)
    if not told.ok or told.error or told.answer is None:
        raise Unanswered(agterm_ctl.TOOL, told.error or "the page state is unknown")
    return told.answer.outcome


def environment(environ: Mapping[str, str]) -> Mapping[str, str]:
    """Use the folder of the executable the owner named with AGTERMCTL, when set."""
    selected = environ.get("AGTERMCTL")
    if not selected:
        return environ
    path = Path(selected).expanduser().resolve()
    if path.name != agterm_ctl.TOOL:
        raise Unanswered(
            agterm_ctl.TOOL, "AGTERMCTL must name the agtermctl executable"
        )
    old = environ.get("PATH", "")
    return {**environ, "PATH": f"{path.parent}:{old}"}
