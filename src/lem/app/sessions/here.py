"""What every command of a task's session starts from: the workspace of the folder it runs in,
its ports bound to their adapters, the terminal's session it runs in, Lem's home folder, and the
envelope it prints."""

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

import msgspec

from lem.app import wiring
from lem.app.sessions.phase import Phase, phase_of, phase_or_none
from lem.kernel import paths
from lem.kernel.envelope import Envelope, Next
from lem.ports.place import Place
from lem.store import places

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.task import Task

# Where a task's worktree is, under the main checkout.
WORKTREES = ".lem/worktrees"


@dataclass(frozen=True, kw_only=True, slots=True)
class Here:
    """A workspace, its ports, the terminal's session the command runs in, and Lem's home."""

    where: places.Workspace
    ports: wiring.Ports
    caller: str | None = None
    home: Path | None = None

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

    def phase_or_none(self, task: Task) -> Phase | None:
        """The phase of the task's session now; None for a task that gets none."""
        return phase_or_none(task, worktree=self.worktree(task.slug) is not None)


def bound(folder: Path) -> Here:
    """The workspace of `folder`, with each port bound to its adapter."""
    where = places.workspace(folder)
    home = paths.home(os.environ)
    place = Place(checkout=where.checkout, home=home, environ=os.environ)
    ports = wiring.bound(place)
    return Here(where=where, ports=ports, caller=ports.terminal.here(), home=home)


def enveloped(outcome: msgspec.Struct, say: str, then: str | None = None) -> Envelope:
    """The envelope of a command of a session: its outcome, the line for the owner, and the
    command the caller runs next in the background, when there is one."""
    encoded = msgspec.Raw(msgspec.json.encode(outcome))
    following = None if then is None else Next(act="run", command=then)
    return Envelope(ok=True, outcome=encoded, say=say, following=following)
