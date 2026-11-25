"""`lem task park` and `lem task resume`: only a task no agent works on is parked, its park
keeps the hold it put aside, and the resume of a dropped task opens a new one: from its breaker's
handoff, or as a new request when the release stop dropped it."""

from typing import TYPE_CHECKING

import pytest
from msgspec.structs import replace

from fakes.command import lem
from fakes.records import MOMENT, record
from fakes.repo import RealRepo, run_git
from lem.app.tasks import park, resume
from lem.kernel.errors import Refusal
from lem.model.task import resumes
from lem.records.decisions import Breaker, Taken
from lem.records.holds import BreakerHold, OwnerHold, Parked, ReleaseHold
from lem.records.journal.task import Summary
from lem.records.task import Shape
from lem.records.tickets import Ticket
from lem.records.work import Span
from lem.store import places, tasks
from unit.task.spaces import made, read, result, said, workspace

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.task import Status
    from lem.store.places import Workspace

SLUG = "gift-note"
BREAKER = Breaker(
    id=3,
    at=MOMENT,
    cause="criteria",
    what="the criteria cannot all hold",
    document="breaker-3.md",
    handoff="handoff.md",
)


@pytest.mark.parametrize("status", ["queued", "planned"])
def test_a_task_that_waits_is_parked_and_the_resume_brings_it_back(
    tmp_path: Path, status: Status
) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status=status)
    park.parked(tmp_path, SLUG, "later")
    task = read(where, SLUG).task
    assert task.status == status
    assert isinstance(task.hold, Parked)
    assert task.hold.words == "later"
    back = resume.resumed(tmp_path, SLUG)
    assert (back.resumed, back.status) == ("parked", status)
    assert read(where, SLUG).task.hold is None


def test_resume_finds_the_hold_before_the_park(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status="building", hold=BreakerHold(number=2, since=MOMENT))
    park.parked(tmp_path, SLUG, "not now")
    back = resume.resumed(tmp_path, SLUG)
    assert back.breaker == 2
    assert read(where, SLUG).task.hold == BreakerHold(number=2, since=MOMENT)


@pytest.mark.parametrize(
    ("status", "said"),
    [
        ("building", "works now"),
        ("shaping", "shapes it now"),
        ("ready", "build is done"),
        ("open", "build is done"),
        ("landed", "stays ended"),
    ],
)
def test_only_a_task_no_agent_works_on_is_parked(
    tmp_path: Path, status: Status, said: str
) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status=status)
    with pytest.raises(Refusal) as refused:
        park.parked(tmp_path, SLUG, "later")
    assert refused.value.code == "park"
    assert said in refused.value.why


