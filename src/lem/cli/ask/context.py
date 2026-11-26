"""The session and task a question belongs to, when there is one."""

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

from lem.app.asking import live
from lem.app.sessions import log
from lem.cli import place
from lem.cli.ask.overlay import Overlay
from lem.kernel.errors import Refusal
from lem.ports.faults import Unanswered
from lem.store import places

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True, kw_only=True)
class Context:
    """The current overlay and the task folder where its card can wait."""

    overlay: Overlay
    task: Path | None


def here() -> Context | None:
    """The question runs in this session, or outside agterm."""
    session = os.environ.get("AGTERM_SESSION_ID")
    if os.environ.get("AGTERM_ENABLED") != "1" or not session:
        return None
    overlay = Overlay(environ=dict(os.environ), session=session)
    return Context(overlay=overlay, task=task_folder())


def task_folder() -> Path | None:
    """A task of the workspace that exists already. An ordinary question keeps no card."""
    slug = os.environ.get("LEM_TASK")
    if slug is None or not places.SLUG.fullmatch(slug):
        return None
    try:
        space = places.workspace(place.folder())
    except Refusal as error:
        if error.code in ("no-repository", "no-lem"):
            return None
        raise
    folder = places.task_folder(space.state, slug)
    return folder if (folder / "task.json").is_file() else None


def board_notice(here: Context) -> str | None:
    """Say when the owner cannot use a saved card on the board."""
    overlay = here.overlay
    if here.task is None:
        return None
    try:
        session = live.active(here.task, overlay.environ)
    except (OSError, Refusal, Unanswered) as error:
        return f"Lem could not check if the board will show the owner's card. {error}"
    if log.same(session, overlay.session):
        return None
    if session is not None:
        return (
            "The owner cannot answer this card on the board. "
            "The task has a live session in a different pane."
        )
    return "The board will not show the owner's card. This pane has no live session for this task."
