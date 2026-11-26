"""Find and run the Tailscale CLI, including the one inside the macOS app."""

import os
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

NAMED = "LEM_TAILSCALE"
PLACES = (
    "/usr/local/bin/tailscale",
    "/opt/homebrew/bin/tailscale",
    "/Applications/Tailscale.app/Contents/MacOS/Tailscale",
)


def executable(environ: Mapping[str, str]) -> str | None:
    """Use the named CLI, then PATH and the usual install locations."""
    named = environ.get(NAMED)
    if named:
        return named
    found = shutil.which("tailscale", path=environ.get("PATH", os.defpath))
    if found:
        return str(Path(found).absolute())
    return next((path for path in PLACES if shutil.which(path)), None)


def run(
    path: str, words: tuple[str, ...], wait: float
) -> subprocess.CompletedProcess[bytes]:
    """Force CLI mode even when the path leads to the app through a symlink."""
    return subprocess.run(
        [path, *words],
        capture_output=True,
        check=False,
        timeout=wait,
        env={**os.environ, "TAILSCALE_BE_CLI": "1"},
    )
