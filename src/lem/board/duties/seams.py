"""Where one duty's failure stops: any failure of a duty gives its kind and words, which the
runner shows on the workspace's board or writes to the server's log, and the other duties and
workspaces still run (the seams of `serve.forge_loop` on `main`).

A refusal is a step that may not run now, and its words say all. Any other failure is a fault
of Lem, whose traceback goes to the server's log, at most once in `memory.TRACE_EVERY` for each
duty of a workspace: an import of a module whose file an update removed fails here too, and is
a fault.
"""

import importlib
import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from lem.board.duties import context
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from collections.abc import Callable

    from lem.board.duties.memory import Kept

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Failure:
    """A failed step of a duty: its words for the board and the log, and its exception."""

    said: str
    error: Exception

    @property
    def refused(self) -> bool:
        """Whether the step was refused, which has no traceback to keep."""
        return isinstance(self.error, Refusal)


def failure(path: str, duty: context.Duty) -> Failure | None:
    """Run the duty of `path`; why it failed, or None."""
    done = attempt(lambda: importlib.import_module(path).tick(duty))
    return done if isinstance(done, Failure) else None


def attempt[Made](step: Callable[[], Made]) -> Made | Failure:
    """What `step` gives, or why it failed."""
    try:
        return step()
    except Exception as error:
        LOGGER.debug("A step of the board's duties failed", exc_info=True)
        return Failure(said=said_of(error), error=error)


def said_of(error: Exception) -> str:
    """The failure's kind and words on one line, a refusal's fix after its why."""
    why = str(error)
    if isinstance(error, Refusal):
        why = f"{why}. {error.fix}"
    said = " ".join(why.split())
    return f"{type(error).__name__}: {said}"


def noted(
    kept: Kept, space: str, name: str, problem: str | None, failed: Failure | None
) -> None:
    """Show the problem `name` on the board of the workspace `space` and in the server's log,
    or forget it."""
    traced(kept, space, name, failed)
    if problem is None:
        kept.problems.pop(name, None)
        return
    kept.problems[name] = problem
    context.said(space, problem)


def traced(kept: Kept, space: str, name: str, failed: Failure | None) -> None:
    """The traceback of a fault of `name` in the server's log, at most once in TRACE_EVERY
    with the count of the failures since; a refusal has none."""
    if failed is None or failed.refused:
        return
    since = kept.traces.due(name, time.monotonic())
    if since is None:
        return
    LOGGER.error(
        "lem serve: %s: the traceback of the fault of %s, tried again at the next tick "
        "(%d more failures of it since its last traceback)",
        space,
        name,
        since,
        exc_info=failed.error,
    )
