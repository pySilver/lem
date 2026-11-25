"""A workspace for the cases of a task's criteria and decisions: a checkout with Lem set up, a
task in it, its `criteria.md`, its worktree and its plan, all in the case's own folder."""

import os
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from fakes.records import record
from lem.kernel import paths
from lem.records.holds import OwnerHold
from lem.store import owner, places, tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.record import Record

SLUG = "gift-note"
# A moment before any the clock gives a case, so that what a case writes now comes after it.
EARLY = datetime(2026, 1, 1, 9, 0, tzinfo=UTC)
WAITS = OwnerHold(on="criteria", line="the criteria wait for the owner", since=EARLY)
INTERVIEW = OwnerHold(
    on="interview", line="the interview waits for the owner", since=EARLY
)

FULL = """## Acceptance criteria

Size: full, because the export gets a new column and two readers of it.

1. A CSV export holds the gift note of an order: order 1042 with the note "for Ania" has
   that text in its row.
2. An order with no gift note has an empty cell, not the word "None".
"""
SMALL = """## Acceptance criteria

Size: small, because it is one word of the README.

1. The README says receive, not recieve.
"""
TESTED = """   - test: `python3 -m unittest tests.test_export.GiftNote` in `tests/test_export.py`
"""


def workspace(folder: Path) -> Path:
    """A main checkout in `folder` with Lem set up."""
    (folder / ".git").mkdir(parents=True, exist_ok=True)
    (folder / ".lem").mkdir(exist_ok=True)
    places.state_of(folder)
    return folder


def task(checkout: Path, slug: str = SLUG, **fields: object) -> Record:
    """A task of the workspace, shaping unless `fields` say otherwise."""
    made = record(slug, **{"status": "shaping", **fields})
    return tasks.create(checkout / places.STATE, made)


def read(checkout: Path, slug: str = SLUG) -> Record:
    """The task's record now."""
    return tasks.read(checkout / places.STATE, slug)


def sheet(checkout: Path, text: str, slug: str = SLUG) -> Path:
    """The task's `criteria.md`, written."""
    path = places.task_folder(checkout / places.STATE, slug) / "criteria.md"
    path.write_text(text, encoding="utf-8")
    return path


def worktree(checkout: Path, slug: str = SLUG) -> Path:
    """The task's worktree, as far as the criteria look: a folder with `.git`."""
    folder = checkout / ".lem" / "worktrees" / slug
    (folder / ".git").mkdir(parents=True, exist_ok=True)
    return folder


def plan(checkout: Path, text: str, slug: str = SLUG, day: str = "2026-11-25") -> Path:
    """The task's plan in its worktree, of the day `day`."""
    folders = worktree(checkout, slug) / "docs" / "plans"
    folders.mkdir(parents=True, exist_ok=True)
    path = folders / f"{day}-{slug}.md"
    path.write_text(text, encoding="utf-8")
    return path


def away(*, gone: bool = True) -> None:
    """Mark the owner away, or back."""
    owner.change(paths.home(os.environ), "a word", datetime.now(UTC), away=gone)
