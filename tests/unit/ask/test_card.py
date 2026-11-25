"""The public card addresses and one answer shared between the board and the overlay."""

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from typing import TYPE_CHECKING

import pytest

from fakes import records
from lem.app.sessions import acts, log
from lem.board.ask import csp, ends, keys, saved
from lem.cli import lazy
from lem.kernel import paths
from lem.kernel.errors import Refusal
from lem.model.owner import held
from lem.model.owner.looks import Look, Session
from lem.store import tasks
from unit.ask.conftest import PAGE, SLUG

if TYPE_CHECKING:
    from lem.records.questions import Answer, Question
    from unit.ask.conftest import Agterm
    from unit.board.service.given import Board

ROUTE = f"/studio/shop/tasks/{SLUG}/cards/{PAGE}"
ORIGIN = {"Origin": "http://127.0.0.1:4999", "Sec-Fetch-Site": "same-origin"}


def show(terminal: Agterm, capsys: pytest.CaptureFixture[str]) -> dict:
    assert (
        lazy.main(
            ["ask", "q", "Keep the empty cell?", "Keep", "Write a dash", "--no-wait"]
        )
        == 0
    )
    opened = json.loads(capsys.readouterr().out)["result"]
    assert opened["outcome"] == "open"
    assert opened["file"] == terminal.shown
    return opened


def posted(digest: str, option: str = "o2", *, text: str | None = None) -> dict:
    return {
        "status": "answered",
        "digest": digest,
        "answers": {
            "answer": {
                "selected": [option] if option else [],
                "labels": ["fake"],
                "text": text,
            }
        },
    }


def test_page_routes_return_the_exact_overlay_and_only_trusted_scripts(
    board: Board, terminal: Agterm, capsys: pytest.CaptureFixture[str]
) -> None:
    opened = show(terminal, capsys)
    folder = board.state / "tasks" / SLUG
    asked = saved.question(folder, PAGE)
    assert asked and asked.digest and asked.id == f"card:{PAGE}"
    assert held.card_rows(Look(record=tasks.read(board.state, SLUG))) == ()
    eyes = Look(
        record=tasks.read(board.state, SLUG),
        session=Session(live=True, since=records.MOMENT),
    )
    assert [(row.card, row.prompt) for row in held.card_rows(eyes)] == [
        (asked.id, "Keep the empty cell?")
    ]
    assert saved.metadata(folder, PAGE).prompts[0].id == "answer"
    for route in (ROUTE, ROUTE + "/"):
        with board.main() as client:
            page = client.get(route)
            head = client.head(route)
        assert page.status_code == head.status_code == 200
        assert page.content == saved.html(folder, PAGE, asked.digest)
        assert page.content.decode() == Path(opened["file"]).read_text(encoding="utf-8")
        assert head.headers["etag"] == f'"{asked.digest}"'
        assert head.content == b""
        trusted = paths.root() / "skills" / "lem-ask" / "runtime" / "ask.js"
        policy = head.headers["content-security-policy"]
        assert csp.hashed(trusted.read_bytes()) in policy
        for rule in ("form-action 'none'", "base-uri 'none'", "frame-ancestors 'self'"):
            assert rule in policy
        assert "unsafe-eval" not in policy

    with board.main() as client:
        for method in ("GET", "HEAD"):
            redirect = client.request(
                method, ROUTE + "?in=waits", follow_redirects=False
            )
            assert redirect.status_code == 302
            assert redirect.headers["location"] == ROUTE + "/?in=waits"


def test_board_answer_is_the_waiters_result_and_the_only_end(
    board: Board, terminal: Agterm, capsys: pytest.CaptureFixture[str]
) -> None:
    show(terminal, capsys)
    with board.main() as client:
        digest = client.head(ROUTE).headers["etag"].strip('"')
        taken = client.post(
            ROUTE + "/answer",
            json=posted(digest, text="For the export"),
            headers={**ORIGIN, "User-Agent": "iPhone"},
        )
        second = client.post(
            ROUTE + "/answer", json=posted(digest, "o1"), headers=ORIGIN
        )
    assert taken.status_code == 200
    assert second.status_code == 409
    assert "Write a dash" in second.json()["said"]
    assert lazy.main(["ask", "wait", PAGE, "--no-status"]) == 0
    picked = json.loads(capsys.readouterr().out)["result"]
    assert picked["outcome"] == "answered"
    assert (picked["from"], picked["via"], picked["device"]) == (
        "board",
        "local",
        "phone",
    )
    assert picked["answers"]["answer"]["labels"] == ["Write a dash"]
    assert picked["answers"]["answer"]["text"] == "For the export"
    assert terminal.shown is None
    record = tasks.read(board.state, SLUG)
    assert [row.act for row in record.journal if hasattr(row, "act")] == [
        "card.asked",
        "card.answered",
    ]
    assert not [call for call in terminal.calls if "submit" in call]


