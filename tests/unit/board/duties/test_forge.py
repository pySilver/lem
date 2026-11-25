"""The board server's look at the forge: at the first tick and then every three minutes, only at a
GitHub origin and with a pull request open, written whole into `forge.json`; the forge's silence
as the board's problem; and the bookkeeping of a pull request the forge merged or closed, once,
again after a failure only when five minutes passed, and never while this server runs its
merge."""

import threading
from datetime import timedelta
from typing import TYPE_CHECKING, Literal

from fakes.forge import LocalForge
from fakes.git import ModelGit
from fakes.records import MOMENT
from lem.app.landing import merged
from lem.app.owner import forge
from lem.board.duties import conflict, forge_look, merge, runner, seams
from lem.board.duties import forge as duty
from lem.board.duties.memory import Kept
from lem.kernel.errors import Refusal
from lem.model.landing.invariants import target
from lem.model.landing.world import Rules
from lem.ports.faults import Unanswered
from lem.ports.forge_facts import Mergeable, Pull
from unit.board.duties.test_wakes import wakes
from unit.board.duties.world import duty_of, looked, opened
from unit.owner.looked import TIP, proposed, read
from unit.sessions.world import here_of

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

    from lem.app.sessions.here import Here

type State = Literal["open", "closed", "merged"]

HOUR = MOMENT + timedelta(hours=1)
LOOK = timedelta(seconds=180)


def pulled(
    here: Here, state: State = "open", mergeable: Mergeable = "mergeable"
) -> None:
    """Pull request 44 on the forge, in `state`, as GitHub calls its merge."""
    pull = Pull(
        number=44,
        url="https://github.com/o/r/pull/44",
        title="Gift note",
        state=state,
        head=TIP,
        head_ref="feat/gift-note",
        base="main",
        mergeable=mergeable,
    )
    found = here.ports.forge
    assert isinstance(found, LocalForge)
    found.pulls[44] = pull


def booking(
    monkeypatch: pytest.MonkeyPatch, refusal: Refusal | None = None
) -> list[str]:
    """The bookkeeping the server runs, each refused with `refusal` when one is named."""
    ran: list[str] = []

    def run(folder: Path, slug: str) -> None:
        ran.append(slug)
        if refusal is not None:
            raise refusal

    monkeypatch.setattr(merged, "run", run)
    return ran


def test_the_look_runs_at_the_first_tick_then_every_three_minutes_at_a_github_origin(
    tmp_path: Path,
) -> None:
    here = here_of(tmp_path)
    kept = Kept()
    assert forge_look.due(duty_of(here, HOUR, kept)) is True
    kept.looked = HOUR
    assert (
        forge_look.due(duty_of(here, HOUR + LOOK - timedelta(seconds=1), kept)) is False
    )
    assert forge_look.due(duty_of(here, HOUR + LOOK, kept)) is True
    git = here.ports.git
    assert isinstance(git, ModelGit)
    git.origin = "git@gitlab.com:acme/shop.git"
    assert forge_look.due(duty_of(here, HOUR + LOOK, kept)) is False


def test_the_look_is_written_whole_for_the_list_of_what_waits_and_the_conflicts_wake(
    tmp_path: Path,
) -> None:
    here = here_of(tmp_path)
    opened(here, "gift-note", proposed=proposed())
    pulled(here, mergeable="conflicting")
    duty.tick(duty_of(here, HOUR))
    look = forge.read(here.where.state)
    assert look.looked == HOUR
    assert look.seen == {"gift-note": forge.Seen(head=TIP, mergeable="CONFLICTING")}


def test_a_workspace_with_no_pull_request_open_asks_the_forge_nothing(
    tmp_path: Path,
) -> None:
    here = here_of(tmp_path)
    kept = Kept(problems={"forge": "an old problem"})
    duty.tick(duty_of(here, HOUR, kept))
    assert kept.looked is None
    assert kept.problems == {}
    assert not (here.where.state / forge.LOOK).exists()


