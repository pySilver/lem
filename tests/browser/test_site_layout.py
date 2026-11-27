"""Every page of the public site, the landing page and each page of the docs, at three phone
widths, a tablet and a computer, in light and dark: nothing scrolls the page sideways, the page
menu stands clear of every heading and paragraph, the landing page's lead fits a phone, and no
text is cut.

The site is built as `.github/workflows/pages.yml` builds it, once, and served over loopback, as
GitHub Pages serves it. Run
`SITE_LAYOUT_SHOTS=DIR .venv/bin/python -I -B tests --level browser tests/browser/test_site_layout.py`
to keep a full-page picture of each page at each width and palette in DIR. (The test entry clears
every variable whose name starts with LEM_.)
"""

import os
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from typing import TYPE_CHECKING, Any

import pytest

from unit.guides import built

if TYPE_CHECKING:
    from collections.abc import Iterator

    from browser.conftest import OpenWindow

# Three iPhone widths, an iPad's and a laptop's, each with its screen's height.
SCREENS = ((375, 812), (390, 844), (430, 932), (768, 1024), (1280, 900))
# The widest screen that counts as a phone.
PHONE_WIDTH = 430
# Under this width the page menu takes a line of its own above the title (lem-site.css, 60em).
# On the owner's iPhone at 390 px it floated beside the title, and the title broke into a ragged
# column of two words a line beside it (his screenshot, Safari, 2026-11-27).
OWN_LINE_WIDTH = 960
# The landing page's lead on a phone.
LEAD_MOST_PX = 40
# A box edge that differs by less than this is the same edge (sub-pixel rounding).
SLACK = 0.5

# What the page reports: its width, the page menu's control, the text boxes of the headings and
# paragraphs, the lead's size, and every piece of text that is cut.
MEASURE = """() => {
  const width = window.innerWidth
  const rect = r => ({x: r.left, y: r.top, right: r.right, bottom: r.bottom})
  const shown = el => {
    const style = getComputedStyle(el)
    const r = el.getBoundingClientRect()
    if (style.display === 'none' || style.visibility === 'hidden' || r.width <= 1 || r.height <= 1) return false
    for (let up = el; up; up = up.parentElement) if (getComputedStyle(up).opacity === '0') return false
    return true
  }
  // A drawer slid out of the screen (the docs' menu on a narrow screen) is not cut, only away.
  const away = r => r.right <= 0.5 || r.left >= width - 0.5
  const name = el => el.tagName.toLowerCase() + (el.id ? '#' + el.id : '')
    + (el.className && typeof el.className === 'string'
       ? '.' + el.className.trim().split(/\\s+/).join('.') : '')
  const textBoxes = el => {
    const boxes = []
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT)
    for (let node = walker.nextNode(); node; node = walker.nextNode()) {
      if (!node.textContent.trim()) continue
      const range = document.createRange()
      range.selectNodeContents(node)
      for (const r of range.getClientRects()) if (r.width > 0 && r.height > 0) boxes.push(rect(r))
    }
    return boxes
  }
  const body = document.querySelector('article.md-content__inner') || document.querySelector('main')
  const controls = [...document.querySelectorAll('.lem-page-actions summary, .lem-page-menu > summary, .md-content__button')]
    .filter(shown).map(el => ({name: name(el), box: rect(el.getBoundingClientRect())}))
  const texts = [...body.querySelectorAll('h1, h2, h3, h4, h5, h6, p')]
    .filter(el => shown(el) && !el.closest('.lem-page-actions'))
    .map(el => ({name: name(el), text: el.textContent.trim().slice(0, 40), boxes: textBoxes(el)}))
  // Wider than the screen: what makes the page scroll sideways, outside a box that scrolls itself.
  const inScroller = el => {
    for (let up = el.parentElement; up && up !== document.body; up = up.parentElement) {
      if (['auto', 'scroll', 'hidden', 'clip'].includes(getComputedStyle(up).overflowX)) return true
    }
    return false
  }
  const wide = [...document.body.querySelectorAll('*')]
    .filter(el => shown(el) && !inScroller(el) && !el.closest('.md-sidebar, .md-search'))
    .filter(el => { const r = el.getBoundingClientRect(); return r.right > width + 0.5 || r.left < -0.5 })
    .slice(0, 8).map(name)
  // Cut text: a box that clips its own text, and text that runs past the screen's edge. A box
  // that scrolls its text (a code block, a wide table, a chart) cuts nothing.
  const cut = []
  for (const el of document.body.querySelectorAll('*')) {
    if (el.closest('pre, .md-typeset__scrollwrap, .lem-chart-drawn, .md-search, script, style')) continue
    if (!shown(el) || away(el.getBoundingClientRect())) continue
    const style = getComputedStyle(el)
    const clips = ['hidden', 'clip'].includes(style.overflowX) || style.textOverflow === 'ellipsis'
    const own = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())
    if (clips && el.textContent.trim() && el.scrollWidth > el.clientWidth + 1) {
      cut.push(name(el) + ' "' + el.textContent.trim().slice(0, 30) + '"')
    } else if (own && textBoxes(el).some(box => !away(box) && (box.right > width + 0.5 || box.x < -0.5))) {
      cut.push(name(el) + ' runs past the edge')
    }
  }
  const lead = document.querySelector('main .lead')
  return {
    width,
    document: document.documentElement.scrollWidth,
    wide,
    controls,
    texts,
    cut: [...new Set(cut)].slice(0, 8),
    lead: lead ? parseFloat(getComputedStyle(lead).fontSize) : null,
  }
}"""


