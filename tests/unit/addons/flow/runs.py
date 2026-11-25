"""Runs of the night and the retro for the cases of the proposals: a proposal as a run gives it,
a run added to a state folder, a day's record as its file holds it, and the reviewer's verdicts."""

import datetime as dt
from typing import TYPE_CHECKING

from lem.addons.proposals import adding, days, verdicting, verdicts
from lem.addons.proposals.given import Given, RunGiven

if TYPE_CHECKING:
    from pathlib import Path

    from lem.addons.proposals.judgment import Judgment
    from lem.addons.proposals.record import DayRecord, Kind

MORNING = dt.datetime(2026, 11, 23, 6, 55, tzinfo=dt.UTC)
DAY = dt.date(2026, 11, 24)
TODAY = dt.date(2026, 11, 25)


def proposal(area: str, move: str, where: str = "skills/lem/stages/learn.md") -> Given:
    """One proposal of a run, about `area`."""
    return Given(
        area=area,
        move=move,
        body=f"Why: {move.lower()}",
        source="the task gift-note's records",
        where=where,
    )


def add(
    state: Path,
    kind: Kind,
    proposals: list[Given],
    day: dt.date = DAY,
    now: dt.datetime = MORNING,
) -> adding.Added:
    """Add one run of `kind` with `proposals` to its record of `day`."""
    run = RunGiven(read="the tasks since the last retro", proposals=tuple(proposals))
    return adding.added(state, kind, day, run, now)


def record(state: Path, kind: Kind, day: dt.date = DAY) -> DayRecord:
    """The record of `kind`'s proposals of `day`, as it is now."""
    found = days.read(days.path_of(state, kind, day), kind)
    assert found is not None
    return found


def judge(
    state: Path,
    given: list[dict[str, str]],
    titles: dict[str, str] | None = None,
    today: dt.date = TODAY,
) -> Judgment:
    """The reviewer's verdicts, each `{"proposal": NAME, "refuted"|"passed": ...}`."""
    told = verdicts.VerdictsGiven(
        verdicts=tuple(verdicts.VerdictGiven(**one) for one in given),
        titles=titles or {},
    )
    return verdicting.judged(state, told, today)


def eleven(state: Path) -> None:
    """One proposal of the night about the tests, and ten of the retro: six about lessons, four
    about the board."""
    add(state, "night", [proposal("tests", "Wait for the port", "tests/serve.py")])
    lessons = [proposal("lessons", f"Lesson {n}") for n in range(1, 7)]
    board = [
        proposal("board", f"Board {n}", "skills/lem/assets/board.css")
        for n in range(1, 5)
    ]
    add(state, "retro", [*lessons, *board])
