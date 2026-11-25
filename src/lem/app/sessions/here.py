"""What every command of a task's session starts from: the workspace of the folder it runs in,
its ports bound to their adapters, the task's folder and record, and the envelope it prints."""

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

import msgspec

from lem.app import wiring
from lem.app.sessions.phase import Phase, phase_of
from lem.kernel import paths
from lem.kernel.envelope import Envelope
from lem.ports.place import Place
from lem.store import places

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.task import Task

# Where a task's worktree is, under the main checkout.
WORKTREES = ".lem/worktrees"
# The session a command runs in, as agterm names it in each pane's environment: the slice's
# stand-in for a `Terminal.here()` (notes/slice-session.md).
CALLER = "AGTERM_SESSION_ID"


@dataclass(frozen=True, kw_only=True, slots=True)
class Here:
    """A workspace, its ports, and the terminal's session the command runs in."""

    where: places.Workspace
    ports: wiring.Ports
    caller: str | None = None

    def folder(self, slug: str) -> Path:
        """The folder of the task `slug`; refused for a name that is no task's."""
        return places.task_folder(self.where.state, slug)

    def worktree(self, slug: str) -> Path | None:
        """The task's worktree, when it is there."""
        path = self.where.checkout / WORKTREES / slug
        return path if (path / ".git").exists() else None

    def phase(self, task: Task) -> Phase:
        """The phase of the task's session now; refused for a task that gets none."""
        return phase_of(task, worktree=self.worktree(task.slug) is not None)


def bound(folder: Path) -> Here:
    """The workspace of `folder`, with each port bound to its adapter."""
    where = places.workspace(folder)
    place = Place(
        checkout=where.checkout, home=paths.home(os.environ), environ=os.environ
    )
    caller = os.environ.get(CALLER) or None
    return Here(where=where, ports=wiring.bound(place), caller=caller)


def enveloped(outcome: msgspec.Struct, say: str) -> Envelope:
    """The envelope of a command of a session: its outcome, and the line for the owner."""
    encoded = msgspec.Raw(msgspec.json.encode(outcome))
    return Envelope(ok=True, outcome=encoded, say=say)
