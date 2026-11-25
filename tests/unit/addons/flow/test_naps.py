"""`lem nap may`: the naps' one switch, the start it writes down, the nap that runs, the gap
between two, the local file's no, and the folder of naps it never prunes (`main`:
tests/lem-naps.sh, `project.cmd_may_nap`). No agent naps here: a nap's folder is written by
hand, the way a nap's agent leaves it."""

import datetime as dt
import json
from typing import TYPE_CHECKING

import pytest

from fakes.command import lem
from fakes.repo import RealRepo, run_git
from lem.addons.naps import folder as naps
from lem.addons.naps import may
from lem.kernel import clock
from lem.kernel.errors import Refusal
from unit.task.spaces import refusal, result, workspace

if TYPE_CHECKING:
    from pathlib import Path

ON = '[branch]\nbase = "main"\n[naps]\non = true\n'
OFF = '[branch]\nbase = "main"\n[naps]\non = false\n'
NOW = dt.datetime(2026, 11, 25, 12, 0, tzinfo=dt.UTC)
TEAM = (True, ".lem/settings.toml")


def woke(state: Path, name: str) -> None:
    """A nap's folder as its agent leaves it: its dream, a thing it made, its waking note."""
    folder = state / naps.NAPS / name
    folder.mkdir(parents=True)
    (folder / "dream.md").write_text("# A dream\n\nA field.\n")
    (folder / "thing.txt").write_text("x\n")
    (folder / naps.WAKING).write_text("# Waking\n\nNothing.\n")


def ago(hours: float) -> str:
    """The folder minute of a nap that started `hours` before NOW."""
    return (NOW - dt.timedelta(hours=hours)).strftime(naps.TIME)


def test_with_the_naps_off_it_is_a_no_that_writes_nothing(tmp_path: Path) -> None:
    where = workspace(tmp_path, OFF)
    ran = lem("nap", "may", cwd=tmp_path)
    said = result(ran)
    assert (ran.code, said["may"], said["time"]) == (0, False, None)
    assert said["why"] == "the naps are off (naps.on = false in .lem/settings.toml)"
    assert said["folder"] == str(where.state / "naps")
    assert not (where.state / "naps").exists()
    assert lem("nap", "may", "--asked", cwd=tmp_path).code == 2


def test_with_the_naps_on_it_starts_one_at_the_clocks_minute_and_a_second_call_is_a_no(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path, ON)
    before = clock.now()
    started = result(lem("nap", "may", cwd=tmp_path))
    after = clock.now()
    minutes = {moment.strftime(naps.TIME) for moment in (before, after)}
    assert (started["may"], started["why"]) == (True, "there is no nap yet")
    assert started["time"] in minutes
    record = json.loads((where.state / "naps" / naps.ASLEEP).read_text())
    assert record["time"] == started["time"]
    again = result(lem("nap", "may", cwd=tmp_path))
    assert again["may"] is False
    assert again["why"].startswith("a nap runs since ")


def test_a_nap_that_wrote_its_waking_note_runs_no_more_and_the_gap_holds(
    tmp_path: Path,
) -> None:
    state = workspace(tmp_path, ON).state
    started = may.may_nap(state, TEAM, NOW)
    woke(state, f"{started.time}-a-field")
    later = may.may_nap(state, TEAM, NOW + dt.timedelta(hours=1))
    assert later.may is False
    assert later.why == (
        "the newest nap started 1.0 hours ago, and 6 hours pass between two naps"
    )
    assert later.newest == f"{started.time}-a-field"


def test_a_start_with_no_waking_note_runs_an_hour_at_most_and_counts_for_the_gap(
    tmp_path: Path,
) -> None:
    state = workspace(tmp_path, ON).state
    since = NOW - dt.timedelta(hours=2)
    naps.fell_asleep(state / naps.NAPS, naps.Asleep(since=since, time=ago(2)))
    stale = may.may_nap(state, TEAM, NOW)
    assert (stale.may, stale.why) == (
        False,
        "the newest nap started 2.0 hours ago, and 6 hours pass between two naps",
    )
    (state / naps.NAPS / naps.ASLEEP).unlink()
    woke(state, f"{ago(7)}-long-ago")
    due = may.may_nap(state, TEAM, NOW)
    assert (due.may, due.why, due.time) == (
        True,
        "the newest nap started 7.0 hours ago",
        NOW.strftime(naps.TIME),
    )


def test_it_removes_no_nap_and_refuses_a_broken_record_of_a_start(
    tmp_path: Path,
) -> None:
    state = workspace(tmp_path, ON).state
    woke(state, "2026-01-01-0000-the-first")
    (state / naps.NAPS / "not-a-nap").mkdir()
    link = state / naps.NAPS / "2026-01-02-0000-a-link"
    link.symlink_to(state / naps.NAPS / "2026-01-01-0000-the-first")
    found = may.may_nap(state, TEAM, NOW)
    assert found.newest == "2026-01-01-0000-the-first"
    assert sorted(path.name for path in (state / naps.NAPS).iterdir()) == [
        naps.ASLEEP,
        "2026-01-01-0000-the-first",
        "2026-01-02-0000-a-link",
        "not-a-nap",
    ]
    (state / naps.NAPS / naps.ASLEEP).write_text("not json\n")
    with pytest.raises(Refusal) as caught:
        may.may_nap(state, TEAM, NOW)
    assert caught.value.code == "asleep-record"
    assert f"{state / naps.NAPS / naps.ASLEEP} is not the record" in caught.value.why


def test_the_local_file_says_no_for_its_person_and_a_yes_there_is_refused(
    tmp_path: Path,
) -> None:
    where = workspace(tmp_path, ON)
    local = tmp_path / ".lem" / "settings.local.toml"
    local.write_text("[naps]\non = false\n")
    said = result(lem("nap", "may", cwd=tmp_path))
    assert (said["may"], said["why"]) == (
        False,
        "the naps are off on this machine (naps.on = false in .lem/settings.local.toml)",
    )
    assert not (where.state / "naps" / naps.ASLEEP).exists()
    local.write_text("[naps]\non = true\n")
    refused = refusal(lem("nap", "may", cwd=tmp_path))
    assert "naps.on" in refused["why"] + refused["fix"]


def test_in_a_tasks_worktree_the_naps_table_is_the_main_checkouts_and_a_nap_leaves_git_clean(
    tmp_path: Path,
) -> None:
    repo = RealRepo.init(tmp_path / "repo", {".lem/settings.toml": OFF.encode()})
    checkout = repo.checkout
    tree = tmp_path / "naps-on"
    run_git(checkout, "worktree", "add", "--quiet", "-b", "feat/naps-on", str(tree))
    (tree / ".lem" / "settings.toml").write_text(ON)
    run_git(tree, "commit", "--quiet", "-am", "chore: the naps on")
    said = result(lem("nap", "may", cwd=tree))
    assert said["may"] is False
    assert said["folder"] == str(checkout.resolve() / ".lem" / "state" / "naps")
    run_git(tree, "checkout", "--quiet", "--detach")
    (checkout / ".lem" / "settings.toml").write_text(ON)
    run_git(checkout, "commit", "--quiet", "-am", "chore: the naps on for everybody")
    assert result(lem("nap", "may", cwd=checkout))["may"] is True
    woke(checkout / ".lem" / "state", f"{ago(0)}-a-field")
    assert run_git(checkout, "status", "--porcelain", "--untracked-files=all") == ""
