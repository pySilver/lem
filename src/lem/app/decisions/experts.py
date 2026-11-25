"""The experts that answer on this machine, which `lem decisions log --by experts` writes as its
`advisers`, so that the record says one expert or two (`decisions.experts_here` on `main`).

The experts are the settings' `seats.experts`, the local file's over the team's, each
`agent/model:effort` and named by its place, `fable` then `astra`; the ones whose agent can run
here answer. A stand-in until the step `settings` reads the seats, from the same tables.
"""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.ports.harness import Seat
from lem.settings import places
from lem.settings.load import tables

if TYPE_CHECKING:
    from pathlib import Path

    from lem.ports.harness import Harness

EXPERTS = ("claude/fable:high", "codex/gpt-6.2-astra:high")
PLACES = ("fable", "astra")


def named(checkout: Path) -> tuple[str, ...]:
    """The seats of `seats.experts`: the local file's, else the team's, else Lem's two."""
    for path in (checkout / places.LOCAL, checkout / places.TEAM):
        found = tables(path) if path.is_file() else {}
        seats = found.get("seats")
        given = seats.get("experts") if isinstance(seats, dict) else None
        if isinstance(given, list) and given:
            return tuple(str(seat) for seat in given)
    return EXPERTS


def seat_of(said: str) -> Seat:
    """A seat as `agent/model:effort` names it."""
    agent, _, rest = said.partition("/")
    model, _, effort = rest.partition(":")
    return Seat(agent=agent, model=model or None, effort=effort or None)


def here(harness: Harness, checkout: Path) -> tuple[str, ...]:
    """The places of the experts whose agent can run on this machine; none is refused."""
    seats = zip(named(checkout), PLACES, strict=False)
    found = tuple(
        place for seat, place in seats if harness.available(seat_of(seat)) is None
    )
    if found:
        return found
    raise Refusal(
        "no-expert",
        "no expert of the settings' seats.experts can answer on this machine",
        'name a seat of an agent it has, as experts = ["claude/fable:high"]',
    )
