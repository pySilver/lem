"""GET and HEAD at the page table, with an in-process app and a typed view source."""

from typing import TYPE_CHECKING

import anyio
import msgspec
import pytest
from starlette.applications import Starlette
from starlette.datastructures import Headers
from starlette.testclient import TestClient

from fixtures.board import columns, frame, panel, shelves, waiting
from lem.board import stream
from lem.board.facts import Facts, Install
from lem.board.inputs.activity import NewTask
from lem.board.inputs.page import Page
from lem.board.inputs.switcher import Box, Workspaces
from lem.board.inputs.task.artifacts import Artifacts, Body, Shown
from lem.board.inputs.task.steps import Card, Confirm, Drop, Park
from lem.board.inputs.tasks import Older
from lem.board.pages import routes
from lem.kernel import clock
from unit.board.pages import test_sections as examples
from unit.board.pages.markup import Parsed

if TYPE_CHECKING:
    from pathlib import Path

    from starlette.requests import Request
    from starlette.types import Message

    from lem.store.places import Workspace

HOST = "studio"
WORKSPACE = "/studio/shop"
TASK = WORKSPACE + "/tasks/refund-line-on-receipt"


TASK_TABS = {
    "overview": panel.OPEN,
    "criteria": panel.CRITERIA_TAB,
    "checks": panel.CHECKS_TAB,
    "merge": panel.MERGE_STEP,
    "timeline": panel.Panel(
        slug=panel.SLUG, shows="timeline", timeline=examples.TIMELINE
    ),
    "artifacts": panel.Panel(
        slug=panel.SLUG,
        shows="artifacts",
        artifacts=Artifacts(sections=(), said="Task files"),
    ),
    "park": panel.Panel(
        slug=panel.SLUG,
        shows="park",
        park=Park(
            confirm=Confirm(look="you", label="Park this task", eyebrow="Confirm"),
            what="Waits",
            said="Work stays.",
        ),
    ),
    "drop": panel.Panel(
        slug=panel.SLUG,
        shows="drop",
        drop=Drop(
            confirm=Confirm(look="you", label="Drop this task", eyebrow="Confirm"),
            what="Waits",
            said="Work stops.",
        ),
    ),
}
WORKSPACE_VIEWS = {
    "tasks": Page(frame=frame.FRAME, tasks=columns.TASKS),
    "waits": Page(frame=examples.for_view("waits", "Waits"), waits=waiting.WAITS),
    "backlog": Page(
        frame=examples.for_view("backlog", "Backlog"), backlog=shelves.BACKLOG
    ),
    "activity": Page(
        frame=examples.for_view("activity", "Activity"), activity=examples.ACTIVITY
    ),
    "done": Page(
        frame=examples.for_view("done", "Done"),
        older=Older(newer=examples.BACK, empty="No older tasks"),
    ),
    "new": Page(
        frame=examples.for_view("new", "New"),
        new=NewTask(form=examples.FORM, cancel=examples.BACK),
    ),
}


def task_panel(request: Request, name: str) -> panel.Panel:
    slug = request.path_params["slug"]
    assert slug == panel.SLUG
    if name == "artifact":
        path = request.path_params["path"]
        return panel.Panel(
            slug=slug,
            shows="artifacts",
            artifacts=Artifacts(
                sections=(),
                said="Task files",
                chosen=True,
                shown=Shown(
                    path=path,
                    title=f"Artifact {path}",
                    kind="text",
                    icon="file",
                    meta="Text",
                    body=Body(where=path, text="Contents of the selected file"),
                ),
            ),
        )
    if name == "card":
        asked = request.path_params["page"]
        return panel.Panel(
            slug=slug,
            shows="card",
            card=Card(
                confirm=Confirm(look="you", label="Question", eyebrow="Card"),
                frame=f"{TASK}/cards/{asked}/",
                title="Question from the task",
                keep=f"card-{asked}",
            ),
        )
    return TASK_TABS[name]


