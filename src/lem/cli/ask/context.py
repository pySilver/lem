"""The session and task a question belongs to, when there is one."""

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

from lem.board.ask import observe_card
from lem.cli import place
from lem.cli.ask.overlay import Overlay
from lem.kernel.errors import Refusal
from lem.store import places

if TYPE_CHECKING:
    from pathlib import Path

    from lem.cli.ask.answer import Words


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


def with_board_notice(here: Context, page: str, words: Words) -> Words:
    """Check the board as the command returns an open or pending card."""
    if here.task is not None and words.get("outcome") in ("open", "pending"):
        notice = observe_card.notice(here.task, page, here.overlay.environ)
        if notice is not None:
            words["board"] = notice
    return words
