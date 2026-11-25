"""Who added an item, on which day and in which task (`board_pages.added_line` on `main`): for an
item of the backlog folder, the commit that added its file, `not committed yet` while git has
none, and nothing when git gave no answer; for a reviewer's item, which git never holds, the
reviewer and the day of its `added`. The task is a link to its board when this board has it."""

from typing import TYPE_CHECKING

from lem.board.inputs.backlog import Added
from lem.board.inputs.names import task_href
from lem.board.inputs.parts import Link
from lem.board.views.backlog.days import day_of

if TYPE_CHECKING:
    from lem.board.views.backlog_read import AddedBy, Entry
    from lem.board.views.world import World
    from lem.records.record import Record

REVIEWER = "added by the reviewer of the night's and the retro's proposals"
NOT_COMMITTED = Added(said="not committed yet")
NO_AUTHOR = "an unnamed author"
NO_DAY = "an unknown day"


def added_of(world: World, records: tuple[Record, ...], entry: Entry) -> Added | None:
    """The line of who added the item `entry`."""
    if entry.reviewer:
        return reviewer_added(entry)
    if world.backlog is None or not world.backlog.told:
        return None
    by = entry.added
    if by is None:
        return NOT_COMMITTED
    return committed(world, records, by)


def reviewer_added(entry: Entry) -> Added:
    """The reviewer, and the day of the item's `added` when it names one."""
    day = day_of(entry.added_on)
    return Added(said=f"{REVIEWER} on {day}" if day else REVIEWER)


def committed(world: World, records: tuple[Record, ...], by: AddedBy) -> Added:
    """The author and day of the commit that added the file, and the task or the pull
    request it names."""
    said = author_said(by)
    slug = by.task
    if slug is None:
        after = f", in pull request #{by.pull}" if by.pull else None
        return Added(said=said, after=after)
    if not any(record.task.slug == slug for record in records):
        return Added(said=f"{said}, in task {slug}")
    link = Link(
        href=task_href(world.viewer.base, slug, under="backlog"), label=slug, frame=True
    )
    return Added(said=f"{said}, in task", task=link)


def author_said(by: AddedBy) -> str:
    """`added by Ann on 2026-11-24`, with words for an author or a day git did not give."""
    author = by.author or NO_AUTHOR
    day = by.day or NO_DAY
    return f"added by {author} on {day}"
