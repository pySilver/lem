"""Find an Inbox the owner already started, through its status command."""

import shutil
import subprocess

import httpx
import msgspec

from lem.addons.inbox.messages import Door

# The status command's time limit in main, 2026-11-25.
SECONDS = 60


def status() -> Door:
    """Check the local status, with no command that can start the Inbox."""
    program = shutil.which("plannotator")
    if not program:
        return Door(why="not installed")
    try:
        ran = subprocess.run(
            [program, "inbox", "status", "--json"],
            capture_output=True,
            timeout=SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return Door(why="failed", said=str(error))
    if ran.returncode:
        return stopped(ran.returncode, ran.stderr.decode(errors="replace").strip())
    return read(ran.stdout)


def stopped(code: int, said: str) -> Door:
    """Report the CLI's absent and unresponsive outcomes."""
    reasons = {1: "not running", 2: "not answering"}
    return Door(why=reasons.get(code, "failed"), said=said)


def read(raw: bytes) -> Door:
    """Only loopback HTTP can receive the local protocol's calls."""
    try:
        found = msgspec.json.decode(raw, type=Door)
    except msgspec.DecodeError:
        return Door(why="failed", said="the Inbox status gave no JSON")
    if not found.running or not local(found.url):
        return Door(why="not answering", said="the Inbox named no loopback address")
    return msgspec.structs.replace(
        found, why=None if found.tailnet_url else "no tailnet address"
    )


def local(given: str | None) -> bool:
    """Reject redirects and any status address off this machine."""
    try:
        url = httpx.URL(given or "")
    except httpx.InvalidURL:
        return False
    return (
        url.scheme == "http"
        and url.host in {"127.0.0.1", "::1"}
        and not url.userinfo
        and url.port not in {None, 4536, 4537}
    )