def meets(one: dict[str, float], other: dict[str, float]) -> bool:
    """Whether two boxes share an area."""
    return (
        one["x"] < other["right"] - SLACK
        and other["x"] < one["right"] - SLACK
        and one["y"] < other["bottom"] - SLACK
        and other["y"] < one["bottom"] - SLACK
    )


def same_line(one: dict[str, float], other: dict[str, float]) -> bool:
    """Whether two boxes share a band of the page's height."""
    return one["y"] < other["bottom"] - SLACK and other["y"] < one["bottom"] - SLACK


def faults(page: str, width: int, found: dict[str, Any]) -> list[str]:
    """What is wrong on one page at one width, a line for each fault."""
    lines = []
    if found["document"] > width:
        lines.append(
            f"{page}: the page is {found['document']} px wide on a {width} px screen "
            f"({', '.join(found['wide']) or 'no element found'})"
        )
    touches = same_line if width < OWN_LINE_WIDTH else meets
    lines.extend(
        f"{page}: {control['name']} stands on the line of {text['name']} "
        f'"{text["text"]}"'
        for control in found["controls"]
        for text in found["texts"]
        if any(touches(control["box"], box) for box in text["boxes"])
    )
    if len(found["controls"]) > 1:
        lines.append(f"{page}: {len(found['controls'])} page controls, not one")
    if width <= PHONE_WIDTH and found["lead"] and found["lead"] > LEAD_MOST_PX:
        lines.append(f"{page}: the lead is {found['lead']} px on a {width} px phone")
    lines.extend(f"{page}: text cut, {cut}" for cut in found["cut"])
    return lines


@pytest.fixture(scope="module")
def site(tmp_path_factory: pytest.TempPathFactory) -> Iterator[tuple[str, list[str]]]:
    """The built site on a loopback address, and the path of each page under it."""
    result = built.build(tmp_path_factory.mktemp("site-layout"))
    assert result.code == 0, result.said

    class Quiet(SimpleHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:  # noqa: A002
            pass

    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), partial(Quiet, directory=str(result.root))
    )
    Thread(target=server.serve_forever, daemon=True).start()
    try:
        # A page at an old address of a guide only leads to the guide, which the loop opens.
        paths = [
            built.name_of(result.root, page).removesuffix("index.html")
            for page in built.pages(result.root)
            if 'http-equiv="refresh"' not in page.read_text(encoding="utf-8")
        ]
        yield f"http://127.0.0.1:{server.server_address[1]}/", paths
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.parametrize("dark", [False, True], ids=["light", "dark"])
@pytest.mark.parametrize("screen", SCREENS, ids=[f"{w}x{h}" for w, h in SCREENS])
def test_every_page_fits_the_screen(
    site: tuple[str, list[str]],
    window: OpenWindow,
    tmp_path: Path,
    screen: tuple[int, int],
    *,
    dark: bool,
) -> None:
    address, paths = site
    width, height = screen
    shots = Path(os.environ.get("SITE_LAYOUT_SHOTS") or tmp_path)
    shots.mkdir(parents=True, exist_ok=True)
    page = window(screen, phone=width < 1024, dark=dark).pages[0]
    found: list[str] = []
    for path in paths:
        got = page.goto(address + path, wait_until="load")
        assert got is not None
        assert got.ok, path
        page.wait_for_load_state("networkidle")
        found += faults(path or "index.html", width, page.evaluate(MEASURE))
        stem = path.strip("/").replace("/", "-").removesuffix(".html") or "landing"
        page.screenshot(
            path=shots / f"{stem}-{width}x{height}-{'dark' if dark else 'light'}.png",
            full_page=True,
            animations="disabled",
        )
    assert not found, "\n".join(found)
