"""A headless Chromium window with the test's own profile and keychain."""

import os
import pwd
import sys
from pathlib import Path

DESKTOP = (1440, 900)
PHONE = (390, 844)
INSTALL = ".venv/bin/playwright install chromium"


def installed() -> str:
    """Locate Playwright's installed browser, even when the test entry gives us a new home."""
    if "PLAYWRIGHT_BROWSERS_PATH" in os.environ:
        return os.environ["PLAYWRIGHT_BROWSERS_PATH"]
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
