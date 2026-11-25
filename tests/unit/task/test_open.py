"""`lem task open`: the first record, the owner's words written once, the ticket in its one form
and its claim, the backlog item's claim, the night, the queue, and the dropped task a new one goes
on from."""

import threading
from typing import TYPE_CHECKING

import msgspec
import pytest

from fakes.command import lem
from fakes.records import MOMENT
from fakes.repo import RealRepo
from lem.app.tasks import open as opening
from lem.app.tasks.opening import Asked
from lem.kernel.errors import Refusal
from lem.records.tickets import Ticket, TicketStep
from unit.task.spaces import SETTINGS, made, read, refusal, result, workspace

if TYPE_CHECKING:
    from pathlib import Path

    from lem.store.places import Workspace

GITHUB = f'{SETTINGS}[tracker]\nkind = "github"\n'
LINEAR = f'{SETTINGS}[tracker]\nkind = "linear"\n'


def opened(where: Workspace, slug: str = "gift-note", **words: str | bool) -> str:
    """Open `slug` with `words` over the owner's plain ask; its status."""
    asked = msgspec.convert({"slug": slug, "ask": "add a gift note", **words}, Asked)
    return opening.opened(where.checkout, asked).status


def test_a_task_opens_shaping_with_his_words_and_its_release(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    assert opened(where) == "shaping"
    task = read(where, "gift-note").task
    assert (task.ask, task.status, task.mode) == (
        "add a gift note",
        "shaping",
        "with-owner",
    )


def test_the_same_words_again_are_a_retry_and_other_words_are_refused(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    opened(where)
    retry = opening.opened(
        where.checkout, Asked(slug="gift-note", ask="add  a gift note")
    )
    assert (retry.made, retry.status) == (False, "shaping")
    with pytest.raises(Refusal) as refused:
        opening.opened(where.checkout, Asked(slug="gift-note", ask="drop the footer"))
    assert refused.value.code == "task-exists"


def test_an_ended_task_keeps_its_slug(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    made(where, "gift-note", ask="add a gift note", status="landed")
    with pytest.raises(Refusal) as refused:
        opened(where)
    assert refused.value.code == "task-ended"


def test_empty_words_are_refused(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    with pytest.raises(Refusal) as refused:
        opening.opened(where.checkout, Asked(slug="gift-note", ask="  "))
    assert refused.value.code == "ask"


def test_a_project_with_no_tracker_takes_no_ticket_and_says_how_to_add_one(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    with pytest.raises(Refusal) as refused:
        opened(where, ticket="MBZ-12")
    assert refused.value.code == "no-tracker"
    assert "[tracker]" in refused.value.fix or "[tracker]" in refused.value.why


@pytest.mark.parametrize("given", ["42", "#42", "#042"])
def test_an_issue_is_its_number_after_a_hash_in_one_saved_form(
    tmp_path: Path, given: str
) -> None:
    where = workspace(tmp_path, GITHUB)
    opened(where, ticket=given, ticket_repo="owner/project")
    ticket = read(where, "gift-note").task.ticket
    assert ticket == Ticket(tracker="github", id="#42", repo="owner/project")


@pytest.mark.parametrize("given", ["MBZ-12", "0", "#0", "forty"])
def test_github_refuses_a_linear_id_and_no_number(tmp_path: Path, given: str) -> None:
    where = workspace(tmp_path, GITHUB)
    with pytest.raises(Refusal) as refused:
        opened(where, ticket=given, ticket_repo="owner/project")
    assert refused.value.code == "ticket"


def test_an_issue_keeps_its_repository_and_another_tracker_takes_none(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path, GITHUB)
    with pytest.raises(Refusal) as missing:
        opened(where, ticket="42")
    with pytest.raises(Refusal) as alone:
        opened(where, ticket_repo="owner/project")
    linear = workspace(tmp_path / "linear", LINEAR)
    with pytest.raises(Refusal) as other:
        opened(linear, ticket="MBZ-12", ticket_repo="owner/project")
    assert {missing.value.code, alone.value.code, other.value.code} == {"ticket-repo"}


def test_linear_refuses_a_number_and_keeps_its_own_form(tmp_path: Path) -> None:
    where = workspace(tmp_path, LINEAR)
    opened(where, ticket="mbz-12")
    assert read(where, "gift-note").task.ticket == Ticket(tracker="linear", id="MBZ-12")
    with pytest.raises(Refusal):
        opened(where, "other", ticket="42")


def test_a_landed_task_keeps_its_ticket_and_the_refusal_names_it(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path, LINEAR)
    ticket = Ticket(tracker="linear", id="MBZ-12")
    made(where, "first", status="landed", ticket=ticket)
    with pytest.raises(Refusal) as refused:
        opened(where, ticket="MBZ-12")
    assert refused.value.code == "ticket-landed"
    assert "first" in refused.value.why


def test_an_ended_task_that_still_owes_holds_the_ticket_and_the_refusal_names_the_step(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path, GITHUB)
    ticket = Ticket(tracker="github", id="#42", repo="owner/project")
    made(where, "first", status="dropped", ticket=ticket)
    with pytest.raises(Refusal) as refused:
        opened(where, ticket="42", ticket_repo="owner/project")
    assert refused.value.code == "ticket-owed"
    assert "lem issue drop first" in refused.value.fix


def test_a_ticket_given_back_goes_to_the_new_task(tmp_path: Path) -> None:
    where = workspace(tmp_path, LINEAR)
    step = TicketStep(act="dropped", at=MOMENT)
    ticket = Ticket(tracker="linear", id="MBZ-12", steps=(step,))
    made(where, "first", status="dropped", ticket=ticket)
    assert opened(where, ticket="MBZ-12") == "shaping"


def test_an_open_task_holds_its_ticket(tmp_path: Path) -> None:
    where = workspace(tmp_path, LINEAR)
    made(
        where, "first", status="building", ticket=Ticket(tracker="linear", id="MBZ-12")
    )
    with pytest.raises(Refusal) as refused:
        opened(where, ticket="MBZ-12")
    assert refused.value.code == "ticket-held"


def test_a_backlog_item_is_claimed_by_an_open_task_and_a_gone_one_is_refused(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    (tmp_path / "docs" / "backlog").mkdir(parents=True)
    (tmp_path / "docs" / "backlog" / "a.md").write_text("# A\n", encoding="utf-8")
    opened(where, backlog_item="docs/backlog/a.md")
    with pytest.raises(Refusal) as held:
        opened(where, "other", backlog_item="docs/backlog/a.md")
    with pytest.raises(Refusal) as gone:
        opened(where, "third", backlog_item="docs/backlog/b.md")
    assert (held.value.code, gone.value.code) == ("item-held", "item-gone")


def test_a_night_task_runs_alone_from_its_opening(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    opened(where, night="2026-11-25")
    task = read(where, "gift-note").task
    assert (task.mode, str(task.night)) == ("alone", "2026-11-25")
    with pytest.raises(Refusal) as refused:
        opened(where, "other", night="25.11.2026")
    assert refused.value.code == "night"


def test_after_queues_the_task_and_plan_only_is_kept(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    assert opened(where, after="first", plan_only=True) == "queued"
    task = read(where, "gift-note").task
    assert (task.after, task.plan_only) == ("first", True)


def test_a_resumed_task_takes_the_ticket_of_the_task_it_goes_on_from_and_no_other(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path, LINEAR)
    ticket = Ticket(tracker="linear", id="MBZ-12")
    made(where, "first", status="dropped", ticket=ticket)
    opened(where, "first-2", origin="first")
    assert read(where, "first-2").task.ticket == ticket
    with pytest.raises(Refusal) as again:
        opened(where, "first-3", origin="first")
    with pytest.raises(Refusal) as open_one:
        opened(where, "other", origin="first-2")
    assert (again.value.code, open_one.value.code) == ("resumed", "from")


def test_outside_a_repository_the_open_is_refused_and_nothing_is_made(
    tmp_path: Path,
) -> None:
    ran = lem("task", "open", "gift-note", "--ask", "add a gift note", cwd=tmp_path)
    assert ran.code == 1
    assert refusal(ran)["code"] == "no-repository"
    assert list(tmp_path.iterdir()) == []


def test_from_a_tasks_worktree_the_state_is_the_main_checkouts(tmp_path: Path) -> None:
    where = workspace(tmp_path / "main")
    git = where.checkout / ".git" / "worktrees" / "gift-note"
    git.mkdir(parents=True)
    (git / "commondir").write_text("../..\n", encoding="utf-8")
    worktree = where.lem / "worktrees" / "gift-note"
    worktree.mkdir(parents=True)
    (worktree / ".git").write_text(f"gitdir: {git}\n", encoding="utf-8")
    ran = lem("task", "open", "other", "--ask", "add a gift note", cwd=worktree)
    assert result(ran)["folder"] == str(where.state / "tasks" / "other")


def test_his_words_with_a_line_separator_read_back_as_one_ask(tmp_path: Path) -> None:
    workspace(tmp_path)
    words = "add a gift note\u2028and a card"
    lem("task", "open", "gift-note", "--ask", words, cwd=tmp_path)
    shown = result(lem("task", "show", "gift-note", cwd=tmp_path))
    assert shown["ask"] == words


def test_two_opens_at_one_moment_one_takes_the_ticket(tmp_path: Path) -> None:
    where = workspace(tmp_path, LINEAR)
    codes: list[str] = []

    def one(slug: str) -> None:
        try:
            opened(where, slug, ticket="MBZ-12")
            codes.append("opened")
        except Refusal as refused:
            codes.append(refused.code)

    both = [threading.Thread(target=one, args=(slug,)) for slug in ("first", "second")]
    for thread in both:
        thread.start()
    for thread in both:
        thread.join(timeout=30)
    assert sorted(codes) == ["opened", "ticket-held"]


def test_one_issue_is_one_task_whatever_the_case_of_its_repository(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path, GITHUB)
    opened(where, "first", ticket="42", ticket_repo="ACME/shop")
    with pytest.raises(Refusal) as refused:
        opened(where, "second", ticket="42", ticket_repo="acme/shop")
    assert refused.value.code == "ticket-held"


def test_the_same_slug_and_words_with_another_ticket_are_no_retry(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path, LINEAR)
    opened(where, ticket="MBZ-12")
    assert opened(where, ticket="mbz-12") == "shaping"
    with pytest.raises(Refusal) as refused:
        opened(where, ticket="MBZ-13")
    assert refused.value.code == "task-exists"


def test_a_branch_origin_has_is_refused_before_the_task_is_written(
    tmp_path: Path,
) -> None:
    repo = RealRepo.init(tmp_path / "repo", {"README.md": b"one\n"})
    where = workspace(repo.checkout)
    repo.outside_commit("fix/gift-note", {"THEIRS.md": b"x\n"})
    with pytest.raises(Refusal) as refused:
        opened(where)
    assert refused.value.code == "branch-taken"
    with pytest.raises(Refusal):
        opened(where, "other", branch="fix/gift-note")
    assert not (where.state / "tasks" / "gift-note").exists()
    assert opened(where, "gift-card") == "shaping"


def test_an_origin_that_does_not_answer_is_said_and_the_task_opens(
    tmp_path: Path,
) -> None:
    workspace(tmp_path)
    ran = lem("task", "open", "gift-note", "--ask", "add a gift note", cwd=tmp_path)
    assert "origin did not answer" in result(ran)["said"]


def test_a_reviewers_item_as_the_ask_is_claimed_and_a_gone_one_is_refused(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    item = ".lem/state/backlog/gift-note.md"
    (tmp_path / item).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / item).write_text("# Gift note\n", encoding="utf-8")
    opening.opened(where.checkout, Asked(slug="gift-note", ask=item))
    assert read(where, "gift-note").task.backlog_item == item
    gone = ".lem/state/backlog/dropped.md"
    with pytest.raises(Refusal) as refused:
        opening.opened(where.checkout, Asked(slug="other", ask=f"{tmp_path}/{gone}"))
    assert refused.value.code == "item-gone"
