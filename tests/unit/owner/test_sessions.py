"""What waits when a task has no session, or its live session works on the owner's answer."""

from datetime import timedelta
from typing import TYPE_CHECKING

import pytest

from fakes.records import MOMENT, record
from lem.app.owner import looking, scope
from lem.app.sessions import acts, log
from lem.ports.harness import Signs, Transcript
from lem.ports.terminal import Opening
from lem.records.holds import BreakerHold, OwnerHold
from lem.records.sessions import SessionLine
from lem.store import sessions, tasks
from unit.sessions.harness import SigningHarness
from unit.sessions.terminal import with_caller
from unit.sessions.test_use_cases import here_of

if TYPE_CHECKING:
    from pathlib import Path

    from lem.app.sessions.here import Here

NOW = MOMENT + timedelta(hours=1)


def test_a_task_with_no_open_on_record_waits_after_the_grace_period(
    tmp_path: Path,
) -> None:
    here = here_of(tmp_path)
    tasks.create(here.where.state, record("gift-note", status="building"))
    early = looking.looked(here, MOMENT)
    assert scope.scoped(early, None, MOMENT).rows == ()
    seen = looking.looked(here, NOW)
    assert seen.unknown is None
    assert [row.key for row in scope.scoped(seen, None, NOW).rows] == [
        "session:gift-note"
    ]


def test_only_a_pane_with_its_agent_counts_as_live(tmp_path: Path) -> None:
    terminal = with_caller()
    here = here_of(tmp_path, terminal)
    tasks.create(here.where.state, record("gift-note", status="building"))
    session = opened(here)
    seen = looking.looked(here, NOW)
    assert scope.scoped(seen, None, NOW).rows == ()
    terminal.end_agent(session)
    seen = looking.looked(here, NOW)
    assert [row.key for row in scope.scoped(seen, None, NOW).rows] == [
        "session:gift-note"
    ]
    terminal.unreadable = "the terminal did not answer"
    seen = looking.looked(here, NOW)
    assert seen.unknown and "the terminal did not answer" in seen.unknown
    assert scope.scoped(seen, None, NOW).rows == ()


@pytest.mark.parametrize(
    ("hold", "key"),
    [
        (BreakerHold(number=2, since=MOMENT), "breaker:gift-note:2"),
        (OwnerHold(on="fact", line="Which label?", since=MOMENT), "held:gift-note"),
    ],
)
def test_a_held_row_returns_when_the_reply_turn_ends(
    tmp_path: Path, hold: BreakerHold | OwnerHold, key: str
) -> None:
    terminal, harness = with_caller(), SigningHarness()
    here = here_of(tmp_path, terminal, harness)
    tasks.create(here.where.state, record("gift-note", status="building", hold=hold))
    session = opened(here)
    sessions.append(
        here.folder("gift-note"),
        SessionLine(
            at=MOMENT,
            source="startup",
            claude="claude-1",
            transcript="/t/claude-1",
            pane=session,
            task="gift-note",
        ),
    )
    harness.by_task["gift-note"] = (Transcript(path="/t/claude-1", claude="claude-1"),)
    harness.signs_of["/t/claude-1"] = Signs(sign=NOW, turn="runs")
    seen = looking.looked(here, NOW)
    assert scope.scoped(seen, None, NOW).rows == ()
    harness.signs_of["/t/claude-1"] = Signs(sign=NOW, turn="ended")
    seen = looking.looked(here, NOW)
    assert [row.key for row in scope.scoped(seen, None, NOW).rows] == [key]


def opened(here: Here) -> str:
    terminal = here.ports.terminal
    opening = Opening(
        name="gift-note", cwd=str(here.where.checkout), command=("claude",)
    )
    session = terminal.open(opening)
    log.append(
        here.folder("gift-note"),
        acts.Open(
            session=session, name="gift-note", phase="fast", why="new", at=MOMENT
        ),
    )
    return session
