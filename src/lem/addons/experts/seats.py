"""Resolve the experts from the settings or the brief's own seats."""

import os
import re
from itertools import chain, repeat
from typing import TYPE_CHECKING

import msgspec

from lem.addons.cast.names import name_of
from lem.addons.experts.records import Named
from lem.kernel.errors import Refusal
from lem.settings import experts, seats
from lem.settings.load import settings_of
from lem.store.places import checkout_of

if TYPE_CHECKING:
    from pathlib import Path

# The explicit --seat grammar on main, 2026-11-25.
EXPLICIT = re.compile(r"[a-z]+(?:/[A-Za-z0-9][A-Za-z0-9._-]*)?(?::[a-z]+)?")


def chosen(folder: Path, given: tuple[str, ...]) -> tuple[Named, ...]:
    """Each expert that can answer, or each explicitly named seat."""
    found = explicit(given) if given else configured(folder)
    names = {seat.name for seat in found}
    if not found or len(names) != len(found):
        raise Refusal(
            "expert-seats",
            "the owner's experts must be available and have distinct answer names",
            "give --seat with models whose last words differ, or change seats.experts",
        )
    return found


def configured(folder: Path) -> tuple[Named, ...]:
    """The configured seats that can start on this machine."""
    settings = settings_of(checkout_of(folder)).settings
    return tuple(
        named(seats.split(seat.seat), seat.place)
        for seat in experts.experts_of(settings.seats, os.environ)
        if seat.here
    )


def explicit(given: tuple[str, ...]) -> tuple[Named, ...]:
    """An explicit seat may leave out either the model or the effort."""
    located = zip(given, chain(seats.PLACES, repeat(None)), strict=False)
    return tuple(named(parsed(line), place) for line, place in located)


def parsed(line: str) -> seats.Seat:
    """Check the seat's spelling and agent, with optional parts."""
    found = seats.split(line)
    if not EXPLICIT.fullmatch(line) or found.agent not in seats.BOTH:
        raise Refusal(
            "expert-seat",
            f"the owner's --seat {line!r} is not a Claude Code or Codex seat",
            "use agent/model:effort, with the model and effort optional",
        )
    return found


def named(seat: seats.Seat, place: str | None) -> Named:
    """An answer file takes the last word of its model, or its assigned place."""
    return Named(
        **msgspec.structs.asdict(seat),
        place=place,
        name=name_of(seat.model, place or seat.agent),
    )
