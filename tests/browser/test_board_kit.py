"""Exercise the installed board kit in a disposable Chrome profile and loopback page."""

from contextlib import closing
from pathlib import Path
from typing import TYPE_CHECKING

import msgspec
from playwright.sync_api import expect

from fixtures.board import columns, frame, panel, shelves, waiting
from lem.board.inputs.backlog import Holds
from lem.board.inputs.page import Page
from lem.board.inputs.switcher import Group, Space
from lem.board.inputs.task.artifacts import Artifacts, Body, Folder, Section, Shown
from lem.board.pages.render import section

if TYPE_CHECKING:
    import pytest

    from browser.conftest import OpenWindow
    from browser.server import Board
    from lem.board.inputs.task.panel import Panel

PROBE = Path(__file__).parents[1] / "unit" / "board" / "pages" / "browser.js"
ARTIFACTS = Artifacts(
    sections=(Section(key="request", name="The request"),),
    work=(Folder(id="work-folder", name="Working files", docs=(), open=True),),
    said="One document",
    shown=Shown(
        path="docs/backlog/file with spaces.md",
        title="A document",
        kind="text",
        icon="file",
        meta="text",
        body=Body(where="/tmp/file with spaces.md", text="Text"),
    ),
)


def with_panel(selected: Panel) -> Page:
    return Page(frame=frame.FRAME, tasks=columns.TASKS, panel=selected)


SWITCH = msgspec.structs.replace(
    frame.FRAME.sidebar.switcher,
    groups=(
        Group(
            head="Workspaces",
            spaces=(
                Space(
                    id="other",
                    name="Other",
                    says="1 waits",
                    href="/studio/other/",
                    waits=True,
                ),
            ),
        ),
    ),
    every="All workspaces",
)
DRAWER = msgspec.structs.replace(
    frame.FRAME,
    sidebar=msgspec.structs.replace(frame.FRAME.sidebar, switcher=SWITCH),
)

BACKLOG = msgspec.structs.replace(
    shelves.BACKLOG,
    shelves=tuple(
        msgspec.structs.replace(
            group,
            entries=tuple(
                msgspec.structs.replace(
                    entry,
                    new=entry.key == "invoice-footer-wraps",
                    holds=Holds(typed="/lem new docs/backlog/export-in-one-query.md")
                    if entry.key == "export-in-one-query"
                    else entry.holds,
                    where_problem="The source moved."
                    if entry.key == "export-in-one-query"
                    else None,
                )
                for entry in group.entries
            ),
        )
        for group in shelves.BACKLOG.shelves
    ),
)

BOARDS = (
    ("keys", Page(frame=frame.FRAME, tasks=columns.TASKS)),
    ("panel", with_panel(panel.OPEN)),
    (
        "backlog",
        Page(
            frame=msgspec.structs.replace(
                frame.FRAME,
                viewer=msgspec.structs.replace(frame.FRAME.viewer, view="backlog"),
                keys=shelves.KEYS,
            ),
            backlog=BACKLOG,
        ),
    ),
    (
        "waits",
        Page(
            frame=msgspec.structs.replace(
                frame.FRAME,
                viewer=msgspec.structs.replace(frame.FRAME.viewer, view="waits"),
            ),
            waits=waiting.WAITS,
        ),
    ),
    ("chart", with_panel(panel.CRITERIA_TAB)),
    ("merge", with_panel(panel.MERGE_STEP)),
    (
        "copy",
        with_panel(
            msgspec.structs.replace(
                panel.OPEN,
                overview=None,
                shows="artifacts",
                artifacts=ARTIFACTS,
            )
        ),
    ),
    ("drawer", Page(frame=DRAWER, tasks=columns.TASKS)),
)


def test_installed_kit_runs_in_chromium(
    board: Board,
    window: OpenWindow,
    subtests: pytest.Subtests,
) -> None:
    for probe, example in BOARDS:
        with subtests.test(probe=probe):
            size = (390, 840) if probe == "drawer" else (1280, 900)
            with closing(window(size)) as context:
                page = context.pages[0]
                url = f"{board.url}/"
                source = section("page.html", example).replace(
                    '<html lang="en">', f'<html lang="en" data-probe="{probe}">'
                )
                source = source.replace(
                    "</body>",
                    f"<script>{PROBE.read_text(encoding='utf-8')}</script></body>",
                )
                page.route(
                    url,
                    lambda route, *, body=source: route.fulfill(
                        content_type="text/html", body=body
                    ),
                )
                page.route("**/stream?**", lambda route: route.abort())
                page.goto(url)
                expect(page.locator("body")).to_have_attribute(
                    "data-probe-result", "passed"
                )
