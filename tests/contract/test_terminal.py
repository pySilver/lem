"""The agterm adapter against the whole `Terminal` contract, and the calls it makes, on a stand-in
for `agtermctl` (`agterm_standin.py`) on a PATH of the stand-ins and the system's folders alone,
with no socket, window or session of the owner's agterm inherited."""

import subprocess
from typing import TYPE_CHECKING

import pytest

from contract.agterm_standin import Standin, install
from contract.suites.terminal import TerminalContract
from lem.adapters import terminal_agterm
from lem.ports.faults import Unanswered
from lem.ports.place import Place
from lem.ports.terminal import Opening, Unreadable

if TYPE_CHECKING:
    from pathlib import Path

HIS = {"id": "S-HIS", "name": "notes", "workspace": "W-OTHER", "active": True}
MINE = {"id": "S-MINE", "name": "main", "workspace": "W-MINE"}


def bound(standin: Standin, **environ: str) -> terminal_agterm.AgtermTerminal:
    """The adapter on the stand-in, as `lem` binds it for a place."""
    place = Place(
        checkout=standin.folder,
        home=standin.folder / "home",
        environ=standin.environ(**environ),
    )
    return terminal_agterm.bind(place)


class TestAgtermTerminal(TerminalContract):
    def terminal(self, folder: Path) -> terminal_agterm.AgtermTerminal:
        return bound(install(folder / "agterm"))


def test_a_named_workspace_and_a_companion_go_where_they_are_named(
    tmp_path: Path,
) -> None:
    standin = install(
        tmp_path / "agterm", [MINE, HIS], ("W-MINE", "W-OTHER", "W-EMPTY")
    )
    terminal = bound(standin)
    terminal.open(Opening(name="t", cwd="/r", command=("x",), workspace="W-OTHER"))
    terminal.open(Opening(name="e", cwd="/r", command=("x",), workspace="W-EMPTY"))
    terminal.open(Opening(name="c", cwd="/r", command=("x",), companion_of="S-MINE"))
    news = [call for call in standin.calls() if call[:2] == ["session", "new"]]
    # agterm refuses --after beside --workspace: the anchor carries its own workspace
    assert news[0][2:4] == ["--after", "S-HIS"]
    assert "--workspace" not in news[0]
    assert news[1][2:4] == ["--workspace", "W-EMPTY"]
    assert news[2][2:4] == ["--parent", "S-MINE"]
    placed = {node["name"]: node["workspace"] for node in standin.sessions()}
    assert (placed["t"], placed["e"], placed["c"]) == ("W-OTHER", "W-EMPTY", "W-MINE")
    assert not [call for call in standin.calls() if call[:2] == ["session", "move"]]


def test_the_stand_in_refuses_what_agtermctl_refuses(tmp_path: Path) -> None:
    standin = install(tmp_path / "agterm", [MINE])
    environ = standin.environ()
    refused = (
        ["session", "new", "--workspace", "W-MINE", "--after", "S-MINE"],
        ["session", "new", "--parent", "S-MINE", "--workspace", "W-MINE"],
        ["session", "status", "waiting", "--target", "S-MINE"],
        ["msg", "send", "x", "--to", "S-MINE:left", "--window", "W1"],
        ["session", "rename", "--target", "S-MINE"],
        ["session", "overlay", "open", "--html", "x.html", "--browse"],
        ["tree", "--all"],
    )
    for words in refused:
        ran = subprocess.run(
            ["agtermctl", *words],
            env=environ,
            capture_output=True,
            text=True,
            check=False,
        )
        assert ran.returncode == 64, words


def test_a_tree_that_does_not_read_is_unreadable_never_empty(tmp_path: Path) -> None:
    standin = install(tmp_path / "agterm", [MINE])
    standin.change(fail="tree")
    assert bound(standin).sessions() == Unreadable(why="agterm does not answer")
    gone = Standin(tmp_path / "nowhere")
    listed = bound(gone).sessions()
    assert isinstance(listed, Unreadable)
    assert "not on the PATH" in listed.why
    with pytest.raises(Unanswered, match="not on the PATH"):
        bound(gone).tell("S-1", "lem: gift-note owner")


def test_a_line_goes_to_the_left_pane_and_a_mark_is_agterms_glyph(
    tmp_path: Path,
) -> None:
    standin = install(tmp_path / "agterm", [MINE])
    terminal = bound(standin)
    terminal.tell("S-MINE", "lem: gift-note merged")
    terminal.mark("S-MINE", "waiting")
    assert ["msg", "send", "lem: gift-note merged", "--to", "S-MINE:left"] in (
        standin.calls()
    )
    assert standin.sessions()[0]["status"] == "blocked"


