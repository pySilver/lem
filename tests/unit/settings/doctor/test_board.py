"""The rows of the board server, its door, its notifications and the installs of Lem it serves:
each read from the files the server keeps in Lem's home folder, with no connection."""

import os
import subprocess
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import msgspec
import pytest

from lem.board import install
from lem.board.facts import Facts, Install
from lem.cli.doctor import plugins
from lem.cli.doctor.board_rows import server_row
from lem.cli.doctor.door_rows import door_row, notifications_row
from lem.cli.doctor.installed import install_row, installed_rows
from lem.kernel.errors import Refusal
from unit.settings.doctor.stage import Stage

if TYPE_CHECKING:
    from pathlib import Path

MOMENT = datetime(2026, 11, 25, 10, 0, tzinfo=UTC)


@pytest.fixture
def stage(tmp_path: Path) -> Stage:
    """A machine of its own for each case."""
    return Stage(tmp_path)


def serving(
    stage: Stage, running: Install, *, pid: int | None = None, door: int | None = None
) -> None:
    """The facts of a server in `serve.json` of Lem's home folder."""
    facts = Facts(
        pid=os.getpid() if pid is None else pid,
        port=4636,
        url="http://127.0.0.1:4636/",
        host="mac",
        install=running,
        home=str(stage.lem_home),
        door=door,
        started=MOMENT,
    )
    stage.lem_home.mkdir(parents=True, exist_ok=True)
    (stage.lem_home / "serve.json").write_bytes(msgspec.json.encode(facts))


def ended_pid() -> int:
    """The pid of a process that has ended."""
    ran = subprocess.Popen(["/bin/sh", "-c", "exit 0"])
    ran.wait()
    return ran.pid


def test_with_no_server_the_row_gives_the_line_that_starts_one(stage: Stage) -> None:
    row = server_row(stage.look())
    assert (row.need, row.found) == ("optional", False)
    assert (row.detail or "").startswith("no server runs:")
    assert row.line is not None
    assert row.line.endswith("serve ensure")
    serving(stage, install.install_of(), pid=ended_pid())
    assert not server_row(stage.look()).found


def test_the_server_row_names_which_install_serves(stage: Stage) -> None:
    mine = install.install_of()
    serving(stage, mine)
    row = server_row(stage.look())
    assert row.found
    assert row.detail is not None
    assert row.detail.startswith(f"pid {os.getpid()} serves http://127.0.0.1:4636/")
    assert row.detail.endswith(", this install")
    serving(stage, msgspec.structs.replace(mine, stamp=1, commit=None))
    assert "the next `lem serve ensure` replaces it" in (
        server_row(stage.look()).detail or ""
    )
    other = Install(version="999.0.0", package="/elsewhere/lem")
    serving(stage, other)
    said = server_row(stage.look()).detail or ""
    assert "it runs Lem 999.0.0 from /elsewhere/lem" in said
    assert said.endswith("and leaves it as it is")


def test_a_serve_file_that_does_not_read_is_refused_with_its_fix(stage: Stage) -> None:
    stage.write("config/lem/serve.json", "{")
    with pytest.raises(Refusal, match="does not read") as raised:
        server_row(stage.look())
    assert raised.value.code == "serve-file"


def test_the_door_is_off_on_and_open_or_on_and_not_opened(stage: Stage) -> None:
    off = door_row(stage.look())
    assert (off.need, off.found, off.line) == ("optional", False, "lem serve door on")
    stage.write("config/lem/machine.toml", "[serve]\ntailscale = true\n")
    closed = door_row(stage.look())
    assert closed.found is False
    assert "no server that runs opened it" in (closed.detail or "")
    assert "lem serve ensure" in (closed.without_it or "")
    serving(stage, install.install_of(), door=4537)
    opened = door_row(stage.look())
    assert (opened.found, opened.without_it) == (True, None)
    assert (
        opened.detail
        == "the door is on, tailnet port 4537; the server that runs opened it"
    )


def test_the_notifications_row_counts_the_devices_and_the_last_push(
    stage: Stage,
) -> None:
    none = notifications_row(stage.look())
    assert (none.need, none.found, none.line) == (
        "optional",
        False,
        "lem serve push-test",
    )
    stage.write(
        "config/lem/push.json",
        '{"devices": [{"device": "iPhone"}], "last": {"at": "2026-11-25T10:00:00Z",'
        ' "results": [{"device": "iPhone", "status": 201}]}}',
    )
    row = notifications_row(stage.look())
    assert row.found
    assert row.detail == (
        "1 device (iPhone); the last push went at 2026-11-25T10:00:00Z (iPhone: 201)"
    )
    stage.write("config/lem/push.json", '{"devices": [{"device": "a"}, {}]}')
    assert (
        notifications_row(stage.look()).detail
        == "2 devices (a, ?); no push has gone yet"
    )


def entry(project: str | None, version: str, scope: str = "project") -> plugins.Install:
    """Lem's install for `project` (None: for the user), of `version`, with no folder."""
    return plugins.Install(
        key="lem@lem",
        scope=scope if project else "user",
        project=project,
        folder=None,
        version=version,
    )


def test_a_repository_whose_install_is_another_release_gets_a_row_with_the_two_lines() -> (
    None
):
    assert install_row("/r/notes", entry("/r/notes", "0.1.2"), "0.1.2") is None
    row = install_row("/r/shop", entry("/r/shop", "0.1.1"), "0.1.2")
    assert row is not None
    assert (row.name, row.need, row.found) == ("installed Lem: shop", "optional", False)
    assert row.lines == (
        "cd /r/shop && claude plugin update lem@lem --scope project",
        "lem serve ensure",
    )
    assert row.detail == (
        "/r/shop has 0.1.1 of lem@lem installed for the project, and the board server "
        "runs 0.1.2; the install is the older"
    )


def test_an_install_for_the_user_counts_where_the_repository_has_none_of_its_own(
    stage: Stage,
) -> None:
    row = install_row("/r/shop", entry(None, "0.1.2"), "0.1.1")
    assert row is not None
    assert "--scope user" in (row.line or "")
    assert (row.detail or "").endswith("the server is the older")
    unknown = install_row("/r/shop", entry(None, "0.1.2"), "a commit")
    assert unknown is not None
    assert (unknown.detail or "").endswith("which is the newer is not known")
    shop, notes = stage.repository("shop"), stage.repository("notes")
    stage.lem_home.mkdir(parents=True)
    stage.write("config/lem/workspaces.json", f'["{shop}", "{notes}"]')
    stage.plugins(
        {
            "plugins": {
                "lem@lem": [
                    {"scope": "user", "version": "0.1.0"},
                    {
                        "scope": "project",
                        "projectPath": str(notes),
                        "version": "999.0.0",
                    },
                ]
            }
        }
    )
    assert installed_rows(stage.look()) == ()
    serving(stage, Install(version="999.0.0", package="/elsewhere"))
    rows = installed_rows(stage.look())
    assert [row.name for row in rows] == ["installed Lem: shop"]
