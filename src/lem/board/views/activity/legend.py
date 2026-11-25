"""The legend of the chart Where the time went (`board_pages.legend` on `main`): one entry for
each look a bar of the chart has, the states drawn alike sharing it, in the order of the states;
queued and ready, which have a swatch of their own, each an entry of its own."""

from typing import TYPE_CHECKING

from lem.board.inputs.activity import Shade
from lem.board.views.activity import states

if TYPE_CHECKING:
    from datetime import datetime

    from lem.board.views.activity.lanes import Drawn
    from lem.board.views.activity.stretches import Stretch
    from lem.board.views.rule import Said


def shades(drawn: list[Drawn], now: datetime) -> tuple[Shade, ...]:
    """The legend's entries for the states the chart's bars held for some time."""
    held = {
        each.key for _, stretches in drawn for each in stretches if lasted(each, now)
    }
    groups: dict[str, list[str]] = {}
    for key in states.ORDER:
        if key in held:
            groups.setdefault(group_of(key), []).append(key)
    return tuple(shade(keys) for keys in groups.values())


def lasted(held: Stretch, now: datetime) -> bool:
    """Whether a stretch held its state for some time."""
    end = now if held.open else held.end
    return end > held.start


def group_of(key: str) -> str:
    """The entry a state shares: its look's, or its own when it has a swatch of its own."""
    look = states.said_of(key).look
    return f"{look}:{key}" if key in states.OWN_SWATCH else look


def shade(keys: list[str]) -> Shade:
    """One entry: its look, its own swatch's state, its states' words, and who acts in each."""
    said = [states.said_of(key) for key in keys]
    labels = " · ".join(each.label for each in said)
    acts = "\n".join(map(who_acts, said))
    own = own_swatch(keys)
    return Shade(look=said[0].look, status=own, label=labels, title=acts)


def who_acts(said: Said) -> str:
    """`Queued: Lem acts`."""
    return f"{said.label}: {said.who} acts"


def own_swatch(keys: list[str]) -> str | None:
    """The state of an entry with a swatch of its own."""
    first = keys[0]
    return first if first in states.OWN_SWATCH else None
