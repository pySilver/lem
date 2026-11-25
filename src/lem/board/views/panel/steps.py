"""The tab or step a task's panel shows besides its Overview (`board_task.panel` on `main`): the
other views' tabs from the functions the caller passes, and the steps of the owner's acts, each a
step of its own or the one that says why there is nothing to do now."""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.board.inputs.task.steps import NotNow
from lem.board.views.panel.card import card
from lem.board.views.panel.drop import drop
from lem.board.views.panel.merge import merge
from lem.board.views.panel.park import park

if TYPE_CHECKING:
    from functools import partial

    from lem.board.inputs.task.panel import Panel, Shows
    from lem.board.inputs.task.steps import Card, Drop, Merge, Park
    from lem.board.views.panel.opened import Opened, Sections, Shown

TABS = ("criteria", "checks", "timeline", "artifacts")


def body(
    base: partial[Panel], shows: Shows, shown: Shown, opened: Opened, sections: Sections
) -> Panel:
    """Construct the panel with its one required body."""
    if shows in TABS:
        drawn = getattr(sections, shows)
        if drawn is None:
            raise ValueError(f"the panel needs its {shows} section")
        return base(**{shows: drawn(shown.world, shown.seen)})
    made = MAKERS[shows](shown, opened)
    key = "not_now" if isinstance(made, NotNow) else shows
    return base(**{key: made})


def merge_step(shown: Shown, opened: Opened) -> Merge | NotNow:
    """The merge's confirm step."""
    return merge(shown.world, shown.seen, shown.standing)


def park_step(shown: Shown, opened: Opened) -> Park | NotNow:
    """The park's confirm step."""
    return park(shown.world, shown.seen, shown.standing, opened.asked)


def drop_step(shown: Shown, opened: Opened) -> Drop | NotNow:
    """The drop's confirm step."""
    return drop(shown.world, shown.seen, shown.standing, opened.asked)


def card_step(shown: Shown, opened: Opened) -> Card | NotNow:
    """The step of a card of the task's session."""
    return card(shown.world, shown.seen, shown.rows, opened.page or "")


MAKERS = MappingProxyType(
    {"merge": merge_step, "park": park_step, "drop": drop_step, "card": card_step}
)
