"""The release notice fits both board widths and stays closed after a reload."""

from typing import TYPE_CHECKING

import pytest
from playwright.sync_api import expect

from browser.board_ui import in_screen, visit
from browser.chromium import DESKTOP, PHONE
from lem.board import update, update_record
from lem.kernel import release

if TYPE_CHECKING:
    from pathlib import Path

    from browser.conftest import OpenWindow
    from browser.server import Board


@pytest.mark.parametrize("screen", (PHONE, DESKTOP), ids=("phone", "desktop"))
def test_the_update_note_fits_and_stays_closed(
    board: Board, window: OpenWindow, tmp_path: Path, screen: tuple[int, int]
) -> None:
    version = release.running()
    # The record as a server of 0.4.0 left it, and the start of this release after it.
    home = tmp_path / "lem-home"
    update.started(home, "0.4.0")
    update.started(home, version)
    phone = screen == PHONE
    page = window(screen, phone=phone).pages[0]
    address = board.task("coupon-has-a-slug") if phone else f"{board.url}/"
    visit(page, address)
    note = page.get_by_text(f"Lem was updated to {version}", exact=True)
    expect(note).to_be_visible()
    expect(page.get_by_text("Replaces 0.4.0.", exact=True)).to_be_visible()
    in_screen(note, screen)
    close = page.get_by_role("button", name="Close the update notice")
    in_screen(close, screen)
    close.click()
    expect(note).to_be_hidden()
    with page.expect_response("**/api/server/update") as asked:
        page.reload()
    assert asked.value.request.method == "GET"
    assert asked.value.status == 204
    expect(note).to_be_hidden()


def test_a_record_that_does_not_read_shows_its_line(
    board: Board, window: OpenWindow, tmp_path: Path
) -> None:
    (tmp_path / "lem-home" / update_record.STATE).write_bytes(b"{")
    page = window(DESKTOP).pages[0]
    visit(page, f"{board.url}/")
    expect(
        page.get_by_text("Lem could not keep its update notice", exact=True)
    ).to_be_visible()
    expect(page.get_by_text(f"{update_record.STATE} does not read")).to_be_visible()
