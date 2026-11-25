"""The owner's acts on the board, on a real repository and `LocalForge`: the board server's app
through Starlette's test client over the workspace of `tests/journeys/test_skeleton.py`, whose
commands the agents run.

His approval of the merge (amendment A4: the button says Approve) lands the pull request as his
own word through the board; another commit merges nothing; on a base another merge moved, his
approval stands, as the landing keeps it, and a second press starts no merge call. A new task
from his words opens its record and its session.
"""

import os
import time
from typing import TYPE_CHECKING
from urllib.parse import parse_qs, urlsplit

from starlette.testclient import TestClient

from fakes.records import MOMENT
from fakes.terminal import FakeTerminal
from journeys.test_skeleton import SLUG, World, made, upto
from lem.app import wiring
from lem.board import app, install, machine, workspaces
from lem.board.acts.notes import NOTES
from lem.board.facts import Facts
from lem.kernel import paths
from lem.ports.place import Place
from lem.ports.terminal import Pane
from lem.store import tasks

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

    from lem.board.acts.notes import Note

PORT = 4998
ORIGIN = f"http://127.0.0.1:{PORT}"
SENT = {"origin": ORIGIN, "sec-fetch-site": "same-origin"}


class Board:
    """The board's app over the journey's workspace."""

    def __init__(self, world: World) -> None:
        """Put the workspace on the list of Lem's home folder, and make the server's app."""
        home = paths.home(os.environ)
        workspaces.noted(home, world.checkout)
        facts = Facts(
            pid=os.getpid(),
            port=PORT,
            url=f"{ORIGIN}/",
            host=machine.machine_name(),
            install=install.install_of(),
            home=str(home),
            started=MOMENT,
        )
        served = app.made(facts, home=home, listen="127.0.0.1", stop=lambda: None)
        self.client = TestClient(served, base_url=ORIGIN, client=("127.0.0.1", 50000))
        name = workspaces.name_of(home, facts.host, world.checkout)
        self.base = f"/{facts.host}/{name}"
        self.world = world

    def post(self, path: str, fields: dict[str, str]) -> str:
        """A form of the board's own page; the token of the note its 303 names."""
        answer = self.client.post(
            f"{self.base}{path}", data=fields, headers=SENT, follow_redirects=False
        )
        assert answer.status_code == 303, answer.text
        return parse_qs(urlsplit(answer.headers["location"]).query)["note"][0]

    def settled(self, token: str) -> Note:
        """The note of `token` once the task's merge no longer runs."""
        key = (str(self.world.checkout), SLUG)
        deadline = time.monotonic() + 60
        while NOTES.running(key) is not None and time.monotonic() < deadline:
            time.sleep(0.05)
        note = NOTES.get(token)
        assert note is not None
        return note


def proposed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> tuple[World, Board, str]:
    """The journey up to the merge agent's read of the open pull request, its board, and the
    tip it proposed."""
    world = made(tmp_path, monkeypatch)
    upto(capsys, world, "merge-review")
    capsys.readouterr()
    tip = world.record()["landing"]["proposed"]["tip"]
    return world, Board(world), tip


def test_his_approval_from_the_confirm_step_lands_the_pull_request_as_his_word(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world, board, tip = proposed(tmp_path, monkeypatch, capsys)
    stale = board.post(f"/tasks/{SLUG}/merge", {"confirm": "yes", "tip": "f" * 40})
    refused = NOTES.get(stale)
    assert refused is not None
    assert refused.state == "refused"
    assert world.forge.merge_calls == []
    token = board.post(f"/tasks/{SLUG}/merge", {"confirm": "yes", "tip": tip})
    note = board.settled(token)
    assert note.state == "done", note.said
    assert note.said.startswith("Merged: pull request #")
    landing = world.record()["landing"]
    assert (landing["merged"]["by"], landing["merged"]["via"]) == ("owner", "board")
    assert len(world.forge.merge_calls) == 1
    acts = [one for one in world.record()["journal"] if one["kind"] == "owner-act"]
    assert [(one["act"], one["option"], one["via"]) for one in acts] == [
        ("merge", tip, "local")
    ]


def test_on_a_base_another_merge_moved_his_approval_stands_and_a_second_press_merges_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world, board, tip = proposed(tmp_path, monkeypatch, capsys)
    world.repo.outside_commit("main", {"OTHER.md": b"another task's merge\n"})
    token = board.post(f"/tasks/{SLUG}/merge", {"confirm": "yes", "tip": tip})
    note = board.settled(token)
    assert note.state == "stands", note.said
    assert note.said.startswith("Your approval of pull request #")
    landing = world.record()["landing"]
    assert landing["standing"]["tip"] == tip
    assert (landing["refused"]["kind"], landing["refused"]["by"]) == ("base", "owner")
    assert world.forge.merge_calls == []
    again = NOTES.get(
        board.post(f"/tasks/{SLUG}/merge", {"confirm": "yes", "tip": tip})
    )
    assert again is not None
    assert again.state == "stands"
    assert world.forge.merge_calls == []


def test_a_new_task_from_his_words_opens_its_record_and_its_session(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    world = made(tmp_path, monkeypatch)
    board = Board(world)
    monkeypatch.setenv("AGTERM_SESSION_ID", "S-MINE")
    place = Place(checkout=world.checkout, home=tmp_path, environ={})
    terminal = wiring.bound(place).terminal
    assert isinstance(terminal, FakeTerminal)
    terminal.panes["S-MINE"] = Pane(id="S-MINE", name="main", workspace="W-1")
    token = board.post("/start", {"words": "The README says receive on every page"})
    note = NOTES.get(token)
    assert note is not None
    assert note.state == "done", note.said
    slug = "the-readme-says-receive-on"
    record = tasks.read(world.checkout / ".lem" / "state", slug)
    assert record.task.ask == "The README says receive on every page"
    assert terminal.openings[-1].name == slug
