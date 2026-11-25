"""`Open a session` on a row of Waits for you, for a task whose phase gives it a session the
board may open (`board_model.opens_session` on `main`)."""

from typing import TYPE_CHECKING

from lem.app.sessions.phase import phase_or_none
from lem.board.inputs import names
from lem.board.inputs.forms import ActForm, Field

if TYPE_CHECKING:
    from lem.board.views.world import Seen, World

UNDER = "waits"


def opens_session(seen: Seen) -> bool:
    """Whether the task's phase gives it a session the board may open."""
    task = seen.record.task
    return phase_or_none(task, worktree=seen.worktree) is not None


def session_form(world: World, seen: Seen) -> ActForm:
    """`Open a session` for the task, from the row."""
    action = f"{names.task_href(world.viewer.base, seen.record.task.slug)}/session"
    return ActForm(
        action=action,
        label="Open a session",
        icon="play",
        press="go",
        busy="Opening…",
        fields=(Field(name="in", shown=UNDER),),
    )
