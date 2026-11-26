"""`lem task read`, `lem task may-start` and `lem task start`: the read's shape, its queue behind
another task, his order in his words and its wait, and his "start SLUG now"."""

from typing import TYPE_CHECKING

import pytest
from msgspec.structs import replace

from fakes.command import lem
from fakes.records import MOMENT
from lem.app.tasks import shape, start
from lem.kernel.errors import Refusal
from lem.model.task.read import ORDER_WAIT, Queue
from lem.records.holds import OwnerHold, Parked
from lem.records.task import Shape
from lem.store import tasks
from unit.task.spaces import last_line, made, read, refusal, result, said, workspace

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from lem.model.task.read import Wait
    from lem.records.record import Record
    from lem.records.task import Status
    from lem.store.places import Workspace

SLUG = "gift-note"
SHAPE = Shape(type="feat", why="a new note", track="full", then="interview")


def shaped(where: Workspace, queue: Queue | None = None, slug: str = SLUG) -> None:
    """The read of `slug` with SHAPE and `queue`."""
    shape.shaped(where.checkout, slug, SHAPE, queue or Queue())


def code(call: Callable[[], object]) -> str:
    """The code of the refusal `call` raises."""
    with pytest.raises(Refusal) as refused:
        call()
    return refused.value.code


def test_the_read_keeps_the_type_the_track_and_what_comes_next(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status="shaping")
    ran = lem(
        "task", "read", SLUG, "--type", "fix", "--why", "the total is wrong",
        "--track", "small", "--careful", "money", "--then", "fast", cwd=tmp_path,
    )  # fmt: skip
    assert result(ran)["type"] == "fix"
    found = read(where, SLUG).task.shape
    assert found == Shape(
        type="fix", why="the total is wrong", track="small", careful=("money",),
        then="fast", first_line=said(ran),
    )  # fmt: skip


def test_a_misspelled_type_is_a_wrong_call_that_names_the_types(tmp_path: Path) -> None:
    workspace(tmp_path)
    ran = lem(
        "task", "read", SLUG, "--type", "feet", "--why", "w", "--track", "full",
        cwd=tmp_path,
    )  # fmt: skip
    assert ran.code == 2
    assert "feat" in ran.stderr


def test_after_queues_the_task_and_his_order_is_kept_in_his_words(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    made(where, "first", status="building")
    made(where, SLUG, status="shaping")
    shaped(where, Queue(after=("first",), order="after the footer"))
    task = read(where, SLUG).task
    assert (task.status, task.after, task.order) == (
        "queued",
        ("first",),
        "after the footer",
    )


def test_an_order_that_names_no_task_waits_for_his_answer(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status="shaping")
    shaped(where, Queue(order="after the other one"))
    hold = read(where, SLUG).task.hold
    assert isinstance(hold, OwnerHold)
    assert (hold.on, hold.line) == ("order", ORDER_WAIT)
    shaped(where)
    assert read(where, SLUG).task.hold is None


@pytest.mark.parametrize("wait", ["interview", "criteria"])
def test_a_wait_is_the_owners_hold(tmp_path: Path, wait: Wait) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status="shaping")
    shaped(where, Queue(wait=wait))
    hold = read(where, SLUG).task.hold
    assert isinstance(hold, OwnerHold)
    assert hold.on == wait


def test_the_read_command_records_a_request_hold(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status="shaping")
    ran = lem(
        "task",
        "read",
        SLUG,
        "--type",
        "fix",
        "--why",
        "the total is wrong",
        "--track",
        "small",
        "--wait",
        "request",
        cwd=tmp_path,
    )
    assert ran.code == 0, ran.stdout + ran.stderr
    hold = read(where, SLUG).task.hold
    assert isinstance(hold, OwnerHold)
    assert (hold.on, hold.line) == ("request", "the request waits for the owner")


def test_after_names_another_task_of_the_workspace(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status="shaping")
    assert code(lambda: shaped(where, Queue(after=("nothing",)))) == "after"
    assert code(lambda: shaped(where, Queue(after=(SLUG,)))) == "after"


def test_the_read_stops_at_the_first_unknown_dependency(tmp_path: Path) -> None:
    class UnreadName(str):
        __slots__ = ()

        def __hash__(self) -> int:
            raise AssertionError(
                "the first unknown dependency already decides the refusal"
            )

    where = workspace(tmp_path)
    made(where, SLUG, status="shaping")
    with pytest.raises(Refusal, match="first-missing is no other task"):
        shaped(where, Queue(after=("first-missing", UnreadName("also-missing"))))


