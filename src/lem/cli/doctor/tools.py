"""The rows of a program on PATH: found or not, with its version; the GitHub CLI signed in or
not; cronn and whether its status answers; and the Python of Lem's app.
"""

import sys
from pathlib import Path
from typing import TYPE_CHECKING

import msgspec

from lem.cli.doctor import tool_words
from lem.cli.doctor.row import REQUIRED, Row

if TYPE_CHECKING:
    from lem.cli.doctor.look import Look

# The oldest Python Lem's app runs on.
OLDEST = (3, 14)
CRONN_PORT = "CRONN_PORT="


def version_of(look: Look, path: Path, probe: tuple[str, ...]) -> str | None:
    """The first line the program at `path` prints for `probe`; None with no probe."""
    if not probe:
        return None
    return look.first_line((str(path), *probe))


def tool_row(look: Look, tool: tool_words.Tool) -> Row:
    """The row of `tool`: where it is on PATH, and the version it prints."""
    path = look.which(tool.program)
    detail = None
    if path is not None:
        detail = version_of(look, path, tool.probe) or str(path)
    return Row(
        name=tool.name,
        need=tool.need,
        found=path is not None,
        detail=detail,
        used_for=tool.used_for,
        without_it=tool.without_it,
        guide=tool.guide,
    )


def gh_row(look: Look) -> Row:
    """The GitHub CLI, and whether it is signed in. Required, since every task lands through a
    GitHub pull request; a login that is missing is said in the row's detail."""
    row = tool_row(look, tool_words.GH)
    path = look.which(tool_words.GH.program)
    if path is None:
        return msgspec.structs.replace(row, signed_in=False)
    if look.succeeds((str(path), "auth", "status")):
        return msgspec.structs.replace(row, signed_in=True)
    detail = f"{row.detail}; not signed in: `gh auth login` signs it in"
    return msgspec.structs.replace(row, signed_in=False, detail=detail)


def cronn_folder(look: Look) -> Path:
    """cronn's folder: `CRONN_CONFIG_DIR`, else `~/.config/cronn`."""
    named = look.environ.get("CRONN_CONFIG_DIR")
    return Path(named) if named else look.home / ".config" / "cronn"


def cronn_port(look: Look) -> int | None:
    """The port of cronn's status, from `cronn.env` of its folder; None when no line names
    one."""
    try:
        text = (cronn_folder(look) / "cronn.env").read_text(
            encoding="utf-8", errors="replace"
        )
    except OSError:
        return None
    said = [line for line in text.splitlines() if line.startswith(CRONN_PORT)]
    if not said:
        return None
    port = said[-1].removeprefix(CRONN_PORT).strip().strip("\"'")
    return int(port) if port.isdigit() else None


def cronn_row(look: Look) -> Row:
    """cronn, and whether its status answers on this machine."""
    row = tool_row(look, tool_words.CRONN)
    port = cronn_port(look) if row.found else None
    answered = port is not None and look.status(port)
    return msgspec.structs.replace(row, running=answered)


def python_row(look: Look) -> Row:
    """The Python of Lem's app: the interpreter its commands and its hooks run under, which
    is the one that runs this check."""
    said = ".".join(map(str, sys.version_info[:3]))
    return Row(
        name="python3",
        need=REQUIRED,
        found=sys.version_info >= OLDEST,
        detail=f"Python {said} at {look.executable}, Lem's app's own",
        used_for=(
            "every command of Lem and the plugin's hooks, which run in the app's own Python"
        ),
        without_it=(
            "Lem's app is installed with a Python older than 3.14; the owner installs Lem "
            "again (`brew reinstall pySilver/tap/lem`)"
        ),
    )
