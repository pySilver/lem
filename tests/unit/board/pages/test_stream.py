"""The refresh sent for a missed change and for a file written while a page is open."""

from contextlib import aclosing
from functools import partial
from typing import TYPE_CHECKING

import anyio
import anyio.lowlevel
import pytest
from starlette.applications import Starlette
from starlette.requests import Request

from lem.board import stream
from lem.board.pages import stamps

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize(
    ("rendered", "missed", "owed"),
    [
        ("current", False, False),
        ("old", False, True),
        ("current", True, True),
        (None, True, True),
        (None, False, False),
    ],
)
def test_open_and_reconnect_have_distinct_refresh_rules(
    rendered: str | None, *, missed: bool, owed: bool
) -> None:
    assert stream.owes(rendered=rendered, missed=missed, told="current") == owed


def test_turbo_refresh_and_quiet_ping_have_distinct_event_types() -> None:
    assert stream.refresh("123").encode().decode().splitlines()[:2] == [
        "id: 123",
        f"data: {stream.REFRESH}",
    ]
    assert "event: ping" in stream.pinged().encode().decode()


def at(home: Path, slug: str | None) -> Request:
    app = Starlette()
    app.state.home = home
    return Request(
        {
            "type": "http",
            "app": app,
            "path_params": {"slug": slug} if slug else {},
            "query_string": f"task={slug}".encode() if slug else b"",
        }
    )


@pytest.mark.parametrize(
    "leaf",
    [
        "checkout/.lem/state/tasks/a-task/task.json",
        "checkout/.lem/state/tasks/a-task/sessions.jsonl",
        "checkout/.lem/state/tasks/a-task/report.md",
        "checkout/.lem/state/tasks/a-task/media/view.png",
        "checkout/.lem/state/backlog/a.md",
        "checkout/.lem/state/inbox.json",
        "checkout/.lem/state/forge.json",
        "checkout/.lem/settings.toml",
        "checkout/docs/backlog/a.md",
        "home/owner.json",
    ],
)
def test_poll_notices_replacement_and_removal(tmp_path: Path, leaf: str) -> None:
    state = tmp_path / "checkout" / ".lem" / "state"
    state.mkdir(parents=True)
    path = tmp_path / leaf
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("first", encoding="utf-8")
    look = partial(stamps.shown, at(tmp_path / "home", "a-task"), state)
    before = look()

    async def check() -> None:
        async with anyio.create_task_group() as group:

            async def change() -> None:
                await anyio.lowlevel.checkpoint()
                replacement = path.with_suffix(".new")
                replacement.write_text("other", encoding="utf-8")
                replacement.replace(path)

            async with aclosing(
                stream.refreshed(look, rendered=before, missed=False)
            ) as messages:
                group.start_soon(change)
                with anyio.fail_after(5):
                    first = await anext(messages)
                    assert first.id == look() != before
                    path.unlink()
                    second = await anext(messages)
                    assert second.id == look() != first.id

    anyio.run(check)


def test_poll_ignores_other_tasks_prose_and_does_not_follow_a_slug_as_a_path(
    tmp_path: Path,
) -> None:
    state = tmp_path / "state"
    artifact = state / "tasks" / "other-task" / "note.txt"
    artifact.parent.mkdir(parents=True)
    for slug in ("a-task", "../other-task", "*"):
        request = at(tmp_path / "home", slug)
        before = stamps.shown(request, state)
        artifact.write_text(f"{slug} new contents", encoding="utf-8")
        assert before == stamps.shown(request, state)


def test_session_stop_refreshes_activity_without_an_open_task(tmp_path: Path) -> None:
    state = tmp_path / "state"
    request = at(tmp_path / "home", None)
    happened = state / "tasks" / "a-task" / "session-acts.jsonl"
    happened.parent.mkdir(parents=True)
    before = stamps.shown(request, state)
    happened.write_text('{"act":"stop"}\n', encoding="utf-8")
    assert stamps.shown(request, state) != before


def test_merge_refusal_refreshes_after_the_last_file_write(tmp_path: Path) -> None:
    state = tmp_path / "state"
    request = at(tmp_path / "home", "a-task")
    notes = {state: "running: Merging…"}
    request.app.state.act_revision = notes.__getitem__
    other = tmp_path / "other"
    notes[other] = "running: Merging…"
    look = partial(stamps.shown, request, state)
    before = look()
    notes[other] = "refused: Another merge stopped."
    assert look() == before
    notes[state] = "refused: The base moved."

    async def check() -> None:
        async with aclosing(
            stream.refreshed(look, rendered=before, missed=False)
        ) as messages:
            with anyio.fail_after(2):
                message = await anext(messages)
                assert message.id == look() != before

    anyio.run(check)