def inputs(
    request: Request, space: Workspace | None, version: str
) -> Page | Workspaces:
    name = request.state.page_route
    if space is None:
        assert name == "workspaces"
        return Workspaces(
            host=HOST,
            ask="Two workspaces.",
            boxes=(
                Box(id="shop", name="shop", path="shop", href=WORKSPACE + "/"),
                Box(id="offline", name="Other", path="other"),
            ),
        )
    assert version and space.checkout.name == "shop"
    layout = msgspec.structs.replace(
        frame.FRAME, head=msgspec.structs.replace(frame.FRAME.head, version=version)
    )
    if "slug" in request.path_params:
        return Page(frame=layout, tasks=columns.TASKS, panel=task_panel(request, name))
    base = WORKSPACE_VIEWS[name]
    return msgspec.structs.replace(
        base, frame=msgspec.structs.replace(base.frame, head=layout.head)
    )


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    checkout = tmp_path / "shop"
    (checkout / ".lem" / "state").mkdir(parents=True)
    home = tmp_path / "home"
    home.mkdir()
    (home / "workspaces.json").write_text(f'["{checkout}"]', encoding="utf-8")
    app = Starlette(routes=(*routes.ROUTES, *routes.FALLBACK_ROUTES))
    app.state.facts = Facts(
        pid=1,
        port=1,
        url="http://testserver",
        host=HOST,
        home=str(home),
        install=Install(version="0.3.1", package="scratch"),
        started=clock.now(),
    )
    app.state.home = home
    app.state.page_inputs = inputs
    app.state.act_revision = lambda _: ""
    return TestClient(app)


PAGES = (
    ("/", "index", "<h1>Workspaces</h1>"),
    ("/assets/lem.css", "asset", "--you:"),
    ("/studio/assets/lem.css", "host-asset", "--you:"),
    (f"{WORKSPACE}/", "tasks", 'id="card-refund-line-on-receipt"'),
    (f"{WORKSPACE}/waits", "waits", 'id="wait-stack-refund-line-on-receipt"'),
    (f"{WORKSPACE}/backlog", "backlog", 'id="item-invoice-footer-wraps"'),
    (f"{WORKSPACE}/activity", "activity", 'id="tl-refund-line-on-receipt"'),
    (f"{WORKSPACE}/done", "done", "No older tasks"),
    (f"{WORKSPACE}/new", "new", 'id="new-words"'),
    (TASK, "task", 'id="merge-review"'),
    (f"{TASK}/overview", "overview", 'id="merge-review"'),
    (f"{TASK}/criteria", "criteria", 'id="criterion-1"'),
    (f"{TASK}/checks", "checks", "make test"),
    (f"{TASK}/timeline", "timeline", 'id="now-work"'),
    (f"{TASK}/artifacts", "artifacts", 'id="arts-side"'),
    (f"{TASK}/merge", "merge", "Approve"),
    (f"{TASK}/park", "park", "Park this task"),
    (f"{TASK}/drop", "drop", "Drop this task"),
    (f"{TASK}/artifacts/one/two", "artifact-file", "Artifact one/two"),
    (f"{TASK}/card/question", "question-card", f'src="{TASK}/cards/question/"'),
)


@pytest.mark.parametrize(
    ("url", "label", "expected"), PAGES, ids=[label for _, label, _ in PAGES]
)
def test_get_and_head_at_the_same_address(
    client: TestClient, url: str, label: str, expected: str
) -> None:
    get = client.get(url)
    head = client.head(url)
    assert get.status_code == head.status_code == 200
    assert get.content and not head.content
    assert get.headers["content-type"] == head.headers["content-type"]
    assert get.headers["content-length"] == head.headers["content-length"]
    assert expected in get.text
    if label.endswith("asset"):
        assert get.headers["content-type"].startswith("text/css")
    else:
        assert get.text.startswith("<!doctype html>")


