"""What `lem settings show` prints: every value in force with the file it comes from, each seat
read into its parts, the experts and whether each can answer on this machine, the places Lem
reads, and the load now against the gate of the landing's checks.

`settings` is None where Lem is not set up: the machine's numbers and the load still show.
"""

import os
from typing import TYPE_CHECKING

import msgspec

from lem.records.base import Frozen
from lem.settings.effective import Effective
from lem.settings.experts import Expert, experts_of, seats_of
from lem.settings.load import settings_of
from lem.settings.placed import Placed, places_of
from lem.settings.seats import Seat

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from lem.settings.machine import Load


class LoadNow(Frozen, frozen=True, kw_only=True):
    """The load average now, the cores, and the gate: `open`, `closed` with the number the
    checks wait for, or None where the machine took the gate away (`load.start = 0`)."""

    now: float
    cores: int | None
    gate: str | None = None


class Shown(msgspec.Struct, frozen=True, kw_only=True):
    """The settings in force and the file of each value, the seats' parts, the experts, the
    places, and the load now; `settings` is null where Lem is not set up, and says so."""

    checkout: str | None = None
    settings: Effective | None = None
    sources: dict[str, str] = msgspec.field(default_factory=dict, name="from")
    seats: dict[str, Seat | None] = msgspec.field(default_factory=dict)
    experts: tuple[Expert, ...] = ()
    places: dict[str, Placed] = msgspec.field(default_factory=dict)
    load: LoadNow


def load_now(given: Load) -> LoadNow:
    """The load average now against the machine's gate."""
    now = round(os.getloadavg()[0], 1)
    gate = None
    if given.start:
        gate = (
            "open"
            if now < given.start
            else f"closed: the checks wait for a load below {given.start:g}"
        )
    return LoadNow(now=now, cores=os.cpu_count(), gate=gate)


def shown(checkout: Path | None, environ: Mapping[str, str]) -> Shown:
    """The settings of `checkout`, the main checkout of a workspace where Lem is set up, or
    None outside one."""
    found = settings_of(checkout, environ)
    in_force = found.settings
    if checkout is None:
        return Shown(sources=found.sources, load=load_now(in_force.load))
    return Shown(
        checkout=str(checkout),
        settings=in_force,
        sources=found.sources,
        seats=seats_of(in_force.seats),
        experts=experts_of(in_force.seats, environ),
        places=places_of(checkout, in_force.paths),
        load=load_now(in_force.load),
    )
