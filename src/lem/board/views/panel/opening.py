"""Whether the board offers "Open a session" for a task (`board_model.opens_session` on
`main`), and its form: nothing says its session lives, or it lives and the guard logged its
stop; and `lem session open` would take it (`phase_or_none`: not parked, not two releases back,
not ended unless its worktree stays for the cleanup), and it is not queued behind a task that
has not landed."""

from typing import TYPE_CHECKING

from lem.app.sessions.phase import phase_or_none
from lem.board.inputs.forms import ActForm, Field
from lem.board.inputs.names import task_href
from lem.model.task import behind

if TYPE_CHECKING:
    from lem.board.inputs.text import View
    from lem.board.views.world import Seen, World


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
    """Whether every prerequisite of the queued task landed or was answered."""
    records = tuple(each.record for each in world.tasks)
    return not behind.waited(seen.record.task, records)


def session_form(world: World, seen: Seen, *, under: View | None = None) -> ActForm:
    """`Open a session`, which posts to the task's own act, over the view of the page."""
    view = under or world.viewer.view
    fields = () if view == "tasks" else (Field(name="in", shown=view),)
    return ActForm(
        action=f"{task_href(world.viewer.base, seen.record.task.slug)}/session",
        label="Open a session",
        icon="play",
        press="go",
        busy="Opening…",
        fields=fields,
    )
