"""The seat dispatched with each brief of the proposed tip."""

from typing import TYPE_CHECKING

import msgspec

from lem.app.sessions import seats
from lem.app.sessions.seating import Shown
from lem.kernel import files
from lem.records.base import Frozen, Sha
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.app.landing.frame import Context

NAME = "merge-seats.json"


class Dispatches(Frozen, frozen=True, kw_only=True):
    """One tip and round's seats, by the whole commit of the base each reads."""

    tip: Sha
    round: int
    bases: dict[Sha, Shown]


def matching(context: Context, tip: Sha) -> Dispatches:
    """The seats kept for this tip and round, or an empty set of bases."""
    round_number = (context.record.landing or Landing()).round
    try:
        written = (context.folder / NAME).read_bytes()
    except FileNotFoundError:
        return Dispatches(tip=tip, round=round_number, bases={})
    kept = msgspec.json.decode(written, type=Dispatches)
    if kept.tip == tip and kept.round == round_number:
        return kept
    return Dispatches(tip=tip, round=round_number, bases={})


def kept(context: Context, tip: Sha, base: Sha) -> str | None:
    """The seat printed with this brief, independent of later changes to the settings."""
    shown = matching(context, tip).bases.get(base)
    return shown.seat if shown and shown.seat else None


def dispatched(context: Context, tip: Sha, base: Sha) -> Shown:
    """Keep the dispatched seat beside this brief before the stage can start its agent."""
    shown = seats.effective(context.record, "merger", context.workspace.checkout)
    bound = matching(context, tip)
    bound.bases[base] = shown
    files.write_whole(context.folder / NAME, msgspec.json.encode(bound))
    return shown
