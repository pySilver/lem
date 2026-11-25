"""`lem task move`: the table of statuses, the stale wake-up over a landing, a park and a seat's
block, `answered` with its report, the start over of a landing, and the owner's drop under the
landing's step lock."""

import subprocess
import sys
import threading
import time
from typing import TYPE_CHECKING, Literal

import pytest
from msgspec.structs import replace

from fakes.command import lem
from fakes.forge import LocalForge
from fakes.git import ModelGit
from fakes.ports import fake_ports
from fakes.records import MOMENT
from lem.app.tasks import drop, move
from lem.kernel.errors import Refusal
from lem.model.task import ending, table
from lem.ports.forge_facts import Pull
from lem.records.holds import Blocked, BreakerHold, OwnerHold, Parked, ReleaseHold
from lem.records.journal.task import StateNoted
from lem.records.landing.propose import MergeRead, Proposed, Standing
from lem.records.landing.record import Landing
from lem.records.landing.record import Pull as LandingPull
from lem.records.landing.review import Reviewed
from lem.records.landing.start import Started
from lem.records.work import Investigation
from lem.store import steps, tasks
from unit.task.spaces import last_line, made, read, result, workspace

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.task import Status

    type PullState = Literal["open", "closed", "merged"]
    from lem.store.places import Workspace

SHA = "a" * 40
SLUG = "gift-note"
PULL_URL = "https://github.com/owner/project/pull/7"


def moved(
    where: Workspace, status: Status, *lines: str, start_over: str | None = None
) -> table.Moved:
    """Move the task `SLUG` from the folder of the call."""
    return move.moved(where.checkout, SLUG, status, lines, start_over)


def refusal(where: Workspace, status: Status, start_over: str | None = None) -> str:
    """The code of the refusal of a move of `SLUG` to `status`."""
    with pytest.raises(Refusal) as refused:
        moved(where, status, start_over=start_over)
    return refused.value.code


@pytest.mark.parametrize(
    ("was", "status"),
    [
        ("queued", "shaping"),
        ("queued", "building"),
        ("shaping", "building"),
        ("shaping", "queued"),
        ("building", "planned"),
        ("building", "ready"),
        ("building", "queued"),
        ("planned", "building"),
        ("ready", "building"),
        ("landing", "shaping"),
    ],
)
def test_each_move_of_the_table_is_taken_and_journaled(
    tmp_path: Path, was: Status, status: Status
) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status=was)
    assert moved(where, status, "the lead's line").status == status
    record = read(where, SLUG)
    entry = record.journal[-1]
    assert isinstance(entry, StateNoted)
    assert (record.task.status, entry.line) == (status, "the lead's line")


@pytest.mark.parametrize(
    ("was", "status"),
    [
        ("queued", "ready"),
        ("planned", "ready"),
        ("ready", "planned"),
        ("shaping", "planned"),
    ],
)
def test_a_move_the_table_does_not_have_names_where_it_may_go(
    tmp_path: Path, was: Status, status: Status
) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status=was)
    assert refusal(where, status) == "move"


@pytest.mark.parametrize("status", ["landing", "open", "landed"])
def test_the_landings_own_statuses_move_by_lem_land(
    tmp_path: Path, status: Status
) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status="ready")
    assert refusal(where, status) == "move"


@pytest.mark.parametrize("status", ["building", "queued", "planned", "ready"])
def test_a_leads_state_over_a_task_with_its_landing_is_a_stale_wake_up(
    tmp_path: Path, status: Status
) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status="open")
    assert refusal(where, status) == "move"
    assert read(where, SLUG).task.status == "open"


@pytest.mark.parametrize("ended", ["landed", "dropped", "answered"])
def test_an_ended_task_stays_ended(tmp_path: Path, ended: Status) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status=ended)
    assert refusal(where, "building") == "ended"
    assert refusal(where, "dropped") == "ended"


def test_a_parked_task_takes_a_drop_and_a_resume_only(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status="planned", hold=Parked(since=MOMENT, words="later"))
    assert refusal(where, "building") == "parked"
    assert drop.dropped(where, SLUG, "not wanted").status == "dropped"
    assert read(where, SLUG).task.hold is None