def test_a_task_that_waits_for_the_owner_is_parked(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    wait = OwnerHold(on="interview", line="the interview waits", since=MOMENT)
    made(where, SLUG, status="shaping", hold=wait)
    park.parked(tmp_path, SLUG, "later")
    resume.resumed(tmp_path, SLUG)
    assert read(where, SLUG).task.hold == wait


def test_a_task_that_runs_or_ended_is_no_resume(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status="building")
    made(where, "done", status="landed")
    for slug in (SLUG, "done"):
        with pytest.raises(Refusal) as refused:
            resume.resumed(tmp_path, slug)
        assert refused.value.code == "resume"


def dropped_with_breaker(where: Workspace, **fields: object) -> None:
    """A task dropped while its breaker waited, with its handoff and its notes."""
    shape = Shape(type="fix", why="the total is wrong", track="full")
    made(where, SLUG, status="dropped", decisions=(BREAKER,), shape=shape, **fields)
    folder = places.task_folder(where.state, SLUG)
    for name in ("handoff.md", "breaker-3.md", "task.md"):
        (folder / name).write_text(f"# {name}\n", encoding="utf-8")
    (folder / "brief.md").write_text(
        f"task: {SLUG}\nbranch: fix/{SLUG}\nthe lead's brief\n", encoding="utf-8"
    )
    (folder / "landing.json").write_text("{}", encoding="utf-8")


def real(tmp_path: Path) -> Workspace:
    """A workspace over a real repository with an origin."""
    repo = RealRepo.init(tmp_path / "repo", {"README.md": b"one\n"})
    return workspace(repo.checkout)


def test_a_dropped_task_with_its_breaker_goes_on_in_a_new_task(tmp_path: Path) -> None:
    where = real(tmp_path)
    ticket = Ticket(tracker="linear", id="MBZ-12")
    talk = Span(name="plan-talk", start=MOMENT, end=MOMENT)
    open_lead = Span(name="lead", start=MOMENT)
    dropped_with_breaker(
        where, ticket=ticket, branch=f"fix/{SLUG}", spans=(talk, open_lead)
    )
    run_git(where.checkout, "branch", f"fix/{SLUG}")
    back = resume.resumed(where.checkout, SLUG)
    new = f"{SLUG}-2"
    assert (back.task, back.resumed, back.breaker, back.branch) == (
        new,
        "dropped",
        3,
        f"fix/{new}",
    )
    task = read(where, new).task
    assert (task.status, task.hold, task.resumed_from) == (
        "building",
        BreakerHold(number=3, since=task.since),
        SLUG,
    )
    assert (task.ticket, task.decisions, task.shape) == (
        ticket,
        (BREAKER,),
        read(where, SLUG).task.shape,
    )
    folder = places.task_folder(where.state, new)
    assert sorted(path.name for path in folder.iterdir() if path.suffix == ".md") == [
        "breaker-3.md",
        "brief.md",
        "handoff.md",
        "task.md",
    ]
    assert not (folder / "landing.json").exists()
    brief = (folder / "brief.md").read_text(encoding="utf-8")
    assert f"task: {new}\nbranch: fix/{new}\n" in brief
    assert f"resumed from: {SLUG}; read handoff.md and breaker-3.md first" in brief
    assert (where.lem / "worktrees" / new / "README.md").is_file()
    assert read(where, SLUG).task.status == "dropped"
    assert read(where, new).release == read(where, SLUG).release
    assert task.spans == (talk,)
    with pytest.raises(Refusal) as again:
        resume.resumed(where.checkout, SLUG)
    assert again.value.code == "resumed"


def test_the_first_task_of_the_line_with_the_next_free_number(tmp_path: Path) -> None:
    where = real(tmp_path)
    dropped_with_breaker(where)
    made(where, f"{SLUG}-2", status="landed")
    assert resume.resumed(where.checkout, SLUG).task == f"{SLUG}-3"


def test_a_task_the_release_stop_dropped_goes_on_as_a_new_request(
    tmp_path: Path,
) -> None:
    where = real(tmp_path)
    stop = ReleaseHold(began="0.1.0", running="0.3.1", say="x", since=MOMENT)
    dropped_with_breaker(where, hold=stop, branch=f"fix/{SLUG}")
    run_git(where.checkout, "branch", f"fix/{SLUG}")
    back = resume.resumed(where.checkout, SLUG)
    task = read(where, back.task).task
    assert (back.resumed, task.status, task.shape, task.decisions) == (
        "request",
        "shaping",
        None,
        (),
    )
    assert task.branch == f"fix/{back.task}"
    folder = places.task_folder(where.state, back.task)
    assert (folder / "handoff.md").is_file()
    assert not (folder / "brief.md").exists()
    ran = lem("task", "resume", "other", cwd=where.checkout)
    assert ran.code == 1


def test_a_stop_that_named_no_branch_starts_the_request_from_the_base(
    tmp_path: Path,
) -> None:
    where = real(tmp_path)
    stop = ReleaseHold(began="0.1.0", running="0.3.1", say="x", since=MOMENT)
    dropped_with_breaker(where, hold=stop, branch="fix/gone")
    back = resume.resumed(where.checkout, SLUG)
    assert back.branch is None
    assert "the base branch" in back.says


def test_a_dropped_task_with_no_breaker_that_waits_is_refused_with_its_ask(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    helped = Taken(id=4, at=MOMENT, what="w", chose="c", why="y", by="owner", breaker=3)
    dropped_with_breaker(where)
    tasks.update(
        where.state,
        SLUG,
        lambda one: replace(one, task=replace(one.task, decisions=(BREAKER, helped))),
        1,
    )
    with pytest.raises(Refusal) as refused:
        resume.resumed(tmp_path, SLUG)
    assert "no breaker that waits" in refused.value.why
    assert refused.value.fix == "new work for it is a new ask: /lem fix the login"


def test_a_dropped_task_whose_journal_became_a_summary_is_refused_with_its_ask(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    summary = Summary(
        at=MOMENT, statuses=("dropped",), first=MOMENT, last=MOMENT, entries=3
    )
    dropped_with_breaker(where)
    tasks.update(where.state, SLUG, lambda one: replace(one, journal=(summary,)), 1)
    with pytest.raises(Refusal) as refused:
        resume.resumed(tmp_path, SLUG)
    assert "summary" in refused.value.why
    assert not (where.state / "tasks" / f"{SLUG}-2").exists()


def test_a_resume_whose_brief_is_not_utf8_makes_nothing(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    dropped_with_breaker(where)
    brief = places.task_folder(where.state, SLUG) / "brief.md"
    brief.write_bytes(b"task: \xff\n")
    with pytest.raises(Refusal) as refused:
        resume.resumed(tmp_path, SLUG)
    assert refused.value.code == "unreadable"
    assert not (where.state / "tasks" / f"{SLUG}-2").exists()


def test_the_command_parks_and_resumes(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status="queued")
    parked = lem("task", "park", SLUG, "--why", "after the release", cwd=tmp_path)
    assert result(parked)["resumed"] == "parked"
    again = lem("task", "resume", SLUG, cwd=tmp_path)
    assert said(again).endswith("from where it was put aside")
    assert read(where, SLUG).task.hold is None


def test_a_parked_task_two_releases_back_stops_and_a_dropped_one_passes(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status="planned", hold=Parked(since=MOMENT))
    tasks.update(where.state, SLUG, lambda one: replace(one, release="0.1.0"), 1)
    with pytest.raises(Refusal) as refused:
        resume.resumed(tmp_path, SLUG)
    assert refused.value.code == "release"
    made(where, "old", status="dropped", ticket=Ticket(tracker="linear", id="MBZ-1"))
    tasks.update(where.state, "old", lambda one: replace(one, release="0.1.0"), 1)
    record = read(where, "old")
    assert record.task.hold is None
    assert isinstance(
        resume.release.checked(where.state, "old", ends=True).task.hold, ReleaseHold
    )


def test_a_line_of_resumes_that_goes_round_is_refused() -> None:
    first = record("first", status="dropped", resumed_from="second")
    second = record("second", status="dropped", resumed_from="first")
    with pytest.raises(Refusal) as refused:
        resumes.next_slug("second", (first, second))
    assert refused.value.code == "resume-line"
