"""The workspace, task and saved question a card route names."""

from http import HTTPStatus
from typing import TYPE_CHECKING

from starlette.exceptions import HTTPException

from lem.board.ask import keys, saved
from lem.board.pages import place
from lem.kernel.errors import Refusal
from lem.store import places

if TYPE_CHECKING:
    from pathlib import Path

    from starlette.requests import Request

    from lem.records.questions import Question


def located(request: Request) -> tuple[Path, str, Question]:
    """Find the recorded card, or give the address's 404."""
    space = place.workspace(request)
    try:
        return read(space.state, request.path_params)
    except Refusal as error:
        raise HTTPException(HTTPStatus.NOT_FOUND, error.why) from error


def read(state: Path, named: dict[str, str]) -> tuple[Path, str, Question]:
    """Read a card by its two qualified path parts."""
    folder = places.task_folder(state, named["slug"])
    page = keys.checked(named["page"])
    asked = saved.question(folder, page)
    if asked is None:
        raise Refusal(
            "ask-page", f"the task has no card {page}", "open a card from the board"
        )
    return folder, page, asked
