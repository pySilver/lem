"""The standard-library transport for the Stop hook and the agterm adapter."""

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

TOOL = "agtermctl"
SOCKETS = ("AGTERM_SOCKET", "AGT_SOCKET")
WINDOWS = ("AGTERM_WINDOW_ID", "AGT_WINDOW_ID")


def flagged(
    flag: str, environ: Mapping[str, str], names: tuple[str, ...]
) -> tuple[str, ...]:
    """The flag and first configured value, or no arguments."""
    given = [environ[name] for name in names if environ.get(name)]
    return (flag, given[0]) if given else ()


def run(
    environ: Mapping[str, str],
    words: tuple[str, ...],
    *,
    window: bool,
    stdin: str | None,
    timeout: float | None,
) -> subprocess.CompletedProcess[str]:
    """Call agtermctl with the socket and window of this environment."""
    sockets = flagged("--socket", environ, SOCKETS)
    windows = flagged("--window", environ, WINDOWS) if window else ()
    return subprocess.run(
        [TOOL, *words, *sockets, *windows],
        env=dict(environ),
        input=stdin,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def ask_environment(environ: Mapping[str, str]) -> Mapping[str, str]:
    """Put the agtermctl selected for question overlays first on PATH."""
    selected = environ.get("AGTERMCTL")
    if not selected:
        return environ
    path = Path(selected).expanduser().resolve()
    if path.name != TOOL:
        raise ValueError("AGTERMCTL must name the agtermctl executable")
    old = environ.get("PATH", "")
    return {**environ, "PATH": f"{path.parent}:{old}"}
