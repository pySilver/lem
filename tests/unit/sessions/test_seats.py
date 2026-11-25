"""The seat a task's role takes, the fallback that stands in for a seat whose agent gave an error,
the block when none may, and the owner's go on."""

from datetime import timedelta
from typing import TYPE_CHECKING

import pytest

from fakes.records import MOMENT
from lem.app.sessions import seats, seats_again
from lem.kernel.errors import Refusal
from lem.records.holds import Blocked
from lem.records.journal.task import StateNoted
from lem.records.work import StandIn
from unit.sessions.world import SLUG, here_of, made

if TYPE_CHECKING:
    from pathlib import Path

    from lem.app.sessions.here import Here


def failure(seat: str = "codex/gpt-6.2-sol:high") -> StandIn:
    """The reviewer's agent on `seat` is not logged in."""
    return StandIn(seat="reviewer", failed=seat, error="login", at=MOMENT)


def settings(here: Here, text: str) -> None:
    """The team's settings file of the workspace."""
    (here.where.lem / "settings.toml").write_text(text)


def test_a_seat_comes_from_the_first_file_that_names_it_else_lems_own(
    tmp_path: Path,
) -> None:
    here = here_of(tmp_path)
    made(here)
    default = seats.shown(here, SLUG, "reviewer")
    assert (default.seat, default.source) == ("claude/opus:high", "Lem's default")
    settings(here, '[seats]\nreviewer = "codex/gpt-6.2-sol:high"\n')
    (here.where.lem / "settings.local.toml").write_text(
        '[seats]\nreviewer = "claude/fable:xhigh"\n'
    )
    mine = seats.shown(here, SLUG, "reviewer")
    assert (mine.seat, mine.source) == (
        "claude/fable:xhigh",
        ".lem/settings.local.toml",
    )


def test_the_fallback_stands_in_until_the_owners_go_on(tmp_path: Path) -> None:
    here = here_of(tmp_path)
    made(here, status="building", lead="builder")
    settings(here, '[seats]\nreviewer = "codex/gpt-6.2-sol:high"\n')
    record = seats.failed(here, SLUG, failure())
    assert record.task.hold is None
    shown = seats.shown(here, SLUG, "reviewer")
    assert (shown.seat, shown.source) == ("claude/opus:high", "stand-in")
    entry = record.journal[-1]
    assert isinstance(entry, StateNoted)
    assert "stands in for it" in (entry.line or "")
    with pytest.raises(Refusal) as nothing:
        seats_again.again(here, SLUG, MOMENT)
    assert nothing.value.code == "no-seat-block"


@pytest.mark.parametrize(
    ("team", "seat"),
    [
        ("[seats]\nfallback = false\n", "codex/gpt-6.2-sol:high"),
        ("", "claude/opus:high"),
    ],
)
def test_a_task_is_blocked_when_no_fallback_may_stand_in(
    tmp_path: Path, team: str, seat: str
) -> None:
    here = here_of(tmp_path)
    made(here, status="building", lead="builder")
    settings(here, team)
    record = seats.failed(here, SLUG, failure(seat))
    hold = record.task.hold
    assert isinstance(hold, Blocked)
    assert (hold.seat, hold.fix) == (
        "reviewer",
        f"lem seat again {SLUG} once the owner has fixed it",
    )
    back = seats_again.again(here, SLUG, MOMENT + timedelta(minutes=1))
    assert back.task.hold is None
    assert [one.again for one in back.task.stand_ins] == [MOMENT + timedelta(minutes=1)]
    assert seats.shown(here, SLUG, "reviewer").source != "stand-in"


def test_a_failed_seat_not_in_its_form_is_refused(tmp_path: Path) -> None:
    here = here_of(tmp_path)
    made(here)
    with pytest.raises(Refusal) as refused:
        seats.failed(here, SLUG, failure("codex"))
    assert refused.value.code == "seat"
