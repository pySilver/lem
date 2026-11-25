"""Resolve the installed browser before the test's scratch directory matters."""

from typing import TYPE_CHECKING

import pytest

from browser.chromium import installed

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize("npm_dir", [None, "npm"])
def test_relative_browser_path_uses_the_install_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, npm_dir: str | None
) -> None:
    launch_dir = tmp_path / "checkout"
    install_dir = tmp_path / npm_dir if npm_dir else launch_dir
    if npm_dir:
        monkeypatch.setenv("INIT_CWD", str(install_dir))
    else:
        monkeypatch.delenv("INIT_CWD", raising=False)
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", ".browsers")
    assert installed(launch_dir) == str(install_dir / ".browsers")


def test_browser_path_zero_keeps_the_package_local_install(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", "0")
    assert installed(tmp_path) == "0"