def test_an_overlay_answer_already_at_the_mac_wins(
    board: Board, terminal: Agterm, capsys: pytest.CaptureFixture[str]
) -> None:
    show(terminal, capsys)
    terminal.outcome = "submitted"
    terminal.payload = json.dumps(posted("unused", "o1"))
    with board.main() as client:
        digest = client.head(ROUTE).headers["etag"].strip('"')
        assert (
            client.post(
                ROUTE + "/answer", json=posted(digest), headers=ORIGIN
            ).status_code
            == 409
        )
    assert tasks.read(board.state, SLUG).task.questions[0].answer is None
    assert lazy.main(["ask", "wait", PAGE, "--no-status"]) == 0
    assert json.loads(capsys.readouterr().out)["result"]["from"] == "session"
    assert tasks.read(board.state, SLUG).task.questions[0].answer is not None


def test_bad_answers_and_an_older_session_leave_the_card_open(
    board: Board, terminal: Agterm, capsys: pytest.CaptureFixture[str]
) -> None:
    show(terminal, capsys)
    with board.main() as client:
        digest = client.head(ROUTE).headers["etag"].strip('"')
        for wire, status in (
            (posted("changed"), 409),
            (posted(digest, "unknown"), 422),
            (posted(digest, "", text="Can we do both?"), 422),
            ({"status": "chat", "digest": digest}, 422),
            ({"status": "dismissed"}, 204),
            ([], 400),
        ):
            assert (
                client.post(ROUTE + "/answer", json=wire, headers=ORIGIN).status_code
                == status
            )
        assert (
            client.post(
                ROUTE + "/answer",
                json=posted(digest),
                headers={"Origin": "https://elsewhere.test"},
            ).status_code
            == 403
        )
        deep = (
            b'{"status":"answered","answers":{"answer":{"extra":'
            + b"[" * 1200
            + b"]" * 1200
            + b"}}}"
        )
        assert (
            client.post(ROUTE + "/answer", content=deep, headers=ORIGIN).status_code
            == 400
        )
        log.append(
            board.state / "tasks" / SLUG,
            acts.Open(
                at=records.MOMENT, session="S2", name=SLUG, phase="shape", why="open"
            ),
        )
        assert (
            client.post(
                ROUTE + "/answer", json=posted(digest), headers=ORIGIN
            ).status_code
            == 409
        )
    assert tasks.read(board.state, SLUG).task.questions[0].answer is None


def test_two_board_posts_take_one_answer(
    board: Board,
    terminal: Agterm,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    show(terminal, capsys)
    with board.main() as client:
        digest = client.head(ROUTE).headers["etag"].strip('"')

    ready = Barrier(2, timeout=5)
    finish = ends.finish

    def finish_together(
        folder: Path, asked: Question, proposed: Answer, payload: ends.Payload
    ) -> tuple[bool, Answer]:
        ready.wait()
        return finish(folder, asked, proposed, payload)

    monkeypatch.setattr(ends, "finish", finish_together)
    monkeypatch.setattr(ends, "time_of_answer", lambda: records.MOMENT)

    def answer(option: str) -> int:
        with board.main() as client:
            return client.post(
                ROUTE + "/answer", json=posted(digest, option), headers=ORIGIN
            ).status_code

    with ThreadPoolExecutor() as pool:
        assert sorted(pool.map(answer, ("o1", "o2"))) == [200, 409]
    row = tasks.read(board.state, SLUG)
    assert row.revision == 3
    receipts = (board.state / "tasks" / SLUG / "cards" / PAGE).glob("answer-*.json")
    assert len(list(receipts)) == 2


def test_unreadable_terminal_leaves_the_card_open(
    board: Board, terminal: Agterm, capsys: pytest.CaptureFixture[str]
) -> None:
    show(terminal, capsys)
    terminal.silent = True
    with board.main() as client:
        digest = client.head(ROUTE).headers["etag"].strip('"')
        got = client.post(ROUTE + "/answer", json=posted(digest), headers=ORIGIN)
    assert got.status_code == 409
    assert "no socket" in got.json()["said"]
    assert tasks.read(board.state, SLUG).task.questions[0].answer is None


def test_a_page_id_is_never_a_path(board: Board) -> None:
    folder = board.state / "tasks" / SLUG
    with pytest.raises(Refusal, match="no page id"):
        keys.copies(folder, "../another-card")
    with board.main() as client:
        assert client.get(ROUTE + "-missing/").status_code == 404
