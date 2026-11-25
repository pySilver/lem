"""Where one duty's failure stops: any failure of a duty becomes a `Fault` with its kind and
words, which the runner shows on the workspace's board or writes to the server's log, and the
other duties and workspaces still run (the seams of `serve.forge_loop` on `main`)."""

import importlib
from typing import TYPE_CHECKING

from lem.kernel.errors import Fault

if TYPE_CHECKING:
    from lem.board.duties.context import Duty


def failure(path: str, duty: Duty) -> str | None:
    """Run the duty of `path`; why it failed, or None."""
    try:
        contained(path, duty)
    except Fault as fault:
        return str(fault)
    return None


def contained(path: str, duty: Duty) -> None:
    """Run the duty of `path`; any failure becomes a `Fault` with its kind and words."""
    try:
        importlib.import_module(path).tick(duty)
    except Exception as error:
        kind = type(error).__name__
        said = " ".join(str(error).split())
        raise Fault(f"{kind}: {said}") from error
