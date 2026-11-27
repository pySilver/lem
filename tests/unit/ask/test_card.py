"""The public card addresses and one answer shared between the board and the overlay."""

import json
import sys
from base64 import b64encode
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path
from subprocess import CompletedProcess
from threading import Barrier
from typing import TYPE_CHECKING

import pytest

from fakes import records
from lem.adapters import agterm_ctl
from lem.app.asking import ends, form, keys, page_close, saved
from lem.app.asking.scripts import hashed
from lem.app.owner import cards
from lem.app.sessions import acts, log
from lem.cli import lazy
from lem.cli.ask import card_wait, waiting
from lem.kernel import paths
from lem.kernel.errors import Refusal
from lem.model.owner import held
from lem.model.owner.looks import Look, Session
from lem.records.questions import Answer
from lem.store import tasks
from unit.ask.conftest import PAGE, SESSION, SLUG

if TYPE_CHECKING:
    from lem.cli.ask.context import Context
    from lem.records.questions import Question
    from unit.ask.conftest import Agterm
    from unit.board.service.given import Board

ROUTE = f"/studio/shop/tasks/{SLUG}/cards/{PAGE}"
ORIGIN = {"Origin": "http://127.0.0.1:4999", "Sec-Fetch-Site": "same-origin"}
REAL_CTL = agterm_ctl.ctl
CLOSE = ("session", "overlay", "close", "--target", SESSION, "--json")


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
    assert "board" not in opened
    folder = board.state / "tasks" / SLUG
    asked = saved.question(folder, PAGE)
    assert asked and asked.digest and asked.id == f"card:{PAGE}"
    assert held.card_rows(Look(record=tasks.read(board.state, SLUG))) == ()
    record = tasks.read(board.state, SLUG)
    session = Session(live=True, since=records.MOMENT, id=SESSION.lower())
    eyes = Look(record=record, session=cards.in_session(folder, record, session))
    assert [(row.card, row.prompt) for row in held.card_rows(eyes)] == [
        (asked.id, "Keep the empty cell?")
    ]
    card = saved.metadata(folder, PAGE)
    assert card.session == SESSION
    assert card.prompts[0].id == "answer"
    trusted = paths.root() / "skills" / "lem-ask" / "runtime" / "ask.js"
    runtime = trusted.read_text(encoding="utf-8").encode("utf-8")
    digest = b64encode(sha256(runtime).digest()).decode("ascii")
    for route in (ROUTE, ROUTE + "/"):
        with board.main() as client:
            page = client.get(route)
            head = client.head(route)
        assert page.status_code == head.status_code == 200
        assert page.content == saved.html(folder, PAGE, asked.digest)
        assert page.content.decode() == Path(opened["file"]).read_text(encoding="utf-8")
        assert head.headers["etag"] == f'"{asked.digest}"'
        assert head.headers["content-length"] == str(len(page.content))
        assert head.content == b""
        policy = head.headers["content-security-policy"]
        assert page.headers["content-security-policy"] == policy
        directives = [rule.split() for rule in policy.split(";")]
        script_rules = [rule for rule in directives if rule[:1] == ["script-src"]]
        assert script_rules == [["script-src", f"'sha256-{digest}'"]]
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


@pytest.mark.parametrize("other_session", [False, True])
@pytest.mark.parametrize("no_wait", [False, True])
def test_ask_names_why_a_saved_card_stays_off_the_board(
    board: Board,
    terminal: Agterm,
    capsys: pytest.CaptureFixture[str],
    *,
    other_session: bool,
    no_wait: bool,
) -> None:
    folder = board.state / "tasks" / SLUG
    if other_session:
        log.append(
            folder,
            acts.Open(
                at=records.MOMENT, session="S2", name=SLUG, phase="shape", why="open"
            ),
        )
    else:
        terminal.grounds[SESSION] = ("zsh",)
    words = ["--no-wait"] if no_wait else ["--timeout", "0"]
    assert lazy.main(["ask", "q", "Keep the empty cell?", "Keep", *words]) == 0
    opened = json.loads(capsys.readouterr().out)["result"]
    assert opened["outcome"] == ("open" if no_wait else "pending")
    assert opened["board"] == (
        "The board will not show the owner's card. The task has no live session."
    )
    assert saved.question(folder, PAGE) is not None