def test_a_look_the_forge_does_not_answer_is_the_boards_problem_in_its_words(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    here = here_of(tmp_path)
    opened(here, "gift-note", proposed=proposed())
    kept = Kept()
    duty.tick(duty_of(here, HOUR, kept))
    assert kept.problems == {
        "forge": "the board cannot ask GitHub about the open pull requests: gh: no pull "
        "request 44"
    }

    def signed_out(number: int) -> Pull:
        raise Unanswered(
            "gh", "To get started with GitHub CLI, please run: gh auth login"
        )

    monkeypatch.setattr(here.ports.forge, "pull", signed_out)
    duty.tick(duty_of(here, HOUR + LOOK, kept))
    assert kept.problems["forge"].endswith(
        "`gh` is not signed in to github.com (`gh auth login` signs it in)"
    )
    pulled(here)
    monkeypatch.undo()
    duty.tick(duty_of(here, HOUR + 2 * LOOK, kept))
    assert kept.problems == {}


def test_the_runner_keeps_the_forge_problem_until_the_next_successful_poll(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    here = here_of(tmp_path)
    opened(here, "gift-note", proposed=proposed())
    kept = Kept()
    runner.ticked(duty_of(here, HOUR, kept))
    assert "no pull request 44" in kept.problems["forge"]
    runner.ticked(duty_of(here, HOUR + timedelta(seconds=1), kept))
    assert "no pull request 44" in kept.problems["forge"]

    def signed_out(number: int) -> Pull:
        raise Refusal(
            "forge-auth", "GitHub authentication is required", "run gh auth login"
        )

    with monkeypatch.context() as patch:
        patch.setattr(here.ports.forge, "pull", signed_out)
        runner.ticked(duty_of(here, HOUR + LOOK, kept))
        assert "run gh auth login" in kept.problems["forge"]
    pulled(here)
    runner.ticked(duty_of(here, HOUR + 2 * LOOK, kept))
    assert "forge" not in kept.problems


def test_a_duty_refusal_keeps_its_repair_in_the_returned_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def refused(_duty: object) -> None:
        raise Refusal(
            "access", "the forge refused access", "the owner runs gh auth login"
        )

    monkeypatch.setattr(duty, "tick", refused)
    failed = seams.failure(duty.__name__, duty_of(here_of(tmp_path), HOUR))
    assert failed == "Refusal: the forge refused access. the owner runs gh auth login"


def test_a_pull_request_merged_or_closed_on_github_gets_its_bookkeeping_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    here = here_of(tmp_path)
    opened(here, "gift-note", proposed=proposed())
    pulled(here, state="merged")
    ran = booking(monkeypatch)
    kept = Kept()
    duty.tick(duty_of(here, HOUR, kept))
    duty.tick(duty_of(here, HOUR + LOOK, kept))
    assert ran == ["gift-note"]
    assert (
        "lem serve: shop: pull request 44 of gift-note is merged on GitHub; `lem land merged "
        "gift-note` left it open"
    ) in capsys.readouterr().err


def test_a_failed_bookkeeping_is_the_boards_problem_and_is_tried_again_after_five_minutes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    here = here_of(tmp_path)
    opened(here, "gift-note", proposed=proposed())
    pulled(here, state="closed")
    ran = booking(monkeypatch, Refusal("step-held", "the step lock is held", "wait"))
    kept = Kept()
    duty.tick(duty_of(here, HOUR, kept))
    duty.tick(duty_of(here, HOUR + LOOK, kept))
    assert ran == ["gift-note"]
    assert kept.problems == {
        "merged:gift-note": "`lem land merged gift-note` failed after GitHub called pull "
        "request 44 closed: the step lock is held; wait; the board tries it again in a few minutes"
    }
    booking(monkeypatch)
    duty.tick(duty_of(here, HOUR + timedelta(minutes=6), kept))
    assert kept.problems == {}
    assert ("merged", "gift-note", "44") in kept.done


def test_a_task_whose_merge_this_server_runs_gets_no_bookkeeping(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    here = here_of(tmp_path)
    opened(here, "gift-note", proposed=proposed())
    pulled(here, state="merged")
    ran = booking(monkeypatch)
    gate = threading.Event()
    run = threading.Thread(target=gate.wait)
    run.start()
    kept = Kept(merging={"gift-note": run})
    duty.tick(duty_of(here, HOUR, kept))
    gate.set()
    run.join()
    assert ran == []


def test_a_problem_of_a_task_that_no_longer_has_a_pull_request_open_is_forgotten(
    tmp_path: Path,
) -> None:
    here = here_of(tmp_path)
    found = opened(here, "gift-note", proposed=proposed())
    kept = Kept(problems={"merged:gift-note": "old", "merged:gone": "old"}, looked=HOUR)
    duty.tick(duty_of(here, HOUR, kept))
    assert kept.problems == {"merged:gift-note": "old"}
    assert found.task.status == "open"


def test_a_forge_write_failure_keeps_the_fresh_conflict_for_both_duties(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    here = here_of(tmp_path)
    slug = "gift-note"
    opened(here, slug, proposed=proposed(), reads=(read("merge"),))
    pulled(here, mergeable="conflicting")
    looked(here, slug, "MERGEABLE")

    def unavailable(path: Path, body: bytes) -> None:
        raise OSError("forge.json cannot be replaced")

    board = duty_of(here, HOUR)
    with monkeypatch.context() as patch:
        patch.setattr(forge_look.files, "write_whole", unavailable)
        duty.tick(board)
    started: list[str] = []
    monkeypatch.setattr(merge.merge_run, "started", lambda *_: started.append(slug))

    merge.tick(board)
    conflict.tick(board)

    assert started == []
    assert [(why, head) for why, head in wakes(here) if head] == [("conflict", TIP)]


def test_a_merge_into_another_branch_shows_the_owners_remedy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    here = here_of(tmp_path)
    opened(here, "gift-note", proposed=proposed())
    pulled(here, state="merged")
    refusal = target("release", Rules(base="main"), "https://github.com/o/r/pull/44")
    assert refusal is not None
    booking(monkeypatch, refusal)
    board = duty_of(here, HOUR)

    duty.tick(board)

    assert "drops the task" in board.kept.problems["merged:gift-note"]
    assert "brings the change onto main" in board.kept.problems["merged:gift-note"]
