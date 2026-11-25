"""Take a phone screenshot over Chromium's DevTools connection."""

from typing import TYPE_CHECKING

from browser.chromium import PHONE

if TYPE_CHECKING:
    from pathlib import Path

    from browser.conftest import OpenWindow


def test_the_harness_devtools_steps_capture_a_phone_screenshot(
    tmp_path: Path,
    window: OpenWindow,
) -> None:
    context = window(PHONE, phone=True, dark=True, scale=2)
    page = context.pages[0]
    page.set_content(
        "<meta name=viewport content='width=device-width'><h1>Gift note</h1>"
    )
    assert page.get_by_role("heading", name="Gift note").is_visible()
    image = tmp_path / "phone.png"
    page.screenshot(path=image)
    header = image.read_bytes()[:24]
    assert header.startswith(b"\x89PNG\r\n\x1a\n")
    assert (int.from_bytes(header[16:20]), int.from_bytes(header[20:24])) == (780, 1688)