def test_ask_warns_that_a_card_from_an_older_pane_cannot_take_a_board_answer(
    board: Board,
    terminal: Agterm,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    folder = board.state / "tasks" / SLUG
    log.append(
        folder,
        acts.Open(
            at=records.MOMENT, session="S2", name=SLUG, phase="shape", why="open"
        ),
    )
    terminal.grounds[SESSION] = ("zsh",)
    terminal.grounds["S2"] = ("claude",)
    monkeypatch.setenv("AGTERM_WINDOW_ID", SESSION)
    opened = show(terminal, capsys)
    assert saved.metadata(folder, PAGE).session == SESSION
    assert opened["board"] == "The board will not show the owner's card for this task."
    with board.main() as client:
        workspace = client.get("/studio/shop/")
        assert workspace.status_code == 200
        assert "Keep the empty cell?" not in workspace.text
        digest = client.head(ROUTE).headers["etag"].strip('"')
        receipt = client.post(ROUTE + "/answer", json=posted(digest), headers=ORIGIN)
    assert receipt.status_code == 409
    assert "no longer runs" in receipt.json()["said"]


@pytest.mark.parametrize("outcome", ["pending", "answered"])
def test_ask_reads_the_board_after_the_pane_starts_an_agent_during_the_wait(
    board: Board,
    terminal: Agterm,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    outcome: str,
) -> None:
    terminal.grounds[SESSION] = ("zsh",)
    poll = waiting.poll

    def changed(here: Context, page: str) -> waiting.answer.Words | None:
        terminal.grounds[SESSION] = ("claude",)
        if outcome == "answered":
            with board.main() as client:
                digest = client.head(ROUTE).headers["etag"].strip('"')
                receipt = client.post(
                    ROUTE + "/answer", json=posted(digest), headers=ORIGIN
                )
                assert receipt.status_code == 200
        return poll(here, page)

    monkeypatch.setattr(waiting, "poll", changed)
    assert (
        lazy.main(
            [
                "ask",
                "q",
                "Keep the empty cell?",
                "Keep",
                "Write a dash",
                "--timeout",
                "0",
            ]
        )
        == 0
    )
    picked = json.loads(capsys.readouterr().out)["result"]
    assert picked["outcome"] == outcome
    assert "board" not in picked
    if outcome == "answered":
        assert picked["from"] == "board"


@pytest.mark.parametrize("has_override", [False, True])
def test_ask_uses_the_overlay_executable_for_the_board_notice(
    board: Board,
    terminal: Agterm,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    *,
    has_override: bool,
) -> None:
    cli = tmp_path / "bin" / "agtermctl"
    cli.parent.mkdir()
    tree = terminal.other(("tree", "--json"), None).stdout
    cli.write_text(f"#!{sys.executable}\nprint({tree!r})\n")
    cli.chmod(0o700)
    monkeypatch.setenv("PATH", str(tmp_path / "empty"))
    monkeypatch.delenv("AGTERMCTL", raising=False)
    if has_override:
        monkeypatch.setenv("AGTERMCTL", str(cli))

    def ctl(env: dict, *words: str, **flags: object) -> CompletedProcess[str]:
        return (
            REAL_CTL(env, *words)
            if words[0] == "tree"
            else terminal.ctl(env, *words, **flags)
        )

    # Use the real executable search for tree reads and the stand-in for overlays.
    monkeypatch.setattr(agterm_ctl, "ctl", ctl)
    opened = show(terminal, capsys)
    if has_override:
        assert "board" not in opened
    else:
        assert opened["board"].startswith(
            "Lem could not check if the board will show the owner's card."
        )
        assert "not on the PATH" in opened["board"]
        assert "no live session" not in opened["board"]


def test_the_live_session_lists_its_card_and_leaves_out_the_ended_sessions_card(
    board: Board, terminal: Agterm, capsys: pytest.CaptureFixture[str]
) -> None:
    show(terminal, capsys)
    folder = board.state / "tasks" / SLUG
    old = saved.metadata(folder, PAGE)
    current = form.metadata({"prompt": "The new session asks"}, "P2", "S2")
    saved.keep(folder, current, b"new card")
    record = tasks.read(board.state, SLUG)
    for session_id, expected in (
        (old.session, old.page),
        (current.session, current.page),
    ):
        session = Session(live=True, since=records.MOMENT, id=session_id)
        found = Look(record=record, session=cards.in_session(folder, record, session))
        assert [row.card for row in held.card_rows(found)] == [
            keys.question_id(expected)
        ]


def test_board_answer_is_the_waiters_result_and_the_only_end(
    board: Board, terminal: Agterm, capsys: pytest.CaptureFixture[str]
) -> None:
    show(terminal, capsys)
    with board.main() as client:
        digest = client.head(ROUTE).headers["etag"].strip('"')
        before_post = len(terminal.calls)
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
    assert [call for call in terminal.calls[before_post:] if call[0] != "tree"] == [
        ("session", "overlay", "result", "--page", PAGE, "--json"),
        CLOSE,
    ]
    assert terminal.shown is None
    before_wait = len(terminal.calls)
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
    assert CLOSE not in terminal.calls[before_wait:]
    record = tasks.read(board.state, SLUG)
    assert [row.act for row in record.journal if hasattr(row, "act")] == [
        "card.asked",
        "card.answered",
    ]


def test_board_refuses_a_card_when_its_agent_exits_to_the_shell(
    board: Board,
    terminal: Agterm,
    capsys: pytest.CaptureFixture[str],
) -> None:
    show(terminal, capsys)
    terminal.grounds[SESSION] = ("/bin/zsh",)
    with board.main() as client:
        digest = client.head(ROUTE).headers["etag"].strip('"')
        got = client.post(ROUTE + "/answer", json=posted(digest), headers=ORIGIN)
    assert got.status_code == 409
    assert "no longer runs" in got.json()["said"]
    assert tasks.read(board.state, SLUG).task.questions[0].answer is None


@pytest.mark.parametrize("overlay_read_fails", [False, True])
def test_wait_keeps_the_board_pick_and_names_a_later_overlay_pick(
    board: Board,
    terminal: Agterm,
    capsys: pytest.CaptureFixture[str],
    *,
    overlay_read_fails: bool,
) -> None:
    show(terminal, capsys)
    with board.main() as client:
        digest = client.head(ROUTE).headers["etag"].strip('"')
        response = client.post(ROUTE + "/answer", json=posted(digest), headers=ORIGIN)
    assert response.status_code == 200
    assert terminal.shown is None
    terminal.outcome = "submitted"
    terminal.payload = json.dumps(
        {
            "status": "answered",
            "answers": {"answer": {"selected": ["o1"], "labels": ["Keep"]}},
        }
    )
    terminal.error = "no such page" if overlay_read_fails else None
    assert lazy.main(["ask", "wait", PAGE, "--no-status"]) == 0
    picked = json.loads(capsys.readouterr().out)["result"]
    assert picked["from"] == "board"
    assert picked["answers"]["answer"]["labels"] == ["Write a dash"]
    assert "Write a dash was recorded" in picked["said"]
    if not overlay_read_fails:
        assert "The later act in the session was Keep." in picked["said"]
    assert terminal.shown is None
    record = tasks.read(board.state, SLUG)
    assert [row.act for row in record.journal if hasattr(row, "act")] == [
        "card.asked",
        "card.answered",
    ]


def test_board_receipt_keeps_empty_selections_for_text_and_optional_prompts(
    board: Board,
    terminal: Agterm,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    spec = tmp_path / "text.json"
    spec.write_text(
        json.dumps(
            {
                "questions": [
                    {"id": "note", "prompt": "Why?"},
                    {
                        "id": "skip",
                        "prompt": "Anything else?",
                        "optional": True,
                        "options": ["Yes"],
                    },
                ]
            }
        )
    )
    assert lazy.main(["ask", "ask", str(spec), "--no-wait"]) == 0
    opened = json.loads(capsys.readouterr().out)["result"]
    assert terminal.shown == opened["file"]
    with board.main() as client:
        digest = client.head(ROUTE).headers["etag"].strip('"')
        picked = {
            "status": "answered",
            "digest": digest,
            "answers": {"note": {"text": "For the export"}, "skip": {}},
        }
        assert (
            client.post(ROUTE + "/answer", json=picked, headers=ORIGIN).status_code
            == 200
        )
    assert lazy.main(["ask", "wait", PAGE, "--no-status"]) == 0
    receipt = json.loads(capsys.readouterr().out)["result"]
    assert receipt["answers"] == {
        "note": {"selected": [], "labels": [], "text": "For the export"},
        "skip": {"selected": [], "labels": []},
    }


def test_board_uses_the_saved_runtime_hash_after_an_update(
    board: Board,
    terminal: Agterm,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    opened = show(terminal, capsys)
    root = paths.root()
    runtime = Path("skills/lem-ask/runtime/ask.js")
    original = (root / runtime).read_bytes()
    newer = tmp_path / "new-release"
    chart = Path("skills/lem/assets/vendor/pele.js")
    for path in (runtime, chart):
        (newer / path).parent.mkdir(parents=True, exist_ok=True)
        (newer / path).write_bytes((root / path).read_bytes() + b"\n// new release\n")
    monkeypatch.setattr(paths, "root", lambda: newer)
    with board.main() as client:
        served = client.get(ROUTE + "/")
    policy = served.headers["content-security-policy"]
    assert served.content == Path(opened["file"]).read_bytes()
    assert hashed(original) in policy
    assert hashed((newer / runtime).read_bytes()) not in policy


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


@pytest.mark.parametrize("no_wait", [False, True])
def test_a_board_answer_closes_the_page_when_no_wait_runs(
    board: Board,
    terminal: Agterm,
    capsys: pytest.CaptureFixture[str],
    *,
    no_wait: bool,
) -> None:
    words = ["--no-wait"] if no_wait else ["--timeout", "0"]
    assert lazy.main(["ask", "q", "Approve the criteria?", "Yes", "No", *words]) == 0
    asked = json.loads(capsys.readouterr().out)["result"]
    assert asked["outcome"] == ("open" if no_wait else "pending")
    assert terminal.shown is not None
    with board.main() as client:
        digest = client.head(ROUTE).headers["etag"].strip('"')
        got = client.post(ROUTE + "/answer", json=posted(digest), headers=ORIGIN)
    assert got.status_code == 200
    assert terminal.shown is None
    assert terminal.calls.count(CLOSE) == 1
    assert tasks.read(board.state, SLUG).task.questions[0].answer is not None


def test_the_board_closes_the_page_by_its_id_wherever_its_file_is(
    board: Board, terminal: Agterm, capsys: pytest.CaptureFixture[str]
) -> None:
    show(terminal, capsys)
    terminal.shown = "/the/servers/own/tmp/lem-ask/page.html"
    with board.main() as client:
        digest = client.head(ROUTE).headers["etag"].strip('"')
        got = client.post(ROUTE + "/answer", json=posted(digest), headers=ORIGIN)
    assert got.status_code == 200
    assert terminal.shown is None


def test_the_board_leaves_another_page_of_the_session_open(
    board: Board,
    terminal: Agterm,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    show(terminal, capsys)

    def another_page(env: dict, *words: str, **flags: object) -> CompletedProcess[str]:
        told = terminal.ctl(env, *words, **flags)
        if words[0] != "tree":
            return told
        return CompletedProcess(words, 0, told.stdout.replace(f'"{PAGE}"', '"P2"'), "")

    monkeypatch.setattr(agterm_ctl, "ctl", another_page)
    with board.main() as client:
        digest = client.head(ROUTE).headers["etag"].strip('"')
        got = client.post(ROUTE + "/answer", json=posted(digest), headers=ORIGIN)
    assert got.status_code == 200
    assert terminal.shown is not None
    assert CLOSE not in terminal.calls


def test_a_failed_close_keeps_the_answer_and_logs_the_page_and_the_reason(
    board: Board,
    terminal: Agterm,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    show(terminal, capsys)

    def refuses_close(env: dict, *words: str, **flags: object) -> CompletedProcess[str]:
        if words[:3] == CLOSE[:3]:
            return terminal.reply(words, error="the overlay is busy")
        return terminal.ctl(env, *words, **flags)

    monkeypatch.setattr(agterm_ctl, "ctl", refuses_close)
    with board.main() as client:
        digest = client.head(ROUTE).headers["etag"].strip('"')
        got = client.post(ROUTE + "/answer", json=posted(digest), headers=ORIGIN)
    assert got.status_code == 200
    assert got.json()["said"].startswith("The owner’s answer is on record.")
    assert tasks.read(board.state, SLUG).task.questions[0].answer is not None
    logged = (board.home / "lem.log").read_text(encoding="utf-8")
    assert f"the page {PAGE} did not close in session {SESSION}" in logged
    assert "the overlay is busy" in logged
    assert terminal.shown is not None


def test_a_losing_board_answer_closes_nothing(
    board: Board,
    terminal: Agterm,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    show(terminal, capsys)
    with board.main() as client:
        digest = client.head(ROUTE).headers["etag"].strip('"')
    closes: list[str] = []
    monkeypatch.setattr(
        page_close, "close", lambda *args, **_flags: closes.append(args[2])
    )
    first = Answer(
        at=records.MOMENT, option="dismissed", label="dismissed", source="session"
    )
    finish = ends.finish

    def session_first(
        folder: Path, asked: Question, proposed: Answer, payload: ends.Payload
    ) -> tuple[bool, Answer]:
        finish(folder, asked, first, {"status": "dismissed"})
        return finish(folder, asked, proposed, payload)

    monkeypatch.setattr(ends, "finish", session_first)
    with board.main() as client:
        got = client.post(ROUTE + "/answer", json=posted(digest), headers=ORIGIN)
    assert got.status_code == 409
    assert closes == []


@pytest.mark.parametrize("later", ["dismissed", "submitted"])
def test_a_close_after_the_board_answer_is_no_later_act_of_the_owner(
    board: Board,
    terminal: Agterm,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    later: str,
) -> None:
    show(terminal, capsys)
    with board.main() as client:
        digest = client.head(ROUTE).headers["etag"].strip('"')
        got = client.post(ROUTE + "/answer", json=posted(digest), headers=ORIGIN)
    assert got.status_code == 200
    # The poll read the record before the board's answer reached it, and agterm after.
    monkeypatch.setattr(card_wait, "recorded", lambda *_args: None)
    terminal.outcome = later
    terminal.payload = json.dumps(
        {
            "status": "answered",
            "answers": {"answer": {"selected": ["o1"], "labels": ["Keep"]}},
        }
    )
    assert lazy.main(["ask", "wait", PAGE, "--no-status"]) == 0
    picked = json.loads(capsys.readouterr().out)["result"]
    assert picked["from"] == "board"
    assert picked["answers"]["answer"]["labels"] == ["Write a dash"]
    assert "Write a dash was recorded on the board" in picked["said"]
    if later == "dismissed":
        assert "later act" not in picked["said"]
    else:
        assert "The later act in the session was Keep." in picked["said"]
