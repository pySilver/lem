"""Exercise the installed board kit in a disposable Chrome profile and loopback page."""

import re
import subprocess
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from typing import TYPE_CHECKING

import msgspec
import pytest

from fixtures.board import columns, frame, panel, shelves, waiting
from lem.board.inputs.backlog import Holds
from lem.board.inputs.page import Page
from lem.board.inputs.switcher import Group, Space
from lem.board.inputs.task.artifacts import Artifacts, Body, Folder, Section, Shown
from lem.board.pages.render import section
from lem.kernel import paths

if TYPE_CHECKING:
    from lem.board.inputs.task.panel import Panel

CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
ASSETS = paths.root() / "skills" / "lem" / "assets"
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
            frame=msgspec.structs.replace(frame.FRAME, keys=shelves.KEYS),
            backlog=BACKLOG,
        ),
    ),
    ("waits", Page(frame=frame.FRAME, waits=waiting.WAITS)),
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


def test_installed_kit_runs_in_chrome(
    tmp_path: Path, subtests: pytest.Subtests
) -> None:
    if not CHROME.is_file():
        pytest.skip("Google Chrome is unavailable")
    for probe, board in BOARDS:
        with subtests.test(probe=probe):
            folder = tmp_path / probe
            folder.mkdir()
            check_browser(folder, probe, board)


def check_browser(tmp_path: Path, probe: str, board: Page) -> None:
    source = section("page.html", board)
    source = source.replace("/studio/assets/", "/assets/")
    (tmp_path / "assets").symlink_to(ASSETS)
    source = source.replace(
        '<html lang="en">', f'<html lang="en" data-probe="{probe}">'
    )
    source = source.replace(
        "</body>", f"<script>{PROBE.read_text(encoding='utf-8')}</script></body>"
    )
    page = tmp_path / "board.html"
    page.write_text(source, encoding="utf-8")
    screen = "390,840" if probe == "drawer" else "1280,900"
    handler = partial(SimpleHTTPRequestHandler, directory=str(tmp_path))
    with ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
        worker = Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            ran = chrome(tmp_path, screen, server.server_port)
        finally:
            server.shutdown()
            worker.join()
    assert ran.returncode == 0, ran.stderr
    marker = re.search('data-probe-result="([^"]*)"', ran.stdout)
    assert marker and marker[1] == "passed", marker[1] if marker else ran.stderr


def chrome(tmp_path: Path, screen: str, port: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            str(CHROME),
            "--headless",
            "--use-mock-keychain",
            "--disable-background-networking",
            "--no-first-run",
            f"--user-data-dir={tmp_path / 'profile'}",
            f"--window-size={screen}",
            "--disable-gpu",
            "--disable-crash-reporter",
            "--virtual-time-budget=8000",
            "--dump-dom",
            f"http://127.0.0.1:{port}/board.html",
        ],
        capture_output=True,
        text=True,
        timeout=35,
        check=False,
    )
