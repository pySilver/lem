"""A task's session of another Mac shown in this Mac's agterm, on a stand-in for `agtermctl` on each
side (`agterm_standin.py`), in agterm's own reply shapes: the row already attached is selected in
its window, else the session is attached with its companions, and each failure of either side is
a refusal that names its fix."""

import asyncio
import subprocess
from types import SimpleNamespace
from typing import TYPE_CHECKING

import httpx
import pytest
from starlette.applications import Starlette

from contract.agterm_standin import Standin, install
from lem.addons.peers import attaching, group_said, origin, routes
from lem.cli.doctor import peer_look
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from pathlib import Path

PEER = "mini"
SESSION = "6F1C2A30-0000-4000-8000-000000000007"
TALK_ID = "6F1C2A30-0000-4000-8000-000000000009"
TASK = {"id": SESSION, "name": "refund-line", "workspace": "W-MINI"}
TALK = {"id": TALK_ID, "name": "talk", "workspace": "W-MINI", "parent": SESSION}
OTHER = {
    "id": "6F1C2A30-0000-4000-8000-000000000008",
    "name": "notes",
    "workspace": "W-MINI",
}
MINE = {"id": "L-1", "name": "main", "workspace": "W-BOOK"}


def macs(tmp_path: Path) -> tuple[Standin, Standin]:
    """The stand-in of the Mac where the owner works, which reaches the other one as `mini`."""
    far = install(tmp_path / "mini", [TASK, TALK, OTHER])
    here = install(tmp_path / "book", [MINE])
    here.change(hosts={PEER: str(far.folder)})
    return here, far


def shown(here: Standin, session: str = SESSION, host: str = PEER) -> group_said.Shown:
    """The steps in this Mac's agterm for the session of `mini`."""
    return attaching.shown(here.environ(), PEER, host, session)


def zmx(here: Standin) -> list[list[str]]:
    """The calls that reached another Mac or attached a session of it."""
    return [call for call in here.calls() if call[0] == "zmx"]


def test_a_session_is_attached_with_its_companions_then_selected(
    tmp_path: Path,
) -> None:
    here, far = macs(tmp_path)
    assert shown(here, SESSION.lower()) == group_said.Shown(
        said="Opened the session of mini on this Mac."
    )
    assert zmx(here) == [
        ["zmx", "tree", PEER, "--json"],
        ["zmx", "attach", PEER, SESSION, "--companions", "--json"],
    ]
    assert here.calls()[-1] == ["session", "select", "--target", "R-1"]
    rows = {row["id"]: row for row in here.sessions()}
    assert rows["R-1"]["remoteSessionID"] == SESSION and rows["R-1"]["active"]
    assert rows["R-1-C1"]["parent"] == "R-1"
    assert rows["R-1-C1"]["remoteSessionID"] == TALK_ID
    assert [row["id"] for row in far.sessions()] == [SESSION, TALK_ID, OTHER["id"]]


def test_a_row_already_attached_in_another_window_is_selected_there(
    tmp_path: Path,
) -> None:
    here, _ = macs(tmp_path)
    attached = {
        "id": "R-9",
        "name": "refund-line",
        "workspace": "W-BOOK",
        "window": "W2",
    }
    attached |= {"remoteHost": PEER, "remoteSessionID": SESSION}
    here.change(windows=["W1", "W2"], sessions=[MINE, attached])
    assert shown(here).said == group_said.SWITCHED
    assert zmx(here) == []
    assert here.raw()[-1][:6] == [
        "session",
        "select",
        "--target",
        "R-9",
        "--window",
        "W2",
    ]
    assert {row["id"] for row in here.sessions() if row.get("active")} == {"R-9"}


def refused(here: Standin, session: str = SESSION, host: str = PEER) -> Refusal:
    """The refusal of the steps; no row is attached."""
    before = len(here.sessions())
    with pytest.raises(Refusal) as caught:
        shown(here, session, host)
    assert len(here.sessions()) == before
    assert caught.value.fix
    return caught.value


def test_a_row_from_an_agterm_that_names_no_origin_stops_the_attach(
    tmp_path: Path,
) -> None:
    here, _ = macs(tmp_path)
    older = {"id": "R-9", "name": "x", "workspace": "W-BOOK", "remoteHost": PEER}
    here.change(sessions=[MINE, older])
    found = refused(here)
    assert found.code == "agterm-old" and "0.42.0" in found.why
    assert zmx(here) == []


