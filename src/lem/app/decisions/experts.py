"""The experts that answer on this machine, which `lem decisions log --by experts` writes as its
`advisers`, so that the record says one expert or two (`decisions.experts_here` on `main`).

The experts are the settings' `seats.experts` (the nearest file that names them, else Lem's
two), each `agent/model:effort` and named by its place, `fable` then `astra`; the ones whose
agent can run here answer.
"""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.ports.harness import Seat
from lem.settings.load import settings_of

if TYPE_CHECKING:
    from pathlib import Path

    from lem.ports.harness import Harness

PLACES = ("fable", "astra")


def seat_of(said: str) -> Seat:
    """A seat as `agent/model:effort` names it."""
    agent, _, rest = said.partition("/")
    model, _, effort = rest.partition(":")
    return Seat(agent=agent, model=model or None, effort=effort or None)


def here(harness: Harness, checkout: Path) -> tuple[str, ...]:
    """The places of the experts whose agent can run on this machine; none is refused."""
    experts = settings_of(checkout).settings.seats.experts
    seats = zip(experts, PLACES, strict=False)
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
