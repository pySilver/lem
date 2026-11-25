"""The agterm adapter's slice against the `Terminal` contract, and the calls it makes, on a
stand-in for `agtermctl` (`agterm_standin.py`): never the owner's agterm."""

import shlex
from typing import TYPE_CHECKING

import pytest

from contract.agterm_standin import Standin, install
from contract.suites.terminal import TerminalContract
from lem.adapters import terminal_agterm
from lem.kernel.errors import Fault
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


def test_a_session_opens_in_the_callers_workspace_with_no_focus_at_its_end(
    tmp_path: Path,
) -> None:
    standin = install(
        tmp_path / "agterm",
        [MINE, HIS, {**MINE, "id": "S-2ND", "name": "second"}],
        ("W-MINE", "W-OTHER"),
    )
    terminal = bound(standin, AGTERM_SESSION_ID="S-MINE", AGTERM_SOCKET="/tmp/a.sock")
    line = "LEM_TASK=gift-note claude 'Read /r/session.md and follow it.'"
    made = terminal.open(Opening(name="gift-note", cwd="/r", command=(line,)))
    new = next(call for call in standin.calls() if call[:2] == ["session", "new"])
    command = new[new.index("--command") + 1]
    assert new[:11] == [
        "session",
        "new",
        "--workspace",
        "W-MINE",
        "--cwd",
        "/r",
        "--name",
        "gift-note",
        "--no-select",
        "--command",
        command,
    ]
    words = shlex.split(command)
    assert words[1:] == ["-l", "-c", line]
    assert words[0].startswith("/")
    assert ["session", "move", "--to", "bottom", "--target", made] in standin.calls()
    assert not [call for call in standin.calls() if "select" in call]
    names = [(node["name"], node["workspace"]) for node in standin.sessions()]
    assert names[-1] == ("gift-note", "W-MINE")
    listed = terminal.sessions()
    assert not isinstance(listed, Unreadable)
    assert [pane.id for pane in listed if pane.selected] == ["S-HIS"]


def test_a_named_workspace_and_a_companion_go_where_they_are_named(
    tmp_path: Path,
) -> None:
    standin = install(tmp_path / "agterm", [MINE, HIS], ("W-MINE", "W-OTHER"))
    terminal = bound(standin)
    terminal.open(Opening(name="t", cwd="/r", command=("x",), workspace="W-OTHER"))
    terminal.open(Opening(name="c", cwd="/r", command=("x",), companion_of="S-MINE"))
    news = [call for call in standin.calls() if call[:2] == ["session", "new"]]
    assert news[0][2:4] == ["--workspace", "W-OTHER"]
    assert news[1][2:4] == ["--parent", "S-MINE"]
    moves = [call for call in standin.calls() if call[:2] == ["session", "move"]]
    assert len(moves) == 1


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


def test_what_the_slice_does_not_build_says_so_by_name(tmp_path: Path) -> None:
    terminal = bound(install(tmp_path / "agterm", [MINE]))
    with pytest.raises(Fault, match=r"^show: "):
        terminal.show("S-MINE", "http://x", "overlay")
    with pytest.raises(Fault, match=r"^picker: "):
        terminal.picker(("a",), tmp_path)


def test_with_no_workspace_named_and_no_caller_agterm_chooses(tmp_path: Path) -> None:
    standin = install(tmp_path / "agterm", [MINE], ("W-MINE",))
    bound(standin, AGTERM_SESSION_ID="S-GONE").open(
        Opening(name="t", cwd="/r", command=("x",))
    )
    new = next(call for call in standin.calls() if call[:2] == ["session", "new"])
    assert "--workspace" not in new
