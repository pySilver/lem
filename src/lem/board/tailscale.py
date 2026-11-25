"""The `tailscale` CLI of this Mac, by its absolute path: the one on PATH, else the first of
PLACES, since a process started with a short PATH has none of them (`serve.TAILSCALE_PLACES` on
`main`).

A home folder of Lem that is not the owner's (a test's, a trial's) never runs the machine's own
CLI: it runs the one `LEM_TAILSCALE` names, or none, as it never takes the owner's two ports, so
that nothing it runs reads or changes the entries of his tailnet.
"""

import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from lem.board import machine
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from collections.abc import Mapping

PLACES = (
    "/usr/local/bin/tailscale",
    "/Applications/Tailscale.app/Contents/MacOS/Tailscale",
    "/opt/homebrew/bin/tailscale",
)
NAMED = "LEM_TAILSCALE"
# How long one call of the CLI may take. A guess.
WAIT = 20.0
LISTED = ", ".join(PLACES)
STILL_LOCAL = "the board still serves this Mac at its own address"


def cli(environ: Mapping[str, str]) -> str | None:
    """The CLI this home folder may run, by its absolute path; None when there is none."""
    named = environ.get(NAMED, "")
    if named or not machine.owners_home(environ):
        return named or None
    found = shutil.which("tailscale")
    if found:
        return str(Path(found).absolute())
    usable = (place for place in PLACES if Path(place).is_file())
    return next(usable, None)


def needed(environ: Mapping[str, str]) -> str:
    """The CLI; refused when this Mac has none for this home folder."""
    found = cli(environ)
    if found is None:
        raise Refusal(
            "no-tailscale",
            f"no tailscale CLI for this home folder of Lem (PATH, {LISTED}; "
            f"a home that is not the owner's runs only the one {NAMED} names)",
            "the owner installs Tailscale on this Mac and on the phone and signs both in "
            f"with his account; {STILL_LOCAL}",
        )
    return found


def asked(path: str, words: tuple[str, ...], wait: float = WAIT) -> bytes:
    """What `tailscale WORDS` prints; refused when it does not run or fails."""
    joined = " ".join(words)
    said = f"tailscale {joined}"
    try:
        ran = subprocess.run(
            [path, *words], capture_output=True, check=False, timeout=wait
        )
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
