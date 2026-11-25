"""The stream sees changes to a session or a base tree without a Lem write."""

import re
from collections.abc import AsyncGenerator
from contextlib import aclosing
from typing import TYPE_CHECKING, cast
from unittest.mock import Mock

import anyio
import pytest
from msgspec.structs import replace
from starlette.requests import Request

from lem.app.sessions.here import bound
from lem.board import stream
from lem.board.pages import observations, place, stamps
from lem.records.landing.record import Landing
from lem.store import tasks
from unit.board.acts.acts import SLUG, made, opened
from unit.owner.looked import proposed, read

if TYPE_CHECKING:
    from fakes.git import ModelGit
    from unit.board.acts.conftest import Board


def stream_request(board: Board, query: bytes = b"") -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "app": board.client.app,
            "headers": [],
            "path_params": {"host": board.base.split("/")[1], "workspace": "shop"},
            "query_string": query,
        }
    )


def live_clock(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    now = [0.0]
    monkeypatch.setattr(observations, "monotonic", lambda: now[0])
    return now


def test_polls_and_pages_share_the_terminal_read(
    board: Board, monkeypatch: pytest.MonkeyPatch
) -> None:
    made(board, status="building")
    opened(board)
    sessions = Mock(wraps=board.terminal.sessions)
    monkeypatch.setattr(board.terminal, "sessions", sessions)
    now = live_clock(monkeypatch)

    first = stream_request(board)
    space = place.workspace(first)
    before = stamps.shown(first, space.state, space)
    made(board, "add-a-flag", status="building")
    now[0] += observations.REFRESH_SECONDS / 2
    after = stamps.shown(stream_request(board), space.state, space)
    assert before.version != after.version
    assert sessions.call_count == 1
    page = board.client.get(f"{board.base}/")
    assert 'id="card-add-a-flag"' in page.text
    assert f'data-stream-since-value="{after.version}"' in page.text
    assert sessions.call_count == 1
    now[0] += observations.REFRESH_SECONDS / 2
    stamps.shown(stream_request(board), space.state, space)
    assert sessions.call_count == 2


@pytest.mark.parametrize("change", ["session", "base"])
def test_the_stream_refreshes_for_live_facts_without_a_task_write(
    board: Board, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    now = live_clock(monkeypatch)
    (board.checkout / ".lem" / "settings.toml").write_text('[branch]\nbase = "main"\n')
    git = cast("ModelGit", bound(board.checkout).ports.git)
    base = git.store({"README.md": b"First"}, (), "the first commit")
    git.remote["main"] = base
    git.fetch(board.checkout)
    review = read("merge")
    seen = made(board, status="open")
    landing = Landing(
        phase="open",
        proposed=proposed(),
        reads=(replace(review, base=base, base_tree=git.tree(board.checkout, base)),),
    )
    tasks.update(
        board.state,
        SLUG,
        lambda record: replace(record, landing=landing),
        seen.revision,
    )
    session = opened(board) if change == "session" else None
    page = board.client.get(f"{board.base}/")
    assert page.status_code == 200
    version = re.search(r'data-stream-since-value="([^"]+)"', page.text)
    assert version is not None
    request = stream_request(board, f"since={version[1]}".encode())

    async def check() -> None:
        response = await stream.endpoint(request)
        assert isinstance(response, stream.EventSourceResponse)
        events = response.body_iterator
        assert isinstance(events, AsyncGenerator)
        with anyio.fail_after(5):
            async with aclosing(events):
                before = await anext(events)
                assert isinstance(before, stream.ServerSentEvent)
                assert before.id == version[1]
                if session is None:
                    git.outside_commit("main", {"README.md": b"Second"})
                    git.fetch(board.checkout)
                else:
                    board.terminal.close(session, when_unselected=False)
                now[0] += observations.REFRESH_SECONDS
                event = await anext(events)
        assert isinstance(event, stream.ServerSentEvent)
        assert event.data == stream.REFRESH and event.id != version[1]

    anyio.run(check)