def test_a_seats_block_is_lifted_by_his_go_on_only(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    hold = Blocked(
        why="the reviewer failed", fix="go on", seat="reviewer", since=MOMENT
    )
    made(where, SLUG, status="building", hold=hold)
    assert refusal(where, "ready") == "seat-blocked"


def test_a_move_answers_the_owners_wait_and_a_breaker(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    made(
        where,
        SLUG,
        status="shaping",
        hold=OwnerHold(on="interview", line="x", since=MOMENT),
    )
    moved(where, "building")
    assert read(where, SLUG).task.hold is None
    made(where, "other", status="building", hold=BreakerHold(number=1, since=MOMENT))
    move.moved(where.checkout, "other", "planned", ())
    assert read(where, "other").task.hold is None


def test_answered_needs_the_report_and_a_call_that_ends_the_task(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    found = Investigation(kind="question", call="answer", line="it is the cache")
    made(where, SLUG, status="building", investigation=found)
    assert refusal(where, "answered") == "answered"
    (where.state / "tasks" / SLUG / "investigation.md").write_text(
        "# x\n", encoding="utf-8"
    )
    made(
        where,
        "fix",
        status="building",
        investigation=Investigation(kind="fix", call="small"),
    )
    (where.state / "tasks" / "fix" / "investigation.md").write_text(
        "# x\n", encoding="utf-8"
    )
    with pytest.raises(Refusal):
        move.moved(where.checkout, "fix", "answered", ())
    assert moved(where, "answered").status == "answered"


def landing() -> Landing:
    """A landing proposed, with a review, a read and the owner's standing merge."""
    review = Reviewed(
        attempt=1,
        tip=SHA,
        of="change",
        scope="whole",
        floor="read",
        kind="read",
        at=MOMENT,
    )
    proposed = Proposed(tip=SHA, base=SHA, green=True, who_acts="owner", at=MOMENT)
    standing = Standing(tip=SHA, reasons_digest="d", by_act="merge", at=MOMENT)
    carried = MergeRead(tip=SHA, base=SHA, base_tree=SHA, carried_from=SHA, at=MOMENT)
    return Landing(
        phase="open",
        reviews=(review,),
        reads=(carried,),
        proposed=proposed,
        standing=standing,
    )


def test_the_start_over_archives_the_reviews_and_ends_the_owners_merge(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status="open")
    record = read(where, SLUG)
    with_landing = replace(record, landing=landing())
    assert with_landing.landing is not None
    assert with_landing.landing.reads
    started = ending.started_over(with_landing, "the record of the review is broken")
    assert started.landing is not None
    assert (started.landing.reviews, started.landing.reads) == ((), ())
    assert len(started.landing.archived) == 1
    assert started.landing.standing is None
    assert started.landing.proposed is not None
    merge = started.landing.proposed.owner_merge
    assert merge is not None
    assert (merge.state, merge.why) == (
        "ended",
        "the landing started over: the record of the review is broken",
    )


def test_the_flag_writes_the_line_under_why_and_a_plain_ready_has_none(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status="landing")
    moved(where, "ready", start_over="the checks' record is broken")
    line = last_line(where, SLUG)
    assert line == f"{ending.START_OVER}: the checks' record is broken"
    made(where, "plain", status="building")
    move.moved(where.checkout, "plain", "ready", ("the report is written",))
    assert last_line(where, "plain") == "the report is written"
    assert refusal(where, "building", start_over="why") == "start-over"


def test_a_drop_goes_from_any_status_that_is_not_ended(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    for status in (
        "queued",
        "shaping",
        "building",
        "planned",
        "ready",
        "landing",
        "open",
    ):
        made(where, status, status=status)
        assert drop.dropped(where, status, "not wanted").was == status
        assert read(where, status).task.status == "dropped"


def test_a_drop_of_a_task_two_releases_back_keeps_the_stop_for_the_resume(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    created = made(where, SLUG, status="open")
    old = tasks.update(where.state, SLUG, lambda one: replace(one, release="0.1.0"), 1)
    assert old.release == "0.1.0"
    assert created.revision == 1
    assert drop.dropped(where, SLUG, "not wanted").status == "dropped"
    assert isinstance(read(where, SLUG).task.hold, ReleaseHold)


def forge_with(where: Workspace, state: PullState, base: str = "main") -> LocalForge:
    """A forge whose pull request 7 is `state` on `base`."""
    pull = Pull(
        number=7,
        url=PULL_URL,
        title="Add a gift note",
        state=state,
        head=SHA,
        head_ref="feat/gift-note",
        base=base,
    )
    return LocalForge(remote=ModelGit(checkout=where.checkout), pulls={7: pull})


@pytest.mark.parametrize(
    ("state", "base", "dropped"),
    [("merged", "main", False), ("open", "main", True), ("merged", "other", True)],
)
def test_only_a_merge_into_the_tasks_base_defeats_the_drop(
    tmp_path: Path, state: PullState, base: str, *, dropped: bool
) -> None:
    where = workspace(tmp_path)
    pull = LandingPull(number=7, url=PULL_URL, title="t")
    made(where, SLUG, status="open")
    tasks.update(
        where.state, SLUG, lambda one: replace(one, landing=Landing(pull=pull)), 1
    )
    forge = forge_with(where, state, base)
    ports = fake_ports(ModelGit(checkout=where.checkout), forge)
    if dropped:
        assert drop.dropped(where, SLUG, "not wanted", ports).status == "dropped"
        return
    with pytest.raises(Refusal) as refused:
        drop.dropped(where, SLUG, "not wanted", ports)
    assert refused.value.code == "merged"
    assert read(where, SLUG).task.status == "open"


def test_a_drop_that_comes_while_a_step_runs_waits_for_it_and_stays_on_top(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status="landing")
    done: list[str] = []
    with steps.step(where.state, SLUG, "propose", MOMENT):
        waiting = threading.Thread(
            target=lambda: done.append(drop.dropped(where, SLUG, "not wanted").status)
        )
        waiting.start()
        time.sleep(0.5)
        assert done == []
    waiting.join(timeout=30)
    assert done == ["dropped"]


CHECKS = """
import sys, time
from datetime import UTC, datetime
from pathlib import Path
from lem.store import steps, tasks
with steps.step(Path(sys.argv[1]), sys.argv[2], "checks", datetime.now(UTC)):
    print("held", flush=True)
    time.sleep(60)
"""


def test_a_drop_stops_the_running_checks_and_takes_the_lock(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status="landing")
    checks = subprocess.Popen(
        [sys.executable, "-I", "-c", CHECKS, str(where.state), SLUG],
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert checks.stdout is not None
        assert checks.stdout.readline().strip() == "held"
        assert drop.dropped(where, SLUG, "not wanted").status == "dropped"
        assert checks.wait(timeout=30) != 0
    finally:
        checks.kill()
        checks.wait()


def test_the_command_drops_with_the_owners_reason(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status="building")
    ran = lem("task", "move", SLUG, "dropped", "--line", "not wanted", cwd=tmp_path)
    assert result(ran) == {"slug": SLUG, "was": "building", "status": "dropped"}
    assert last_line(where, SLUG) == "not wanted"


def test_the_table_is_the_designs() -> None:
    assert set(table.MOVES) == {
        "queued",
        "shaping",
        "building",
        "planned",
        "ready",
        "landing",
        "open",
    }
    assert all("dropped" in moves.split() for moves in table.MOVES.values())


def proposed(where: Workspace, base: str) -> None:
    """The task `SLUG` with pull request 7, its landing started on `base`."""
    started = Started(round=1, branch=f"feat/{SLUG}", base_ref=base, at=MOMENT)
    pull = LandingPull(number=7, url=PULL_URL, title="t")
    landing = Landing(pull=pull, started=started)
    revision = read(where, SLUG).revision
    tasks.update(where.state, SLUG, lambda one: replace(one, landing=landing), revision)


@pytest.mark.parametrize(
    ("merged_into", "refused"), [("main", True), ("stable", False)]
)
def test_the_drop_reads_the_base_its_landing_started_on_not_the_settings_of_now(
    tmp_path: Path, merged_into: str, *, refused: bool
) -> None:
    where = workspace(tmp_path, '[branch]\nbase = "stable"\n')
    made(where, SLUG, status="open")
    proposed(where, "main")
    forge = forge_with(where, "merged", merged_into)
    given = fake_ports(ModelGit(checkout=where.checkout), forge)
    if not refused:
        assert drop.dropped(where, SLUG, "not wanted", given).status == "dropped"
        return
    with pytest.raises(Refusal) as found:
        drop.dropped(where, SLUG, "not wanted", given)
    assert (found.value.code, found.value.fix) == ("merged", f"lem land merged {SLUG}")


def test_a_merge_that_lands_while_the_drop_waits_defeats_it(tmp_path: Path) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status="landing")
    forge = forge_with(where, "open")
    given = fake_ports(ModelGit(checkout=where.checkout), forge)
    outcome: list[str] = []

    def dropping() -> None:
        try:
            drop.dropped(where, SLUG, "not wanted", given)
            outcome.append("dropped")
        except Refusal as refused:
            outcome.append(refused.code)

    with steps.step(where.state, SLUG, "propose", MOMENT):
        waiting = threading.Thread(target=dropping)
        waiting.start()
        time.sleep(0.5)
        proposed(where, "main")
        forge.pulls[7] = replace(forge.pulls[7], state="merged")
        assert outcome == []
    waiting.join(timeout=30)
    assert outcome == ["merged"]
    assert read(where, SLUG).task.status == "landing"


def test_the_owners_standard_track_takes_a_ready_task_until_its_pull_request(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status="ready")
    assert moved(where, "shaping").status == "shaping"
    made(where, "other", status="ready")
    revision = read(where, "other").revision
    pull = LandingPull(number=7, url="https://github.com/o/p/pull/7", title="t")
    tasks.update(
        where.state,
        "other",
        lambda one: replace(one, landing=Landing(pull=pull)),
        revision,
    )
    with pytest.raises(Refusal) as refused:
        move.moved(where.checkout, "other", "shaping", ())
    assert "track no longer changes" in refused.value.why


def test_a_landing_that_missed_its_plan_talk_goes_back_to_planned(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path)
    made(where, SLUG, status="landing")
    assert moved(where, "planned").status == "planned"
