"""Read the names Tailscale reports without starting a service."""

import os
import shutil
import subprocess
from pathlib import Path

import msgspec

from lem.addons.peers.tailnet import Status
from lem.kernel.errors import Refusal

# The peer client's established time to wait for a connection (main, 2026-11-25).
STATUS_SECONDS = 4
# Install locations checked on main, 2026-11-25.
TAILSCALE_PLACES = (
    "/usr/local/bin/tailscale",
    "/Applications/Tailscale.app/Contents/MacOS/Tailscale",
    "/opt/homebrew/bin/tailscale",
)


def executable() -> str:
    """Find Tailscale on PATH, or in one of its install locations."""
    found = shutil.which("tailscale")
    if found:
        return str(Path(found).absolute())
    installed = next(
        (
            place
            for place in TAILSCALE_PLACES
            if Path(place).is_file() and os.access(place, os.X_OK)
        ),
        None,
    )
    if installed is None:
        raise unreadable()
    return installed


def status() -> Status:
    """Read Tailscale's local status without starting a service."""
    command = executable()
    try:
        ran = subprocess.run(
            [command, "status", "--json"],
            capture_output=True,
            check=False,
            timeout=STATUS_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise unreadable() from error
    if ran.returncode:
        raise unreadable()
    try:
        return msgspec.json.decode(ran.stdout, type=Status)
    except msgspec.DecodeError as error:
        raise unreadable() from error


def unreadable() -> Refusal:
    """The owner must connect before using the tailnet."""
    return Refusal(
        "tailnet", "the owner's Tailscale status did not read", "connect to Tailscale"
    )