def test_a_session_that_is_gone_on_the_far_mac_is_refused(tmp_path: Path) -> None:
    here, far = macs(tmp_path)
    assert (
        refused(here, "6F1C2A30-0000-4000-8000-000000000404").code
        == "peer-session-gone"
    )
    far.change(gone_at_attach=True)
    assert refused(here).code == "peer-session-gone"


@pytest.mark.parametrize(
    ("far_mac", "code"),
    [
        ({"agtermctl": False}, "peer-agtermctl"),
        ({"zmx_tree": False}, "peer-agterm-old"),
        ({"restore": "rerun"}, "peer-session-gone"),
        (
            {"ssh_says": ["kex_exchange_identification: Connection reset by peer"]},
            "peer-ssh",
        ),
    ],
    ids=("no-agtermctl", "too-old", "not-live", "reset"),
)
def test_what_the_far_mac_lacks_is_refused_by_name(
    tmp_path: Path, far_mac: dict[str, object], code: str
) -> None:
    here, far = macs(tmp_path)
    far.change(**far_mac)
    assert refused(here).code == code
    assert not [call for call in zmx(here) if call[1] == "attach"]


def test_a_destination_ssh_does_not_reach_is_refused_with_the_alias_that_names_another(
    tmp_path: Path,
) -> None:
    here, _ = macs(tmp_path)
    found = refused(here, host="nowhere")
    assert found.code == "peer-ssh"
    assert "`Host nowhere` alias in ~/.ssh/config" in found.fix


@pytest.mark.parametrize(
    "old", ({"group_attach": False}, {"old_cli": True}), ids=("app", "cli")
)
def test_this_macs_agterm_too_old_for_companions_is_refused(
    tmp_path: Path, old: dict[str, object]
) -> None:
    here, _ = macs(tmp_path)
    here.change(**old)
    found = refused(here)
    assert found.code == "agterm-old" and "with its companions" in found.why


def test_a_group_kept_in_part_says_what_did_not_attach(tmp_path: Path) -> None:
    here, far = macs(tmp_path)
    far.change(gone_members=[TALK_ID])
    seen = shown(here)
    assert seen.said == "Opened the session of mini on this Mac."
    assert seen.notice is not None
    assert (
        f"Not attached: {TALK_ID}" in seen.notice
        and "talk (unavailable on mini)" in seen.notice
    )
    assert here.calls()[-1] == ["session", "select", "--target", "R-1"]


def test_an_origin_that_names_no_companions_gives_a_notice(tmp_path: Path) -> None:
    here, far = macs(tmp_path)
    far.change(companions_known=False)
    seen = shown(here)
    assert seen.notice is not None and "does not say which companions" in seen.notice
    assert any(row.get("parent") == "R-1" for row in here.sessions())


def test_the_far_board_says_whether_its_agterm_runs_live_sessions(
    tmp_path: Path,
) -> None:
    _, far = macs(tmp_path)
    assert origin.live(far.environ()) == (True, "")
    far.change(restore="rerun")
    assert origin.live(far.environ()) == (False, "")
    far.change(fail="restore")
    running, why = origin.live(far.environ())
    assert running is None and "agterm does not answer" in why
    assert far.calls()[-1] == ["restore", "mode", "--json"]


def test_the_doctor_reads_the_boards_answer_in_agterms_real_shape(
    tmp_path: Path,
) -> None:
    _, far = macs(tmp_path)
    board = Starlette(routes=list(routes.ROUTES))
    board.state.environ = far.environ()
    board.state.home = tmp_path / "mini-home"
    board.state.facts = SimpleNamespace(host=PEER, door=None)

    async def asked() -> bytes:
        transport = httpx.ASGITransport(app=board)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://x"
        ) as client:
            return (await client.get(peer_look.AGTERM_PATH)).content

    assert peer_look.decoded(asyncio.run(asked())).live is True
    far.change(restore="none")
    assert peer_look.decoded(asyncio.run(asked())).live is False


def test_the_stand_in_refuses_the_remote_calls_agtermctl_refuses(
    tmp_path: Path,
) -> None:
    here, _ = macs(tmp_path)
    for words in (
        ["zmx", "tree", PEER, "--window", "W1"],
        ["zmx", "attach", PEER],
        ["restore", "mode", "--window", "W1"],
        ["window", "list", "--window", "W1"],
    ):
        ran = subprocess.run(
            ["agtermctl", *words],
            env=here.environ(),
            capture_output=True,
            text=True,
            check=False,
        )
        assert ran.returncode == 64, words
