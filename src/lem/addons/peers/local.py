"""Read the names Tailscale reports without starting a service."""

import subprocess

import msgspec

from lem.addons.peers.tailnet import Status
from lem.kernel.errors import Refusal

# The peer client's established time to wait for a connection (main, 2026-11-25).
STATUS_SECONDS = 4


def status() -> Status:
    """Read Tailscale's local status without starting a service."""
    try:
        ran = subprocess.run(
            ["tailscale", "status", "--json"],
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
