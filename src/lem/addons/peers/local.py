"""Read the names Tailscale reports without starting a service."""

import os
import subprocess

import msgspec

from lem.adapters import tailscale_cli
from lem.addons.peers.tailnet import Status
from lem.kernel.errors import Refusal

# The peer client's established time to wait for a connection (main, 2026-11-25).
STATUS_SECONDS = 4


def executable() -> str:
    """Find the Tailscale CLI for this process."""
    found = tailscale_cli.executable(os.environ)
    if found is None:
        raise unreadable()
    return found


def status() -> Status:
    """Read Tailscale's local status without starting a service."""
    command = executable()
    try:
        ran = tailscale_cli.run(command, ("status", "--json"), STATUS_SECONDS)
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
