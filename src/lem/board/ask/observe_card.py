"""Read a card with the board's session scope and the overlay's choice of agtermctl."""

from typing import TYPE_CHECKING

from lem.app.asking import keys
from lem.app.asking.overlay_read import environment
from lem.board import opening
from lem.board.ask import visibility
from lem.board.duties import context
from lem.kernel import errors, paths
from lem.store import places

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path


def notice(
    folder: Path, page: str, session: str, environ: Mapping[str, str]
) -> str | None:
    """Say when the board cannot show or answer the card, or cannot be checked."""
    try:
        return checked(folder, page, session, environ)
    except (OSError, errors.Fault, errors.Refusal) as error:
        return visibility.unknown(str(error))


def checked(
    folder: Path, page: str, session: str, environ: Mapping[str, str]
) -> str | None:
    """Leave the caller's window as the board server does before it reads the terminal."""
    detached = dict(environ)
    opening.detached(detached)
    space = places.workspace(folder.parents[3])
    here = context.bound(space, environment(detached), paths.home(detached))
    return visibility.notice(here, folder.name, keys.question_id(page), session)
