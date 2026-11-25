"""The browser level's Chromium contexts, screenshot output and test server."""

from contextlib import ExitStack
from typing import TYPE_CHECKING, Protocol

import pytest
from playwright.sync_api import Error, sync_playwright

from browser import chromium
from browser.server import Board, serve

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from playwright.sync_api import BrowserContext, Playwright


class OpenWindow(Protocol):
    def __call__(
        self,
        screen: tuple[int, int] = chromium.DESKTOP,
        *,
        phone: bool = False,
        dark: bool = False,
        scale: int = 1,
        scripts: bool = True,
    ) -> BrowserContext: ...


@pytest.fixture(scope="session")
def playwright(pytestconfig: pytest.Config) -> Iterator[Playwright]:
    with pytest.MonkeyPatch.context() as patch:
        launch_dir = pytestconfig.invocation_params.dir
        patch.setenv("PLAYWRIGHT_BROWSERS_PATH", chromium.installed(launch_dir))
        with sync_playwright() as driver:
            yield driver


@pytest.fixture
def window(tmp_path: Path, playwright: Playwright) -> Iterator[OpenWindow]:
    with ExitStack() as contexts:
        profiles = iter(range(100))

        def opened(
            screen: tuple[int, int] = chromium.DESKTOP,
            *,
            phone: bool = False,
            dark: bool = False,
            scale: int = 1,
            scripts: bool = True,
        ) -> BrowserContext:
            width, height = screen
            # The headless shell needs no Chrome for Testing app bundle. Playwright
            # selects the shell when headless is true and no channel is set.
            try:
                found = playwright.chromium.launch_persistent_context(
                    tmp_path / f"profile-{next(profiles)}",
                    headless=True,
                    args=[
                        "--use-mock-keychain",
                        "--disable-background-networking",
                        "--no-proxy-server",
                    ],
                    viewport={"width": width, "height": height},
                    user_agent=playwright.devices["Pixel 7"]["user_agent"]
                    if phone
                    else None,
                    is_mobile=phone,
                    has_touch=phone,
                    color_scheme="dark" if dark else "light",
                    device_scale_factor=scale,
                    java_script_enabled=scripts,
                    timezone_id="UTC",
                )
            except Error as error:
                if "Executable doesn't exist at " in str(error):
                    pytest.fail(
                        f"Chromium is missing. Run {chromium.INSTALL} from Lem's checkout."
                    )
                raise
            contexts.callback(found.close)
            found.set_default_timeout(5000)
            return found

        yield opened


@pytest.fixture
def board(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Board]:
    with serve(tmp_path, monkeypatch) as running:
        yield running
