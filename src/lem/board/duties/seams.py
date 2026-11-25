"""Where one duty's failure stops: any failure of a duty gives its kind and
words, which the runner shows on the workspace's board or writes to the server's log, and the
other duties and workspaces still run (the seams of `serve.forge_loop` on `main`)."""

import importlib
import logging
from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from lem.board.duties.context import Duty

LOGGER = logging.getLogger(__name__)


def failure(path: str, duty: Duty) -> str | None:
    """Run the duty of `path`; why it failed, or None."""
    try:
        importlib.import_module(path).tick(duty)
    except Exception as error:
        LOGGER.debug("A board duty failed", exc_info=True)
        kind = type(error).__name__
        why = str(error)
        if isinstance(error, Refusal):
            why = f"{why}. {error.fix}"
        said = " ".join(why.split())
        return f"{kind}: {said}"
    return None
