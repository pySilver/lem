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
from unit.task.spaces import last_line, made, read, result, said, workspace

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from lem.model.task.read import Wait
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
        then="fast",
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
    shaped(where, Queue(after="first", order="after the footer"))
    task = read(where, SLUG).task
    assert (task.status, task.after, task.order) == (
        "queued",
        "first",
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


def test_after_names_another_task_of_the_workspace(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status="shaping")
    assert code(lambda: shaped(where, Queue(after="nothing"))) == "after"
    assert code(lambda: shaped(where, Queue(after=SLUG))) == "after"


def test_a_need_that_went_is_read_again_and_his_order_is_lifted_by_his_word_only(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    made(where, "first", status="building")
    made(where, SLUG, status="queued", after="first")
    shaped(where)
    assert read(where, SLUG).task.status == "shaping"
    made(where, "other", status="queued", after="first", order="after first")
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
    made(where, SLUG, status="queued", after="first", order="after first")
    with pytest.raises(Refusal) as refused:
        start.may(tmp_path, SLUG)
    assert refused.value.code == refusal
    assert f'lem task start {SLUG} --words "HIS WORDS"' in refused.value.fix


def test_a_need_names_the_read_again_and_no_order(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    made(where, "first", status="building")
    made(where, SLUG, status="queued", after="first")
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
    made(where, SLUG, status="queued", after="first")
    assert start.may(tmp_path, SLUG).running == ("busy",)


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
    made(where, SLUG, status="queued", after="first", order="after first", shape=SHAPE)
    moved = start.start(tmp_path, SLUG, "start gift-note now")
    record = read(where, SLUG)
    assert (moved.status, record.task.after, record.task.order) == (
        "shaping",
        None,
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
    shown = result(lem("task", "show", SLUG, cwd=tmp_path))
    assert shown["first_line"].startswith(f'{SLUG} · fix: "fix the login".')
    made(where, "night", status="shaping", night=MOMENT.date())
    lem(
        "task", "read", "night", "--type", "fix", "--why", "w", "--track", "small",
        "--then", "fast", cwd=tmp_path,
    )  # fmt: skip
    assert "first_line" not in result(lem("task", "show", "night", cwd=tmp_path))