def test_a_close_is_undoable(tmp_path: Path) -> None:
    standin = install(tmp_path / "agterm", [MINE])
    bound(standin).close("S-MINE", when_unselected=True)
    assert ["session", "close", "--target", "S-MINE", "--undoable"] in standin.calls()


def test_every_call_names_the_socket_and_the_window_but_a_line_names_no_window(
    tmp_path: Path,
) -> None:
    standin = install(tmp_path / "agterm", [MINE])
    terminal = bound(standin, AGTERM_SOCKET="/tmp/a.sock", AGT_WINDOW_ID="W9")
    terminal.mark("S-MINE", "working")
    terminal.tell("S-MINE", "lem: gift-note queue")
    status = next(call for call in standin.raw() if call[:2] == ["session", "status"])
    send = next(call for call in standin.raw() if call[:2] == ["msg", "send"])
    assert status[-4:] == ["--socket", "/tmp/a.sock", "--window", "W9"]
    assert send[-2:] == ["--socket", "/tmp/a.sock"]


def test_a_session_is_found_in_no_regard_to_case_and_renamed(tmp_path: Path) -> None:
    standin = install(tmp_path / "agterm", [MINE])
    bound(standin).rename("s-mine", "gift-note · handed off")
    assert standin.sessions()[0]["name"] == "gift-note · handed off"
    with pytest.raises(Unanswered, match="no session S-GONE"):
        bound(standin).rename("S-GONE", "x")


def test_the_foreground_of_each_main_pane_is_its_programs_words(
    tmp_path: Path,
) -> None:
    standin = install(
        tmp_path / "agterm",
        [
            {**MINE, "foreground": ["/bin/zsh", "-l", "-c", "claude x"]},
            {**HIS, "foreground": None},
            {"id": "S-NEW", "name": "n", "workspace": "W-MINE", "realized": False},
        ],
        ("W-MINE", "W-OTHER"),
    )
    assert bound(standin).foregrounds() == {
        "S-MINE": ("/bin/zsh", "-l", "-c", "claude x"),
        "S-HIS": (),
        "S-NEW": None,
    }


def test_a_line_waits_in_the_mailbox_until_the_pane_takes_it(tmp_path: Path) -> None:
    standin = install(
        tmp_path / "agterm",
        [{**MINE, "surfaces": [{"kind": "left", "paneID": "P-7"}]}],
    )
    terminal = bound(standin)
    assert not terminal.waiting("S-MINE", "lem: gift-note merged")
    terminal.tell("S-MINE", "lem: gift-note merged")
    assert terminal.waiting("S-MINE", "lem: gift-note merged")
    read = next(call for call in standin.calls() if call[:2] == ["msg", "read"])
    assert read[2:4] == ["--as", "S-MINE:P-7"]


def test_a_page_shows_beside_the_session_or_over_it_and_selects_nothing(
    tmp_path: Path,
) -> None:
    standin = install(tmp_path / "agterm", [MINE])
    terminal = bound(standin)
    for mode in ("companion", "overlay", "browser"):
        terminal.show("S-MINE", "http://127.0.0.1:4600/board", mode)
    assert standin.sessions()[0]["pages"] == [
        ["--url", "http://127.0.0.1:4600/board", "--js", "--companion"],
        ["--url", "http://127.0.0.1:4600/board", "--js"],
        ["--url", "http://127.0.0.1:4600/board", "--js", "--browse", "--navigation"],
    ]
    assert not [call for call in standin.calls() if call[:2] == ["session", "select"]]


def test_the_picker_gives_the_row_he_chose_or_none_when_he_closed_it(
    tmp_path: Path,
) -> None:
    standin = install(tmp_path / "agterm", [MINE])
    terminal = bound(standin)
    assert terminal.picker(("gift-note", "fix-the-login"), tmp_path) is None
    standin.change(pick="fix-the-login")
    assert terminal.picker(("gift-note", "fix-the-login"), tmp_path) == "fix-the-login"
    standin.change(pick="no-such-row")
    with pytest.raises(Unanswered, match="a row it was not given"):
        terminal.picker(("gift-note",), tmp_path)


def test_the_owners_select_is_the_one_call_that_selects(tmp_path: Path) -> None:
    standin = install(tmp_path / "agterm", [MINE, HIS], ("W-MINE", "W-OTHER"))
    bound(standin).select("S-MINE")
    assert [node["id"] for node in standin.sessions() if node.get("active")] == [
        "S-MINE"
    ]


@pytest.mark.parametrize("name", ["AGTERM_SESSION_ID", "AGT_SESSION_ID"])
def test_the_caller_is_the_session_its_panes_environment_names(
    tmp_path: Path, name: str
) -> None:
    standin = install(tmp_path / "agterm", [MINE])
    assert bound(standin, **{name: "S-MINE"}).here() == "S-MINE"
    assert bound(standin, **{name: " "}).here() is None
