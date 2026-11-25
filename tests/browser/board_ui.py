"""Small actions shared by the board's browser cases."""

from typing import TYPE_CHECKING

from playwright.sync_api import expect

if TYPE_CHECKING:
    from playwright.sync_api import Locator, Page, Request

WAIT = 15000
RECEIPT = "refund-line-on-receipt"
STOCK = "stock-on-product-page"
GIFT = "gift-note-in-export"
CART = "cart-total-after-coupon"
ROUNDING = "refund-rounding"


def visit(page: Page, url: str, ready: str = "#stage", *, scripts: bool = True) -> None:
    got = page.goto(url, wait_until="load")
    assert got is not None and got.ok, url
    expect(page.locator(ready)).to_be_visible()
    if scripts:
        page.wait_for_function("Boolean(window.Turbo)")


def posts(page: Page) -> list[Request]:
    seen: list[Request] = []

    def record(request: Request) -> None:
        if request.method == "POST":
            seen.append(request)

    page.on("request", record)
    return seen


def box(part: Locator) -> tuple[float, float, float, float]:
    found = part.bounding_box()
    assert found is not None
    return found["x"], found["y"], found["width"], found["height"]


def in_screen(part: Locator, screen: tuple[int, int]) -> None:
    left, top, width, height = box(part)
    assert 0 <= left < left + width <= screen[0] + 1
    assert 0 <= top < top + height <= screen[1] + 1
