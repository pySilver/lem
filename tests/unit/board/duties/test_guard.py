"""The guard of a stopped session as the board server runs it at each tick: the status message
after 45 minutes with no sign of work, then a fresh session when the signs read or the stop when
they do not, each once, and nothing for a task that waits for the owner or out of its phase."""

from datetime import timedelta
from typing import TYPE_CHECKING

from fakes.records import MOMENT
from lem.app.sessions import acts, guard_acts, guard_steps, log, opening
from lem.board.duties import guard
from lem.board.duties.memory import Kept
from lem.kernel.errors import Refusal
from lem.ports.harness import Signs, Transcript
from lem.records.holds import OwnerHold
from lem.records.sessions import SessionLine
from lem.store import sessions
from unit.board.duties.world import duty_of
from unit.sessions.harness import SigningHarness
from unit.sessions.terminal import with_caller
from unit.sessions.world import SLUG, here_of, made

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

    from lem.app.sessions.guard_acts import Acted
    from lem.app.sessions.here import Here

QUIET = MOMENT + timedelta(minutes=45)


def kinds(here: Here) -> list[tuple[str, str | None]]:
    """Lem's acts on the task's sessions after its first open: each kind with its why."""
    found = log.read(here.folder(SLUG))[1:]
    return [(type(act).__name__.lower(), getattr(act, "why", None)) for act in found]


def signing(here: Here, harness: SigningHarness, signs: Signs) -> None:
    """The task's session `session-1` with one transcript whose signs are `signs`."""
    line = SessionLine(
        at=MOMENT,
        source="startup",
        claude="c1",
        transcript="t",
        pane="session-1",
        task=SLUG,
    )
    sessions.append(here.folder(SLUG), line)
    harness.by_task[SLUG] = (Transcript(path="t", claude="c1"),)
    harness.signs_of["t"] = signs


def test_a_session_quiet_for_45_minutes_gets_the_message_then_its_stop_and_never_a_restart_unread(
    tmp_path: Path,
) -> None:
    terminal = with_caller()
    here = here_of(tmp_path, terminal)
    made(here, status="building", lead="builder")
    opening.open_session(here, SLUG, "new", None, MOMENT)
    kept = Kept()
    guard.tick(duty_of(here, QUIET - timedelta(seconds=1), kept))
    assert kinds(here) == []
    guard.tick(duty_of(here, QUIET, kept))
    assert kinds(here) == [("wake", "status")]
    guard.tick(duty_of(here, QUIET + timedelta(minutes=9), kept))
    assert kinds(here) == [("wake", "status")]
    guard.tick(duty_of(here, QUIET + timedelta(minutes=10), kept))
    guard.tick(duty_of(here, QUIET + timedelta(minutes=11), kept))
    assert kinds(here) == [("wake", "status"), ("stopped", None)]
    assert len(terminal.openings) == 1


def test_ten_minutes_after_the_message_a_session_whose_signs_read_is_restarted_beside_it(
    tmp_path: Path,
) -> None:
    terminal = with_caller()
    harness = SigningHarness()
    here = here_of(tmp_path, terminal, harness)
    made(here, status="landing", lead="small")
    opening.open_session(here, SLUG, "new", None, MOMENT)
    signing(here, harness, Signs(sign=MOMENT, turn="ended"))
    kept = Kept()
    guard.tick(duty_of(here, QUIET, kept))
    guard.tick(duty_of(here, QUIET + timedelta(minutes=10), kept))
    assert kinds(here) == [
        ("wake", "status"),
        ("open", "stopped"),
        ("wake", "replaced"),
    ]
    assert len(terminal.openings) == 2


def test_a_session_that_still_works_and_a_task_that_waits_for_the_owner_are_not_woken(
    tmp_path: Path,
) -> None:
    harness = SigningHarness()
    here = here_of(tmp_path, with_caller(), harness)
    made(here, status="building", lead="builder")
    opening.open_session(here, SLUG, "new", None, MOMENT)
    signing(here, harness, Signs(sign=MOMENT, shell=True))
    hold = OwnerHold(on="criteria", line="the criteria wait", since=MOMENT)
    made(here, "held", status="building", lead="builder", hold=hold)
    opening.open_session(here, "held", "new", None, MOMENT)
    guard.tick(duty_of(here, QUIET + timedelta(hours=2)))
    assert kinds(here) == []
    held = [act for act in log.read(here.folder("held")) if isinstance(act, acts.Wake)]
    assert held == []


def test_a_step_that_failed_waits_five_minutes_before_its_next_try(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    here = here_of(tmp_path)
    made(here, status="building", lead="builder")
    opening.open_session(here, SLUG, "new", None, MOMENT)
    tries: list[str] = []

    def refused(*_given: object) -> guard_steps.Acted:
        tries.append("try")
        raise Refusal("terminal", "agterm did not answer", "the owner starts agterm")

    monkeypatch.setattr(guard_steps, "stepped", refused)
    kept = Kept()
    for minutes in (0, 1, 4, 5):
        guard.tick(duty_of(here, QUIET + timedelta(minutes=minutes, seconds=59), kept))
    assert tries == ["try", "try"]
    said = capsys.readouterr().err
    assert (
        f"lem serve: shop: lem session wake {SLUG} --why status --session session-1 failed: "
        "agterm did not answer"
    ) in said


def test_the_step_names_the_session_it_is_for_in_the_servers_log(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    here = here_of(tmp_path)
    made(here, status="building", lead="builder")
    opening.open_session(here, SLUG, "new", None, MOMENT)
    guard.tick(duty_of(here, QUIET))
    said = capsys.readouterr().err
    assert (
        f"lem session wake {SLUG} --why status --session session-1: the session" in said
    )


def test_a_step_that_acted_on_nothing_says_why_in_the_servers_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    here = here_of(tmp_path)
    made(here, status="building", lead="builder")
    opening.open_session(here, SLUG, "new", None, MOMENT)

    def nothing(
        _here: Here, slug: str, _step: str, session: str, _now: object
    ) -> Acted:
        return guard_acts.refused(slug, session, guard_acts.WORKING)

    monkeypatch.setattr(guard_steps, "stepped", nothing)
    guard.tick(duty_of(here, QUIET))
    said = capsys.readouterr().err
    assert (
        f"--session session-1: Lem did nothing for {SLUG}: its session showed a sign"
        in said
    )


def test_a_turn_read_after_an_unread_message_is_put_on_record_once(
    tmp_path: Path,
) -> None:
    harness = SigningHarness()
    here = here_of(tmp_path, with_caller(), harness)
    made(here, status="building", lead="builder")
    opening.open_session(here, SLUG, "new", None, MOMENT)
    kept = Kept()
    guard.tick(duty_of(here, QUIET, kept))
    signing(here, harness, Signs(sign=QUIET + timedelta(minutes=1), turn="ended"))
    guard.tick(duty_of(here, QUIET + timedelta(minutes=2), kept))
    guard.tick(duty_of(here, QUIET + timedelta(minutes=3), kept))
    assert kinds(here) == [("wake", "status"), ("worked", None)]