def test_task_link_can_request_just_the_turbo_frame(client: TestClient) -> None:
    answer = client.get(f"{TASK}/overview", headers={"Turbo-Frame": "task"})
    assert answer.status_code == 200
    assert answer.text.lstrip().startswith('<turbo-frame id="task"')
    assert '<section class="panel"' in answer.text
    assert "<!doctype html>" not in answer.text


@pytest.mark.parametrize("fragment", [False, True])
def test_unknown_task_tab_keeps_the_task_tabs_and_way_back(
    client: TestClient, *, fragment: bool
) -> None:
    headers = {"Turbo-Frame": "task"} if fragment else {}
    address = f"{TASK}/typo"
    answer = client.get(address, headers=headers)
    assert (
        answer.status_code == client.head(address, headers=headers).status_code == 404
    )
    root = Parsed(answer.text).root
    shown = root.one(id_="panel")
    assert "typo" in shown.one(id_="tb-missing").words()
    tabs = shown.one(id_="ptabs").all(cls="ptab")
    assert [tab.attrs["href"] for tab in tabs] == [
        link.href for link in panel.OPEN.tabs
    ]
    assert not any("aria-current" in tab.attrs for tab in tabs)
    assert panel.OPEN.head is not None
    assert shown.one(cls="p-back").attrs["href"] == panel.OPEN.head.back
    assert bool(root.all(tag="html")) is not fragment


def test_assets_and_pages_refuse_an_address_on_another_host(client: TestClient) -> None:
    assert client.get("/other/assets/lem.css").status_code == 404
    assert client.get("/other/shop/waits").status_code == 404
    assert client.get("/studio/shop-was-removed/waits").status_code == 404


def test_stream_head_finishes_with_event_headers(client: TestClient) -> None:
    head = client.head(f"{WORKSPACE}/stream")
    assert head.status_code == 200
    assert head.headers["content-type"].startswith(stream.EVENTS)
    assert not head.content


def test_stream_get_sends_a_refresh_to_a_reconnecting_page(client: TestClient) -> None:
    assert isinstance(client.app, Starlette)
    app = client.app
    path = f"{WORKSPACE}/stream"
    messages: list[Message] = []

    async def read_first_event() -> None:
        wrote = anyio.Event()

        async def receive() -> Message:
            await wrote.wait()
            return {"type": "http.disconnect"}

        async def send(message: Message) -> None:
            messages.append(message)
            if message["type"] == "http.response.body" and message["body"]:
                wrote.set()

        with anyio.fail_after(5):
            await app(
                {
                    "type": "http",
                    "method": "GET",
                    "path": path,
                    "query_string": b"since=previous",
                    "headers": [],
                },
                receive,
                send,
            )

    anyio.run(read_first_event)
    headers, refresh = messages[:2]
    assert headers["status"] == 200
    assert Headers(raw=headers["headers"])["content-type"].startswith(stream.EVENTS)
    assert f"data: {stream.REFRESH}".encode() in refresh["body"]


def test_workspace_index_reports_a_missing_input_provider(client: TestClient) -> None:
    assert isinstance(client.app, Starlette)
    del client.app.state.page_inputs
    answer = client.get("/")
    assert answer.status_code == 503
    assert "The board&#39;s page inputs are not available." in answer.text


def test_workspace_page_requires_the_act_revision_binding(client: TestClient) -> None:
    assert isinstance(client.app, Starlette)
    del client.app.state.act_revision
    with pytest.raises(AttributeError, match="act_revision"):
        client.get(f"{WORKSPACE}/")


def test_one_workspace_redirects_for_get_and_head(client: TestClient) -> None:
    assert isinstance(client.app, Starlette)
    client.app.state.page_inputs = lambda *_: Workspaces(
        host=HOST,
        ask="One workspace",
        boxes=(Box(id="shop", name="shop", path="shop", href=WORKSPACE + "/"),),
    )
    for method in ("GET", "HEAD"):
        reply = client.request(method, "/", follow_redirects=False)
        assert reply.status_code == 302
        assert reply.headers["location"] == f"{WORKSPACE}/"
