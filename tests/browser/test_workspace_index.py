"""The page of every workspace, `/`, on a board joined to a second machine: two machines and
three workspaces at three phone widths, a tablet and a computer, in light and dark. The page has
the board's look (the owner saw it with none, in agterm, 2026-11-27: "Lem" and the machine's name
ran together as one word), nothing scrolls it sideways, and each row keeps its name, its path and
its counts inside it.

Run `BOARD_INDEX_SHOTS=DIR .venv/bin/python -I -B tests --level browser
tests/browser/test_workspace_index.py` to keep a full-page picture at each width and palette in DIR.
"""

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit

import httpx
import pytest
from playwright.sync_api import expect

from browser.board_ui import visit
from fixtures.board.moments import HOST, WORKSPACE
from lem.addons.peers import registry, routes, table

if TYPE_CHECKING:
    from browser.conftest import OpenWindow
    from browser.server import Board

# Three iPhone widths, an iPad's and a laptop's, each with its screen's height.
SCREENS = ((375, 812), (390, 844), (430, 932), (768, 1024), (1280, 900))
PHONE_WIDTH = 430
# The owner's second Mac, by the name it had on his board (2026-11-27).
PEER = "macbook-pro-slvr"
LONG = "a-repository-whose-name-is-longer-than-a-phone-is-wide"
PEER_SPACES = (
    {
        "name": "lem",
        "path": "/Users/owner/Projects/GitHub/lem",
        "waits": 1,
        "building": 0,
        "checks": 0,
    },
    {
        "name": LONG,
        "path": f"/Users/owner/Projects/GitHub/clients/{LONG}",
        "waits": 0,
        "building": 2,
        "checks": 1,
    },
)
# Two boxes closer than this run together as one word.
APART_PX = 4
SLACK = 0.5

MEASURE = """() => {
  const width = document.documentElement.clientWidth
  const rect = el => { const r = el.getBoundingClientRect(); return {x: r.left, y: r.top, right: r.right, bottom: r.bottom} }
  const shown = el => el.getClientRects().length && getComputedStyle(el).visibility !== 'hidden'
  const name = el => el.tagName.toLowerCase() + (el.id ? '#' + el.id : '')
    + (typeof el.className === 'string' && el.className.trim() ? '.' + el.className.trim().split(/\\s+/).join('.') : '')
  const wide = [...document.body.querySelectorAll('*')]
    .filter(el => shown(el) && !el.closest('.sprite'))
    .filter(el => { const r = el.getBoundingClientRect(); return r.right > width + 0.5 || r.left < -0.5 })
    .slice(0, 8).map(name)
  const row = el => ({
    id: el.id,
    you: el.classList.contains('you'),
    shadow: getComputedStyle(el).boxShadow,
    radius: getComputedStyle(el).borderTopLeftRadius,
    box: rect(el),
    parts: [...el.querySelectorAll(':scope > a, :scope > b, :scope > small, .tag')].map(part => ({
      name: name(part), text: part.textContent.trim(), box: rect(part),
      cut: part.scrollWidth > part.clientWidth + 1,
    })),
  })
  return {
    width,
    document: document.documentElement.scrollWidth,
    wide,
    mark: rect(document.querySelector('.ident .mark')),
    brand: rect(document.querySelector('.ident .eyebrow b')),
    host: rect(document.querySelector('.ident .plain-host')),
    machines: [...document.querySelectorAll('.machine')].map(machine => ({
      head: machine.querySelector('h2').textContent.trim(),
      rows: [...machine.querySelectorAll('.workspace')].map(row),
    })),
  }
}"""


@pytest.fixture
def two_machines(
    board: Board, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Board:
    home = tmp_path / "lem-home"
    table.change(home, PEER, 19037)

    async def address(host: str, port: int) -> str:
        return f"https://{host}.test.invalid:{port}"

    def answer(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/workspaces"
        return httpx.Response(200, content=json.dumps(PEER_SPACES))

    peers = registry.Registry(
        home=home, own=HOST, address=address, transport=httpx.MockTransport(answer)
    )
    monkeypatch.setattr(routes, "peers", lambda request: peers)
    return board


def inside(part: dict[str, float], row: dict[str, float]) -> bool:
    return (
        part["x"] >= row["x"] - SLACK
        and part["right"] <= row["right"] + SLACK
        and part["y"] >= row["y"] - SLACK
        and part["bottom"] <= row["bottom"] + SLACK
    )


def faults(width: int, found: dict[str, Any]) -> list[str]:
    """What is wrong at one width, a line for each fault."""
    lines = []
    if found["document"] > width:
        lines.append(f"the page is {found['document']} px wide: {found['wide']}")
    lines.extend(f"{name} runs past the screen" for name in found["wide"])
    if found["mark"]["right"] - found["mark"]["x"] < 32:
        lines.append(f"the mark has no size of its own: {found['mark']}")
    brand, host = found["brand"], found["host"]
    beside = host["y"] < brand["bottom"] and brand["y"] < host["bottom"]
    if beside and host["x"] - brand["right"] < APART_PX:
        lines.append(f"Lem and the machine run together: {brand} {host}")
    for machine in found["machines"]:
        for row in machine["rows"]:
            lines.extend(row_faults(row))
    return lines


def row_faults(row: dict[str, Any]) -> list[str]:
    """What is wrong with one workspace's row: its look, its mark, its parts."""
    lines = []
    if row["radius"] != "10px":
        lines.append(f"{row['id']} has no look of its own ({row['radius']})")
    if row["you"] and "inset" not in row["shadow"]:
        lines.append(f"{row['id']} waits for the owner and has no mark")
    for part in row["parts"]:
        if not inside(part["box"], row["box"]):
            lines.append(f"{row['id']}: {part['name']} leaves its row")
        if part["cut"]:
            lines.append(f"{row['id']}: {part['name']} is cut")
    return lines


@pytest.mark.parametrize("theme", ("light", "dark"))
def test_the_index_groups_two_machines_and_fits_every_screen(
    two_machines: Board, window: OpenWindow, theme: str
) -> None:
    parts = urlsplit(two_machines.url)
    root = f"{parts.scheme}://{parts.netloc}/"
    shots = os.environ.get("BOARD_INDEX_SHOTS")
    problems = []
    for screen in SCREENS:
        width = screen[0]
        phone = width <= PHONE_WIDTH
        page = window(screen, phone=phone, dark=theme == "dark").pages[0]
        visit(page, root, ".workspace-list")
        expect(page.locator("html")).to_have_attribute("data-palette", theme)
        expect(page.locator(".workspace")).to_have_count(3)
        found = page.evaluate(MEASURE)
        assert [machine["head"] for machine in found["machines"]] == [
            f"{HOST} this machine",
            PEER,
        ]
        assert [
            [row["id"] for row in machine["rows"]] for machine in found["machines"]
        ] == [
            [f"/{HOST}/{WORKSPACE}/"],
            [f"/{PEER}/lem/", f"/{PEER}/{LONG}/"],
        ]
        assert [
            row["you"] for machine in found["machines"] for row in machine["rows"]
        ] == [True, True, False]
        problems.extend(f"{width} px: {line}" for line in faults(width, found))
        if shots:
            Path(shots).mkdir(parents=True, exist_ok=True)
            page.screenshot(
                path=Path(shots) / f"index-{width}-{theme}.png",
                full_page=True,
                animations="disabled",
            )
        page.context.close()
    assert not problems, "\n".join(problems)
