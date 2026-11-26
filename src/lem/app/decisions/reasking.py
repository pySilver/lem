"""Renew a breaker's question on the task's current revision."""

from functools import partial
from typing import TYPE_CHECKING

from lem.app.criteria import where
from lem.app.decisions.writing import updated
from lem.app.tasks import release
from lem.kernel import clock
from lem.model.decisions import reask

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.questions import Question


def reasked(folder: Path, slug: str, key: str, line: str) -> Question:
    """Return the new question after the session ends the Help talk."""
    state = where.here_of(folder, slug).workspace.state
    release.checked(state, slug)
    change = partial(reask.renewed, key=key, line=line, now=clock.now())
    return updated(state, slug, change).task.questions[-1]
