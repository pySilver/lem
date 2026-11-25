"""Take a phone screenshot over Chromium's DevTools connection."""

import re
from base64 import b64decode
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import quote

from playwright.sync_api import expect

from browser.chromium import PHONE, dimensions

if TYPE_CHECKING:
    from browser.conftest import OpenWindow

RECIPE = (
    Path(__file__).resolve().parents[2]
    / "skills/lem/harness/claude-code/take-screenshot.md"
)


def test_the_harness_devtools_steps_capture_a_phone_screenshot(
    window: OpenWindow,
) -> None:
    context = window()
    page = context.pages[0]
    session = context.new_cdp_session(page)
    metrics, touch, media, navigate, capture = re.findall(
        r"`((?:Emulation|Page)\.\w+)`", RECIPE.read_text(encoding="utf-8")
    )
    width, height = PHONE
    session.send(
        metrics,
        {"width": width, "height": height, "deviceScaleFactor": 2, "mobile": True},
    )
    session.send(touch, {"enabled": True})
    session.send(
        media, {"features": [{"name": "prefers-color-scheme", "value": "dark"}]}
    )
    address = "data:text/html," + quote(
        "<meta name=viewport content='width=device-width'><h1>Gift note</h1>"
    )
    session.send(navigate, {"url": address})
    expect(page.get_by_role("heading", name="Gift note")).to_be_visible()
    assert page.evaluate("matchMedia('(prefers-color-scheme: dark)').matches")
    assert page.evaluate("navigator.maxTouchPoints") > 0
    assert dimensions(b64decode(session.send(capture, {"format": "png"})["data"])) == (
        width * 2,
        height * 2,
    )