@pytest.mark.parametrize(
    ("status", "order", "new_order", "refused"),
    [
        ("building", "after both", None, "order"),
        ("dropped", "after both", "after first", "order"),
        ("dropped", None, None, "after-dropped"),
    ],
)
def test_a_second_read_cannot_remove_a_dependency_that_needs_the_owners_word(
    tmp_path: Path,
    status: Status,
    order: str | None,
    new_order: str | None,
    refused: str,
) -> None:
    where = workspace(tmp_path)
    made(where, "first", status="landed")
    made(where, "second", status=status)
    made(where, SLUG, status="shaping")
    shaped(where, Queue(after=("first", "second"), order=order))
    prior = read(where, SLUG)
    assert (
        code(lambda: shaped(where, Queue(after=("first",), order=new_order))) == refused
    )
    assert read(where, SLUG) == prior
    assert start.start(tmp_path, SLUG, "start gift-note now").status == "shaping"


def test_a_second_read_keeps_the_owners_order_when_it_keeps_its_dependencies(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    made(where, "first", status="building")
    made(where, SLUG, status="shaping")
    shaped(where, Queue(after=("first",), order="after first"))
    shaped(where, Queue(after=("first",)))
    assert read(where, SLUG).task.order == "after first"
    assert code(lambda: shaped(where)) == "order"


def test_a_need_that_went_is_read_again_and_his_order_is_lifted_by_his_word_only(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    made(where, "first", status="building")
    made(where, SLUG, status="queued", after=("first",))
    shaped(where)
    assert read(where, SLUG).task.status == "shaping"
    made(where, "other", status="queued", after=("first",), order="after first")
    assert code(lambda: shaped(where, slug="other")) == "order"


@pytest.mark.parametrize("status", ["building", "planned", "ready", "open"])
def test_the_read_is_written_while_the_task_is_shaping_or_queued(
    tmp_path: Path, status: Status
) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status=status)
    assert code(lambda: shaped(where)) == "status"


@pytest.mark.parametrize(
    ("other", "refusal"),
    [("building", "queued"), ("open", "queued"), ("dropped", "after-dropped")],
)
def test_a_task_queued_behind_another_waits_for_its_end_or_his_word(
    tmp_path: Path, other: Status, refusal: str
) -> None:
    where = workspace(tmp_path)
    made(where, "first", status=other)
    made(where, SLUG, status="queued", after=("first",), order="after first")
    with pytest.raises(Refusal) as refused:
        start.may(tmp_path, SLUG)
    assert refused.value.code == refusal
    assert f'lem task start {SLUG} --words "HIS WORDS"' in refused.value.fix


def test_a_need_names_the_read_again_and_no_order(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    made(where, "first", status="building")
    made(where, SLUG, status="queued", after=("first",))
    with pytest.raises(Refusal) as refused:
        start.may(tmp_path, SLUG)
    assert "with no --after" in refused.value.fix


@pytest.mark.parametrize("other", ["landed", "answered"])
def test_a_task_behind_one_that_landed_may_start_and_names_the_running_ones(
    tmp_path: Path, other: Status
) -> None:
    where = workspace(tmp_path)
    made(where, "first", status=other)
    made(where, "busy", status="building")
    made(where, SLUG, status="queued", after=("first",))
    assert start.may(tmp_path, SLUG).running == ("busy",)


def moved_to(where: Workspace, slug: str, status: Status) -> None:
    """The task `slug` in `status` now, as a move of its record."""

    def change(record: Record) -> Record:
        return replace(record, task=replace(record.task, status=status))

    tasks.update(where.state, slug, change, read(where, slug).revision)


@pytest.mark.parametrize(
    ("first", "second", "refusal"),
    [
        ("landed", "building", "queued"),
        ("open", "building", "queued"),
        ("open", "dropped", "after-dropped"),
        ("answered", "landed", None),
    ],
)
def test_a_task_queued_behind_two_waits_for_each_and_a_dropped_one_for_his_word(
    tmp_path: Path, first: Status, second: Status, refusal: str | None
) -> None:
    where = workspace(tmp_path)
    made(where, "first", status=first)
    made(where, "second", status=second)
    made(where, SLUG, status="queued", after=("first", "second"))
    if refusal is None:
        assert start.may(tmp_path, SLUG).slug == SLUG
        return
    assert code(lambda: start.may(tmp_path, SLUG)) == refusal


def test_the_refusal_of_a_task_behind_two_names_each_that_it_waits_for(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    made(where, "first", status="landed")
    made(where, "second", status="building")
    made(where, SLUG, status="queued", after=("first", "second"))
    with pytest.raises(Refusal) as one:
        start.may(tmp_path, SLUG)
    assert one.value.why == (
        f"{SLUG} is queued after second, which is building: it starts when second is "
        "landed or answered"
    )
    moved_to(where, "first", "open")
    with pytest.raises(Refusal) as both:
        start.may(tmp_path, SLUG)
    assert both.value.why == (
        f"{SLUG} is queued after first, which is open, and second, which is building: "
        "it starts when each of first and second is landed or answered"
    )
    assert "the result of first and second" in both.value.fix


def test_after_given_twice_queues_the_read_behind_both(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    made(where, "first", status="building")
    made(where, "second", status="shaping")
    made(where, SLUG, status="shaping")
    ran = lem(
        "task",
        "read",
        SLUG,
        "--type",
        "feat",
        "--why",
        "a note",
        "--track",
        "full",
        "--after",
        "first",
        "--after",
        "second",
        cwd=tmp_path,
    )
    assert ran.code == 0, ran.stdout + ran.stderr
    task = read(where, SLUG).task
    assert (task.status, task.after) == ("queued", ("first", "second"))
    assert last_line(where, SLUG) == "queued after first and second"
    assert code(lambda: shaped(where, Queue(after=("first", "nothing")))) == "after"


@pytest.mark.parametrize(
    ("fields", "refusal"),
    [
        ({"status": "landed"}, "ended"),
        ({"status": "open"}, "landing"),
        ({"status": "planned", "hold": Parked(since=MOMENT)}, "parked"),
    ],
)
def test_a_stale_wake_up_starts_no_lead(
    tmp_path: Path, fields: dict[str, object], refusal: str
) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, **fields)
    assert code(lambda: start.may(tmp_path, SLUG)) == refusal


def test_his_word_starts_a_queued_task_and_keeps_his_words(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    made(where, "first", status="dropped")
    made(
        where, SLUG, status="queued", after=("first",), order="after first", shape=SHAPE
    )
    moved = start.start(tmp_path, SLUG, "start gift-note now")
    record = read(where, SLUG)
    assert (moved.status, record.task.after, record.task.order) == (
        "shaping",
        (),
        None,
    )
    assert last_line(where, SLUG) == 'the owner\'s word: "start gift-note now"'
    made(where, "fast", status="queued", shape=replace(SHAPE, then="fast"))
    assert start.start(tmp_path, "fast", "go").status == "building"
    assert code(lambda: start.start(tmp_path, SLUG, "again")) == "start"


def test_the_read_says_the_first_line_and_show_gives_its_named_form(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status="shaping")
    ran = lem(
        "task", "read", SLUG, "--type", "fix", "--why", "the total is wrong",
        "--track", "small", "--then", "fast", cwd=tmp_path,
    )  # fmt: skip
    line = said(ran)
    assert line.startswith('fix: "fix the login".')
    shape = read(where, SLUG).task.shape
    assert shape is not None and shape.first_line == line
    shown = result(lem("task", "show", SLUG, cwd=tmp_path))
    assert shown["first_line"].startswith(f'{SLUG} · fix: "fix the login".')
    made(where, "night", status="shaping", night=MOMENT.date())
    lem(
        "task", "read", "night", "--type", "fix", "--why", "w", "--track", "small",
        "--then", "fast", cwd=tmp_path,
    )  # fmt: skip
    assert "first_line" not in result(lem("task", "show", "night", cwd=tmp_path))


def test_a_stale_read_or_word_over_a_parked_task_keeps_the_park(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    made(where, "first", status="building")
    made(where, SLUG, status="queued", after=("first",), hold=Parked(since=MOMENT))
    assert code(lambda: shaped(where)) == "parked"
    assert code(lambda: start.start(tmp_path, SLUG, "start it")) == "parked"
    task = read(where, SLUG).task
    assert (task.status, isinstance(task.hold, Parked)) == ("queued", True)


def test_a_move_does_not_go_around_a_queue(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    made(where, "first", status="building")
    made(where, SLUG, status="queued", after=("first",))
    for status in ("building", "shaping"):
        ran = lem("task", "move", SLUG, status, cwd=tmp_path)
        assert refusal(ran)["code"] == "queued"
    made(where, "landed", status="landed")
    made(where, "next", status="queued", after=("landed",))
    assert result(lem("task", "move", "next", "building", cwd=tmp_path))["status"] == (
        "building"
    )
