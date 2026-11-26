"""A task's ticket after its open: the steps written once, what its end still owes, who holds it
after a resume, `lem task ticket` after the end, and `lem task list` and `lem task show`."""

from typing import TYPE_CHECKING

import pytest
from msgspec.structs import replace

from fakes.command import lem
from fakes.records import MOMENT, record
from lem.app.tasks import listing, ticket
from lem.kernel.errors import Refusal
from lem.model.task import claim, tickets
from lem.records.holds import BreakerHold
from lem.records.tickets import Ticket, TicketStep
from unit.task.spaces import made, read, refusal, result, rows, workspace

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.task import Status
    from lem.records.tickets import TicketAct

SLUG = "gift-note"
ISSUE = Ticket(tracker="github", id="#42", repo="owner/project")


def taken(*acts: TicketAct, login: str = "silver") -> Ticket:
    """The issue with `acts` written down."""
    steps = tuple(
        TicketStep(act=act, at=MOMENT, login=login if act == "assigned" else None)
        for act in acts
    )
    return replace(ISSUE, steps=steps)


@pytest.mark.parametrize(
    ("status", "acts", "owed"),
    [
        ("building", (), ()),
        ("open", ("started",), ()),
        ("landed", (), ("commented", "landed")),
        ("landed", ("commented",), ("landed",)),
        ("dropped", (), ("dropped",)),
        ("dropped", ("started", "assigned"), ("dropped", "unassigned")),
        ("answered", ("assigned", "answered"), ("unassigned",)),
        ("answered", ("answered",), ()),
    ],
)
def test_what_the_end_owes_its_ticket(
    status: Status, acts: tuple[TicketAct, ...], owed: tuple[str, ...]
) -> None:
    task = record(SLUG, status=status, ticket=taken(*acts)).task
    assert tickets.owed(task, None) == owed


def test_no_ticket_owes_nothing_and_neither_does_a_task_another_holds_now() -> None:
    assert tickets.owed(record(SLUG, status="dropped").task, None) == ()
    task = record(SLUG, status="dropped", ticket=ISSUE).task
    assert tickets.owed(task, "gift-note-2") == ()


def test_the_holder_is_the_task_a_resume_went_on_in_with_the_same_ticket() -> None:
    old = record(SLUG, status="dropped", ticket=ISSUE)
    new = record(f"{SLUG}-2", status="building", ticket=ISSUE, resumed_from=SLUG)
    other = record("other", status="building", resumed_from=SLUG)
    assert claim.holder(old.task, (old, new)) == f"{SLUG}-2"
    assert claim.holder(old.task, (old, other)) is None


def test_a_step_is_written_once_with_the_login_of_the_assignee(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status="building", ticket=ISSUE)
    shown = ticket.recorded(where.state, SLUG, "assigned", "silver")
    assert (shown.steps, shown.assignee) == (("assigned",), "silver")
    with pytest.raises(Refusal) as again:
        ticket.recorded(where.state, SLUG, "assigned", "silver")
    assert again.value.code == "ticket-step"


@pytest.mark.parametrize(
    ("act", "login"),
    [
        ("assigned", None),
        ("started", "silver"),
        ("unassigned", None),
        ("assigned", "-x"),
    ],
)
def test_a_step_out_of_its_form_is_refused(
    tmp_path: Path, act: TicketAct, login: str | None
) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status="building", ticket=ISSUE)
    with pytest.raises(Refusal):
        ticket.recorded(where.state, SLUG, act, login)


def test_a_task_of_no_ticket_has_no_step(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status="building")
    with pytest.raises(Refusal) as refused:
        ticket.recorded(where.state, SLUG, "started", None)
    assert refused.value.code == "no-ticket"


def test_a_step_is_taken_after_the_end_and_pays_what_it_owes(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status="dropped", ticket=taken("assigned"))
    ran = lem("task", "ticket", SLUG, "dropped", cwd=tmp_path)
    assert result(ran)["owed"] == ["unassigned"]
    paid = lem("task", "ticket", SLUG, "unassigned", cwd=tmp_path)
    assert result(paid).get("owed", []) == []
    assert claim.released(read(where, SLUG).task, ())


def test_the_list_shows_open_tasks_and_the_ended_ones_with_ended(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    made(where, "open-one", status="building", hold=BreakerHold(number=1, since=MOMENT))
    made(where, "ended", status="landed", ticket=ISSUE)
    listed = listing.listed(tmp_path, ended=False)
    assert [(one.slug, one.hold, one.hold_line) for one in listed] == [
        ("open-one", "BreakerHold", "breaker 1 waits for the owner")
    ]
    ran = lem("task", "list", "--ended", cwd=tmp_path)
    found = {one["slug"]: one for one in rows(ran)}
    assert found["ended"]["ticket"]["owed"] == ["commented", "landed"]


def test_a_damaged_successor_leaves_the_ticket_owed_nothing_and_names_it(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    linear = Ticket(tracker="linear", id="LEM-44")
    made(where, "old", status="dropped", ticket=linear)
    made(where, "current", status="building", ticket=linear, resumed_from="old")
    before = result(lem("task", "show", "old", cwd=tmp_path))["ticket"]
    assert (before["held_by"], before.get("owed", [])) == ("current", [])
    damaged = where.state / "tasks/current/task.json"
    damaged.write_text("{")

    shown = lem("task", "show", "old", cwd=tmp_path)
    listed = lem("task", "list", "--ended", cwd=tmp_path)
    stepped = lem("task", "ticket", "old", "started", cwd=tmp_path)

    for ran, found in (
        (shown, result(shown)["ticket"]),
        (listed, rows(listed)[0]["ticket"]),
        (stepped, result(stepped)),
    ):
        assert ran.code == 0, ran
        assert found.get("owed", []) == [], found
        assert found["holder_unknown"] == [str(damaged)], found
        assert str(damaged) in ran.stderr
    assert result(lem("task", "show", "old", cwd=tmp_path)).get("held_by") is None


def test_show_reads_one_task_and_writes_nothing(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    made(
        where, SLUG, status="queued", after=("other",), order="after other", night=None
    )
    shown = result(lem("task", "show", SLUG, cwd=tmp_path))
    assert (shown["status"], shown["after"], shown["order"], shown["mode"]) == (
        "queued",
        ["other"],
        "after other",
        "with-owner",
    )
    assert read(where, SLUG).revision == 1
    assert lem("task", "show", "nothing", cwd=tmp_path).code == 1


def test_dir_gives_the_tasks_folder(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    made(where, SLUG)
    ran = lem("task", "dir", SLUG, cwd=tmp_path)
    assert result(ran)["folder"] == str(where.state / "tasks" / SLUG)
    assert refusal(lem("task", "dir", "nothing", cwd=tmp_path))["code"] == ("no-task")
