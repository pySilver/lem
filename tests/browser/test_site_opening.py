"""The public site's first screen, in both palettes."""

from typing import TYPE_CHECKING

import pytest

from browser.board_ui import in_screen
from unit.guides import built

if TYPE_CHECKING:
    from browser.conftest import OpenWindow

# The first screen of the site on main (tests/test-site.sh).
SCREEN = (1280, 800)


@pytest.fixture(scope="module")
def homepage(tmp_path_factory: pytest.TempPathFactory) -> str:
    result = built.build(tmp_path_factory.mktemp("public-site"))
    assert result.code == 0, result.said
    return (result.site / "index.html").as_uri()


@pytest.mark.parametrize("dark", [False, True], ids=["light", "dark"])
def test_install_and_agterm_fit_on_the_first_screen(
    homepage: str, window: OpenWindow, *, dark: bool
) -> None:
    page = window(SCREEN, dark=dark).pages[0]
    page.goto(homepage)
    for part in (
        page.locator(".lem-lead"),
        page.locator(".lem-for"),
        page.locator(".lem-sub"),
        page.locator(".lem-home pre").first,
        page.locator(".lem-home p").filter(has_text="Lem needs agterm."),
    ):
        in_screen(part, SCREEN)
