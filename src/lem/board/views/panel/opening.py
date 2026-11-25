"""Whether the board offers "Open a session" for a task (`board_model.opens_session` on
`main`), and its form: nothing says its session lives, or it lives and the guard logged its
stop; and `lem session open` would take it (`phase_or_none`: not parked, not two releases back,
not ended unless its worktree stays for the cleanup), and it is not queued behind a task that
has not landed."""

from typing import TYPE_CHECKING

from lem.app.sessions.phase import phase_or_none
from lem.board.inputs.forms import ActForm, Field
from lem.board.inputs.names import task_href

if TYPE_CHECKING:
    from lem.board.views.world import Seen, World

# The ends of a task before it that let a queued task start: a dropped one never gave its
# result.
STARTS = frozenset(("landed", "answered"))


def opens(world: World, seen: Seen) -> bool:
    """Whether the board offers a fresh session of the task of `seen`."""
    task, session = seen.record.task, seen.session
    held_back = task.status == "queued" and not after_ended(world, seen)
    if session is None or held_back:
        return False
    if session.live:
        return seen.stop is not None
    return phase_or_none(task, worktree=seen.worktree) is not None


def after_ended(world: World, seen: Seen) -> bool:
    """Whether the task the queued task waits for landed or was answered."""
    after = seen.record.task.after
    ends = {each.record.task.slug: each.record.task.status for each in world.tasks}
    return bool(after) and ends.get(after[0]) in STARTS


def session_form(world: World, seen: Seen) -> ActForm:
    """`Open a session`, which posts to the task's own act, over the view of the page."""
    under = world.viewer.view
    fields = () if under == "tasks" else (Field(name="in", shown=under),)
    return ActForm(
        action=f"{task_href(world.viewer.base, seen.record.task.slug)}/session",
        label="Open a session",
        icon="play",
        press="go",
        busy="Opening…",
        fields=fields,
    )
