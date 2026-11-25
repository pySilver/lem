"""A headless Chromium window with the test's own profile and keychain."""

import os
import pwd
import sys
from pathlib import Path

DESKTOP = (1440, 900)
PHONE = (390, 844)
INSTALL = ".venv/bin/playwright install chromium"


def dimensions(shot: bytes) -> tuple[int, int]:
    assert shot[:8] == b"\x89PNG\r\n\x1a\n"
    return int.from_bytes(shot[16:20]), int.from_bytes(shot[20:24])


def installed(launch_dir: Path) -> str:
    """Locate Playwright's installed browser, even when the test entry gives us a new home."""
    cache_path = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if cache_path == "0":
        return cache_path
    if cache_path:
        npm_dir = os.environ.get("INIT_CWD") or ""
        return str((launch_dir / npm_dir / cache_path).resolve())
    home = Path(pwd.getpwuid(os.getuid()).pw_dir)
    cache = (
        home / "Library" / "Caches"
        if sys.platform == "darwin"
        else (
            Path(os.environ["XDG_CACHE_HOME"])
            if "XDG_CACHE_HOME" in os.environ
            else home / ".cache"
        )
    )
    return str(cache / "ms-playwright")
