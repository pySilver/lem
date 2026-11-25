"""A workspace for a task's test: a checkout with `.git` and `.lem`, its settings, and the
records a test puts there."""

from typing import TYPE_CHECKING, Any, cast

from fakes.records import record
from lem.records.journal.task import StateNoted
from lem.store import places, tasks

if TYPE_CHECKING:
    from pathlib import Path

    from fakes.command import Ran
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


def result(ran: Ran) -> dict[str, Any]:
    """The result of a command that printed one object."""
    found = ran.result()
    assert isinstance(found, dict), ran
    return cast("dict[str, Any]", found)


def rows(ran: Ran) -> list[dict[str, Any]]:
    """The result of a command that printed a list of objects."""
    found = ran.result()
    assert isinstance(found, list), ran
    return cast("list[dict[str, Any]]", found)


def refusal(ran: Ran) -> dict[str, Any]:
    """The refusal a command printed."""
    found = ran.envelope().get("refusal")
    assert ran.code == 1, ran
    assert isinstance(found, dict), ran
    return cast("dict[str, Any]", found)


def said(ran: Ran) -> str:
    """The line a command said."""
    found = ran.envelope().get("say")
    assert isinstance(found, str), ran
    return found


def last_line(where: places.Workspace, slug: str) -> str | None:
    """The line of the newest state entry of `slug`'s journal."""
    entries = [
        entry for entry in read(where, slug).journal if isinstance(entry, StateNoted)
    ]
    return entries[-1].line
