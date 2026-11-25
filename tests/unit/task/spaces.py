"""A workspace for a task's test: a checkout with `.git` and `.lem`, its settings, and the
records a test puts there."""

from typing import TYPE_CHECKING

from fakes.records import record
from lem.store import places, tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.record import Record

SETTINGS = '[branch]\nbase = "main"\n'


def workspace(checkout: Path, settings: str = SETTINGS) -> places.Workspace:
    """A workspace in `checkout` with Lem set up and the team's `settings`."""
    (checkout / ".git").mkdir(parents=True, exist_ok=True)
    (checkout / ".lem").mkdir(exist_ok=True)
    (checkout / ".lem" / "settings.toml").write_text(settings, encoding="utf-8")
    places.state_of(checkout)
    return places.workspace(checkout)


def made(where: places.Workspace, slug: str, **fields: object) -> Record:
    """A task of the workspace, with `fields` over a queued one."""
    return tasks.create(where.state, record(slug, **fields))


def read(where: places.Workspace, slug: str) -> Record:
    """The record of `slug` as it is now."""
    return tasks.read(where.state, slug)
