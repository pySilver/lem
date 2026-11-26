"""The Tailscale calls of the board and their refusals.

A home folder of Lem that is not the owner's (a test's, a trial's) never runs the machine's own
CLI: it runs the one `LEM_TAILSCALE` names, or none, as it never takes the owner's two ports, so
that nothing it runs reads or changes the entries of his tailnet.
"""

import subprocess
from typing import TYPE_CHECKING

from lem.adapters import tailscale_cli
from lem.board import machine
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from collections.abc import Mapping

# How long one call of the CLI may take. A guess.
WAIT = 20.0
LISTED = ", ".join(tailscale_cli.PLACES)
STILL_LOCAL = "the board still serves this Mac at its own address"


def cli(environ: Mapping[str, str]) -> str | None:
    """The CLI this home folder may run, or None when there is none."""
    named = environ.get(tailscale_cli.NAMED)
    if named or not machine.owners_home(environ):
        return named or None
    return tailscale_cli.executable(environ)


def needed(environ: Mapping[str, str]) -> str:
    """The CLI; refused when this Mac has none for this home folder."""
    found = cli(environ)
    if found is None:
        raise Refusal(
            "no-tailscale",
            f"no tailscale CLI for this home folder of Lem (PATH, {LISTED}; "
            f"a home that is not the owner's runs only the one {tailscale_cli.NAMED} names)",
            "the owner installs Tailscale on this Mac and on the phone and signs both in "
            f"with his account; {STILL_LOCAL}",
        )
    return found


def asked(path: str, words: tuple[str, ...], wait: float = WAIT) -> bytes:
    """What `tailscale WORDS` prints; refused when it does not run or fails."""
    joined = " ".join(words)
    said = f"tailscale {joined}"
    try:
        ran = tailscale_cli.run(path, words, wait)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise Refusal(
            "tailscale",
            f"{said} did not run ({error})",
            f"open Tailscale; {STILL_LOCAL}",
        ) from error
    if ran.returncode:
        told = (ran.stderr or ran.stdout).decode(errors="replace").strip()
        raise Refusal(
            "tailscale", f"{said} failed: {told}", f"connect Tailscale; {STILL_LOCAL}"
        )
    return ran.stdout.strip() or b"{}"


def door_address(port: int) -> str:
    """The door's listener on this Mac, which the tailnet's entry proxies to."""
    return f"http://127.0.0.1:{port}"
