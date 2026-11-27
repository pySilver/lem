"""The row of each machine joined to this board: ssh reaches it, agtermctl there is new enough to
list its sessions, and its board says its agterm runs Live sessions. `agtermctl` is a stand-in
script on the stage's PATH."""

from typing import TYPE_CHECKING

import pytest

from lem.cli.doctor.peer_rows import peer_rows
from lem.cli.doctor.rows import gathered
from unit.settings.doctor.stage import Stage, named, script

if TYPE_CHECKING:
    from pathlib import Path

USAGE = 64
LISTED = '{"result": {"remote": {"host": "mini", "sessions": []}}}'


@pytest.fixture
def stage(tmp_path: Path) -> Stage:
    """A machine that joined `mini`, whose board says its agterm runs Live sessions."""
    made = Stage(tmp_path, boards={"mini": (True, "")})
    made.write("config/lem/machine.toml", "[peers]\nmini = 4537\n")
    return made


def agtermctl(
    stage: Stage, error: str = "", code: int = 0, listed: str = LISTED
) -> Path:
    """The stand-in of this Mac's agtermctl, which records its arguments and answers as
    `agtermctl --json` does: agterm's refusal on standard output with exit 1, its own parser's on
    standard error with exit 64."""
    if code == USAGE:
        answer = f"echo '{error}' >&2"
    elif code:
        answer = f'echo \'{{"ok":false,"error":"{error}"}}\''
    else:
        answer = f"echo '{listed}'"
    path = stage.bin / "agtermctl"
    path.write_text(
        f'#!/bin/sh\necho "$@" >> "{stage.root}/asked"\n{answer}\nexit {code}\n',
        encoding="utf-8",
    )
    path.chmod(0o755)
    return path


def asked(stage: Stage) -> list[str]:
    """The arguments of each call of the stand-in."""
    return (stage.root / "asked").read_text().splitlines()


def test_no_machine_joined_gives_no_row(tmp_path: Path) -> None:
    assert peer_rows(Stage(tmp_path).look()) == ()


def test_a_machine_that_ssh_reaches_in_live_sessions_is_found(stage: Stage) -> None:
    agtermctl(stage)
    row = named(gathered(stage.look()), "joined machine mini")
    assert (row.need, row.found) == ("optional", True)
    assert "ssh mini reaches it" in (row.detail or "")
    assert "zmx tree mini --json" in asked(stage)


def test_the_ssh_destination_is_the_name_lem_serve_join_kept(stage: Stage) -> None:
    agtermctl(stage)
    (row,) = peer_rows(stage.look())
    assert row.found and "ssh mini reaches it" in (row.detail or "")
    assert asked(stage) == ["zmx tree mini --json"]


@pytest.mark.parametrize(
    ("said", "code", "words"),
    [
        ("Permission denied (publickey).", 1, "ssh from this Mac"),
        ("sh: agtermctl: command not found", 1, "finds no agtermctl"),
        ("the remote agterm is too old to report its zmx endpoint", 1, "too old"),
        ("Error: Unexpected argument 'mini'", USAGE, "agterm on this Mac is too old"),
    ],
    ids=("ssh", "no-agtermctl", "too-old", "old-here"),
)
def test_what_the_machine_lacks_is_the_rows_detail_with_its_fix(
    stage: Stage, said: str, code: int, words: str
) -> None:
    agtermctl(stage, said, code)
    (row,) = peer_rows(stage.look())
    assert not row.found and words in (row.detail or "")
    assert row.without_it


def test_a_list_without_its_sessions_is_no_list(stage: Stage) -> None:
    agtermctl(stage, listed='{"ok":true,"result":{"remote":{"host":"mini"}}}')
    (row,) = peer_rows(stage.look())
    assert not row.found and "printed no answer of its form" in (row.detail or "")


def test_a_board_whose_agterm_is_not_live_names_the_mac_that_needs_it(
    stage: Stage,
) -> None:
    agtermctl(stage)
    stage.boards["mini"] = (False, "")
    (row,) = peer_rows(stage.look())
    assert not row.found
    assert "the agterm on mini does not run Live sessions" in (row.detail or "")
    assert "this Mac's agterm needs no Live sessions" in (row.detail or "")
    assert (row.without_it or "").startswith("on mini, the owner sets Restore sessions")


def test_a_board_that_does_not_answer_is_named(stage: Stage) -> None:
    agtermctl(stage)
    stage.boards["mini"] = (None, "its agterm did not say its restore mode: no reason")
    (row,) = peer_rows(stage.look())
    assert not row.found and "did not say whether its agterm runs" in (row.detail or "")
    assert "did not say its restore mode: no reason" in (row.detail or "")
    assert "lem serve peers" in (row.without_it or "")


def test_no_agtermctl_on_this_mac_is_named(stage: Stage) -> None:
    script(stage.bin / "other", "x")
    (row,) = peer_rows(stage.look())
    assert not row.found and "this Mac has no agtermctl" in (row.detail or "")
