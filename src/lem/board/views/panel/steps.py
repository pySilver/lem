"""The tab or step a task's panel shows besides its Overview (`board_task.panel` on `main`): the
other views' tabs from the functions the caller passes, and the steps of the owner's acts, each a
step of its own or the one that says why there is nothing to do now."""

from types import MappingProxyType
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.board.inputs.task.steps import NotNow
from lem.board.views.panel.card import card
from lem.board.views.panel.drop import drop
from lem.board.views.panel.merge import merge
from lem.board.views.panel.park import park

if TYPE_CHECKING:
    from lem.board.inputs.task.panel import Panel
    from lem.board.inputs.task.steps import Card, Drop, Merge, Park
    from lem.board.views.panel.opened import Opened, Sections, Shown

TABS = ("criteria", "checks", "timeline", "artifacts")


def tabbed(base: Panel, shown: Shown, sections: Sections) -> Panel:
    """The panel with the other view's tab its address shows, when the caller drew it."""
    shows = base.shows
    drawn = getattr(sections, shows) if shows in TABS else None
    if drawn is None:
        return base
    return replace(base, **{shows: drawn(shown.world, shown.seen)})


def stepped(base: Panel, shown: Shown, opened: Opened) -> Panel:
    """The panel with the step of an act its address shows, or why there is nothing to do."""
    maker = MAKERS.get(base.shows)
    if maker is None:
        return base
    made = maker(shown, opened)
    field = "not_now" if isinstance(made, NotNow) else base.shows
    return replace(base, **{field: made})


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
