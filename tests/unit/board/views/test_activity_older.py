"""The page of the older ended tasks (`board_pages.older_page` and `board_model.done_older` on
`main`): the ended tasks Done has no card for, the newest first, each with how and when it ended,
its board and its pull request."""

from datetime import timedelta
from typing import TYPE_CHECKING

import msgspec

from lem.board.views import older
from lem.records.landing.record import Landing, Pull
from unit.board.views.timed import at, named, seen, task, world

if TYPE_CHECKING:
    from lem.records.record import Record

ENDED = ("landed", "dropped", "answered")
PULL = Pull(number=41, url="https://github.com/acme/shop/pull/41", title="Fix it")


def ended(count: int) -> list[Record]:
    """`count` ended tasks, `task-00` the first to end, a minute apart, in turn landed, dropped
    and answered; `task-02` has a pull request."""
    made = []
    for number in range(count):
        when = at("09:00") + timedelta(minutes=number)
        record = named(f"task-{number:02d}", task(status=ENDED[number % 3], since=when))
        if number == 2:
            record = msgspec.structs.replace(record, landing=Landing(pull=PULL))
        made.append(record)
    return made


def test_done_keeps_every_ended_task_and_the_ones_after_its_newest_20_are_the_older() -> (
    None
):
    """The older page's part of `main`'s Workspace.test_done_keeps_every_ended_task_and_the_
    ones_after_its_newest_20_are_the_older: of 25 ended tasks the five that ended first are the
    older ones, the newest first; with 20, none is."""
    builds = named("builds", task(status="building", since=at("09:30")))
    page = older.older(world(*map(seen, ended(25)), seen(builds)))
    assert [row.slug for row in page.rows] == [
        "task-04",
        "task-03",
        "task-02",
        "task-01",
        "task-00",
    ]
    assert page.newer.label == "the 20 newer ones are in Done"
    assert page.empty is None
    none = older.older(world(*map(seen, ended(20))))
    assert (none.rows, none.empty) == (
        (),
        "Done shows every ended task: none is older than its 20 newest",
    )


def test_each_row_says_how_and_when_it_ended_and_opens_its_board_over_the_list() -> (
    None
):
    page = older.older(world(*map(seen, ended(25))))
    rows = {row.slug: row for row in page.rows}
    assert [(row.slug, row.label) for row in page.rows] == [
        ("task-04", "Dropped"),
        ("task-03", "Landed"),
        ("task-02", "Answered"),
        ("task-01", "Dropped"),
        ("task-00", "Landed"),
    ]
    first = rows["task-04"]
    assert (first.title, first.href, first.ended.shown, first.ended.title) == (
        "Task 04",
        "/h/w/tasks/task-04?in=done",
        "09:04",
        "ended 09:04",
    )
    assert rows["task-03"].pull is None
    pull = rows["task-02"].pull
    assert pull is not None
    assert pull.link is not None
    assert (pull.label, pull.link.href) == ("#41", PULL.url)
