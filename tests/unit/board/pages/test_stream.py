"""The refresh sent for a missed change and for a file written while a page is open."""

from contextlib import aclosing
from functools import partial
from typing import TYPE_CHECKING

import anyio
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
    app.state.act_revision = lambda _: ""
    return Request(
        {
            "type": "http",
            "app": app,
            "path_params": {"slug": slug} if slug else {},
            "query_string": f"task={slug}".encode() if slug else b"",
        }
    )


def test_opening_or_closing_a_task_does_not_owe_a_refresh(tmp_path: Path) -> None:
    state = tmp_path / "state"
    report = state / "tasks" / "a-task" / "report.md"
    report.parent.mkdir(parents=True)
    report.write_text("The task's report", encoding="utf-8")
    home = tmp_path / "home"
    closed = stamps.shown(at(home, None), state)
    request = at(home, "a-task")
    task_page = stamps.shown(request, state)
    request.scope["path_params"] = {}
    opened = stamps.shown(request, state)
    assert opened.watched == task_page.watched != closed.watched
    report.with_name("task.json").write_text("A task record", encoding="utf-8")
    changed = stamps.shown(request, state)
    assert changed.version != closed.version

    async def check() -> None:
        for rendered, first in ((closed, opened), (opened, closed)):
            readings = iter((first, changed))
            async with aclosing(
                stream.refreshed(
                    readings.__next__, rendered=rendered.version, missed=False
                )
            ) as messages:
                with anyio.fail_after(5):
                    assert (await anext(messages)).id == changed.version

    anyio.run(check)


POLL_FILES = {
    "checkout/.lem/state/tasks/a-task/task.json": True,
    "checkout/.lem/state/tasks/a-task/sessions.jsonl": True,
    "checkout/.lem/state/tasks/a-task/report.md": False,
    "checkout/.lem/state/tasks/a-task/media/view.png": False,
    "checkout/.lem/state/backlog/a.md": True,
    "checkout/.lem/state/inbox.json": True,
    "checkout/.lem/state/forge.json": True,
    "checkout/.lem/settings.toml": True,
    "checkout/docs/backlog/a.md": True,
    "home/owner.json": True,
}


@pytest.mark.parametrize("leaf", POLL_FILES)
def test_poll_notices_replacement_and_removal(tmp_path: Path, leaf: str) -> None:
    state = tmp_path / "checkout" / ".lem" / "state"
    state.mkdir(parents=True)
    path = tmp_path / leaf
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("first", encoding="utf-8")
    look = partial(stamps.shown, at(tmp_path / "home", "a-task"), state)
    before = look()

    async def check() -> None:
        async with aclosing(
            stream.refreshed(look, rendered=before.version, missed=True)
        ) as messages:
            with anyio.fail_after(5):
                assert (await anext(messages)).id == before.version
                replacement = path.with_suffix(".new")
                replacement.write_text("other", encoding="utf-8")
                replacement.replace(path)
                first = await anext(messages)
                assert first.id == look().version
                path.unlink()
                second = await anext(messages)
                assert second.id == look().version
                if POLL_FILES[leaf]:
                    assert len({before.version, first.id, second.id}) == 3
                else:
                    assert first.id == second.id == before.version

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
    assert stamps.shown(request, state).version != before.version


def test_merge_refusal_between_render_and_stream_open_sends_refresh(
    tmp_path: Path,
) -> None:
    state = tmp_path / "state"
    request = at(tmp_path / "home", None)
    notes = {state: "running: Merging…"}
    request.app.state.act_revision = notes.__getitem__
    look = partial(stamps.shown, request, state)
    before = look()
    notes[state] = "refused: The base moved."

    async def check() -> None:
        async with aclosing(
            stream.refreshed(look, rendered=before.version, missed=False)
        ) as messages:
            with anyio.fail_after(2):
                message = await anext(messages)
                assert message.data == stream.REFRESH
                assert message.id == look().version != before.version
                assert look().watched == before.watched

    anyio.run(check)


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

    async def check() -> None:
        async with aclosing(
            stream.refreshed(look, rendered=before.version, missed=True)
        ) as messages:
            with anyio.fail_after(2):
                assert (await anext(messages)).id == before.version
                notes[state] = "refused: The base moved."
                message = await anext(messages)
                assert message.id == look().version != before.version

    anyio.run(check)
