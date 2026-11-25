"""The line of a view's keys under the stage (`board_pages.keys_line` on `main`): moving through
the cards and opening one, the key of each view on Activity; and on Waits for you, none while
nothing waits."""

from typing import TYPE_CHECKING

from lem.board.inputs.layout import KeyGroup, Keys

if TYPE_CHECKING:
    from lem.board.views.frame.counted import Counted

MOVE = KeyGroup(keys=("J", "K", "↑", "↓"), word="move")
KANBAN = Keys(
    id="kanban-keys",
    groups=(
        MOVE,
        KeyGroup(keys=("H", "L", "←", "→"), word="column"),
        KeyGroup(keys=("Enter",), word="open"),
        KeyGroup(keys=("Esc",), word="close"),
    ),
)
ACTIVITY = Keys(
    id="activity-keys", groups=(KeyGroup(keys=("T", "W", "B", "A"), word="view"),)
)


def keys_of(view: str, counts: Counted) -> Keys | None:
    """The keys of the view, or None for a view whose keys come from elsewhere (the
    backlog's) or that has none."""
    if view == "tasks":
        return KANBAN
    if view == "activity":
        return ACTIVITY
    if view == "waits":
        return waits_keys(counts)
    return None


def waits_keys(counts: Counted) -> Keys | None:
    """Waits for you's keys: a stack opens on Enter, a row goes."""
    if not counts.waits:
        return None
    stacked = any(len(group) > 1 for group in counts.stacks)
    opens = KeyGroup(keys=("Enter",), word="go or open" if stacked else "go")
    return Keys(id="waits-keys", groups=(MOVE, opens))
