"""A workspace for a use case of a task's session: a checkout with Lem set up, on fakes, whose
command runs in the owner's own session of agterm."""

from typing import TYPE_CHECKING

from fakes.forge import LocalForge
from fakes.git import ModelGit
from fakes.ports import fake_ports
from fakes.records import record
from lem.app.sessions.here import Here
from lem.store import places, tasks
from unit.sessions.terminal import CALLER, LookingTerminal, with_caller

if TYPE_CHECKING:
    from pathlib import Path

    from fakes.harness import FakeHarness
    from lem.records.record import Record

SLUG = "gift-note"


def here_of(
    checkout: Path,
    terminal: LookingTerminal | None = None,
    harness: FakeHarness | None = None,
) -> Here:
    """A workspace in `checkout` with Lem set up, its home folder beside it."""
    (checkout / ".git").mkdir(parents=True, exist_ok=True)
    (checkout / ".lem").mkdir(exist_ok=True)
    places.state_of(checkout)
    git = ModelGit(checkout=checkout)
    ports = fake_ports(git, LocalForge(remote=git), terminal or with_caller(), harness)
    where = places.workspace(checkout)
    return Here(where=where, ports=ports, caller=CALLER.id, home=checkout / "home")


def made(here: Here, slug: str = SLUG, **fields: object) -> Record:
    """A task of the workspace, with `fields` over a queued one."""
    return tasks.create(here.where.state, record(slug, **fields))
