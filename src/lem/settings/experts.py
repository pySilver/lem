"""The seats read into their parts, and the experts of a decision in doubt, each with its place
in a record and whether it can answer on this machine.

An expert answers only where its agent is on the machine: Claude Code is where Lem runs; Codex
needs its command (the owner, 2026-11-18: without Codex, "degraded to a single expert").
"""

import shutil
from typing import TYPE_CHECKING

import msgspec

from lem.settings.seats import PLACES, Seat, split

if TYPE_CHECKING:
    from collections.abc import Mapping

    from lem.settings.shared import Seats

CLAUDE = "claude"


class Expert(Seat, frozen=True, kw_only=True):
    """One expert: its seat's parts, its place in a record, and whether it can answer here."""

    place: str
    here: bool


def experts_of(given: Seats, environ: Mapping[str, str]) -> tuple[Expert, ...]:
    """The experts, each with its place and whether its agent is on this machine."""
    placed = zip(given.experts, PLACES, strict=False)
    return tuple(expert(line, place, environ) for line, place in placed)


def expert(line: str, place: str, environ: Mapping[str, str]) -> Expert:
    """One expert, at `place`, and whether its agent is on this machine."""
    parts = split(line)
    here = parts.agent == CLAUDE or answers(parts.agent, environ)
    return Expert(**msgspec.structs.asdict(parts), place=place, here=here)


def answers(agent: str, environ: Mapping[str, str]) -> bool:
    """Whether the command of `agent` is on the environment's `PATH`."""
    return shutil.which(agent, path=environ.get("PATH")) is not None


def seats_of(given: Seats) -> dict[str, Seat | None]:
    """Each seat but the experts read into its parts; the fallback None when it is off."""
    lines = msgspec.structs.asdict(given)
    return {
        name: split(line) if isinstance(line, str) else None
        for name, line in lines.items()
        if name != "experts"
    }
