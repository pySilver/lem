"""`Open a session` on a row of Waits for you, for a task whose phase gives it a session the
board may open (`board_model.opens_session` on `main`)."""

from typing import TYPE_CHECKING

from lem.app.sessions.phase import phase_or_none

if TYPE_CHECKING:
    from lem.board.views.world import Seen


def opens_session(seen: Seen) -> bool:
    """Whether the task's phase gives it a session the board may open."""
    task = seen.record.task
    return phase_or_none(task, worktree=seen.worktree) is not None
