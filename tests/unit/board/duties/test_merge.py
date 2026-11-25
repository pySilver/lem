"""The merges that are the board server's to make: the merge agent's `merge` and the owner's merge
that stands, never while the forge calls the request conflicting, a call waits on the forge or
this server runs the merge; the count of approved tasks that wait at each (the merge line); and
the wait of a merge that failed, which a new read ends."""

import threading
from datetime import timedelta
from typing import TYPE_CHECKING

from msgspec.structs import replace

from fakes.records import MOMENT
from lem.app.landing import merge
from lem.app.owner import forge
from lem.board.duties import merge as duty
from lem.board.duties import merge_line
from lem.board.duties.memory import Kept
from lem.kernel.errors import Refusal
from lem.model.landing import merge_standing
from lem.records.landing.merge import MergeIntent
from lem.records.landing.propose import Standing
from lem.store import tasks
from unit.board.duties.world import duty_of, landing_of, looked, opened
from unit.owner.looked import TIP, proposed, read
from unit.sessions.world import here_of

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

    from lem.app.sessions.here import Here
    from lem.model.landing.merge_asked import Asked
    from lem.records.record import Record

HOUR = MOMENT + timedelta(hours=1)
LOOK = forge.Look()


def asking(
    monkeypatch: pytest.MonkeyPatch, refusal: Refusal | None = None
) -> list[Asked]:
    """The merges the server asks for, each refused with `refusal` when one is named."""
    asked: list[Asked] = []

    def merged(folder: Path, slug: str, given: Asked) -> None:
        asked.append(given)
        if refusal is not None:
            raise refusal

    monkeypatch.setattr(merge, "run", merged)
    return asked


def ended(kept: Kept) -> None:
    """Wait for each merge the server started."""
    for run in kept.merging.values():
        run.join()


def standing_task(here: Here, slug: str) -> Record:
    """An open task whose owner's merge, refused for the base, stands for the proposed tip."""
    found = opened(here, slug, proposed=proposed(green=False, who="owner"))
    digest = merge_standing.digest_of(merge_standing.reasons_now(found))
    kept = Standing(tip=TIP, reasons_digest=digest, by_act="board", at=MOMENT)
    landing = replace(landing_of(found), standing=kept)
    return tasks.update(
        here.where.state, slug, lambda one: replace(one, landing=landing), 1
    )


def test_the_merge_agents_merge_of_the_proposed_tip_is_the_servers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    here = here_of(tmp_path)
    opened(here, "agent-merges", proposed=proposed(), reads=(read("merge"),))
    opened(here, "calls-owner", proposed=proposed(), reads=(read("call"),))
    opened(here, "owner-merges", proposed=proposed(who="owner"), reads=(read("merge"),))
    asked = asking(monkeypatch)
    kept = Kept()
    duty.tick(duty_of(here, HOUR, kept))
    ended(kept)
    assert [(one.by, one.via, one.tip, one.standing) for one in asked] == [
        ("merger", "server", TIP, False)
    ]
    assert asked[0].subject == "Gift note"


def test_the_owners_merge_that_stands_is_carried_out_by_the_server(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    here = here_of(tmp_path)
    standing_task(here, "stands")
    asked = asking(monkeypatch)
    kept = Kept()
    duty.tick(duty_of(here, HOUR, kept))
    ended(kept)
    assert [(one.by, one.standing) for one in asked] == [("owner", True)]


def test_no_merge_while_the_forge_calls_it_conflicting_a_call_waits_or_it_runs(
    tmp_path: Path,
) -> None:
    here = here_of(tmp_path)
    found = opened(here, "x", proposed=proposed(), reads=(read("merge"),))
    assert duty.merger_of(found, LOOK, frozenset()) == "merger"
    looked(here, "x", forge.CONFLICTING)
    assert duty.merger_of(found, forge.read(here.where.state), frozenset()) is None
    assert duty.merger_of(found, LOOK, frozenset({"x"})) is None
    intent = MergeIntent(tip=TIP, by="merger", via="server", at=MOMENT)
    waiting = replace(found, landing=replace(landing_of(found), intent=intent))
    assert duty.merger_of(waiting, LOOK, frozenset()) is None


def test_a_failed_merge_waits_for_its_own_read_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    here = here_of(tmp_path)
    found = opened(here, "x", proposed=proposed(), reads=(read("merge"),))
    asked = asking(monkeypatch, Refusal("lock", "the merge lock is held", "wait"))
    kept = Kept()
    for minutes in (0, 1, 4):
        duty.tick(duty_of(here, HOUR + timedelta(minutes=minutes), kept))
        ended(kept)
    assert len(asked) == 1
    newer = replace(read("merge"), at=HOUR)
    reads = landing_of(found).reads
    landing = replace(landing_of(found), reads=(*reads, newer))
    tasks.update(here.where.state, "x", lambda one: replace(one, landing=landing), 1)
    duty.tick(duty_of(here, HOUR + timedelta(minutes=4), kept))
    ended(kept)
    assert len(asked) == 2
    duty.tick(duty_of(here, HOUR + timedelta(minutes=9), kept))
    ended(kept)
    assert len(asked) == 3


def test_a_merge_that_ran_says_so_and_one_refused_says_why(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    here = here_of(tmp_path)
    opened(here, "goes", proposed=proposed(), reads=(read("merge"),))
    asking(monkeypatch)
    kept = Kept()
    duty.tick(duty_of(here, HOUR, kept))
    ended(kept)
    assert kept.said["goes"].startswith("Merged: goes is on the base.")
    asking(monkeypatch, Refusal("github", "GitHub refused it", "the owner acts"))
    opened(here, "refused", proposed=proposed(), reads=(read("merge"),))
    duty.tick(duty_of(here, HOUR, kept))
    ended(kept)
    assert kept.said["refused"] == "The merge did not go: GitHub refused it"
    said = capsys.readouterr().err
    assert (
        "lem serve: shop: `lem land merge goes --by merger --via server` started, with 1 "
        "other approved tasks waiting"
    ) in said


def test_each_merge_the_server_starts_records_how_many_approved_tasks_wait(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    here = here_of(tmp_path)
    for slug in ("a-first", "b-second", "c-third"):
        opened(here, slug, proposed=proposed(), reads=(read("merge"),))
    opened(here, "d-calls", proposed=proposed(), reads=(read("call"),))
    standing_task(here, "e-stands")
    gate = threading.Event()

    def held(folder: Path, slug: str, given: Asked) -> None:
        gate.wait()

    monkeypatch.setattr(merge, "run", held)
    kept = Kept()
    duty.tick(duty_of(here, HOUR, kept))
    gate.set()
    ended(kept)
    lines = merge_line.read(here.where.state)
    assert [(one.task, one.by, one.waiting) for one in lines] == [
        ("a-first", "merger", 3),
        ("b-second", "merger", 3),
        ("c-third", "merger", 3),
        ("e-stands", "owner", 3),
    ]
    assert lines[0].behind == ("b-second", "c-third", "e-stands")
    assert lines[0].tip == TIP
