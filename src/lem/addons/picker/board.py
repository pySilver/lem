"""The board of the task picked, or of all tasks, opened as `lem board --follow` opens it: the
board server's page as a companion of the session, which needs no agent (`picker.open_board` on
`main`). It runs the command of this same install, as a process of its own."""

import subprocess
import sys
from typing import TYPE_CHECKING

import msgspec

from lem.addons.picker import row
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from pathlib import Path


class Said(msgspec.Struct, kw_only=True):
    """The refusal of a printed envelope, when it has one."""

    refusal: dict[str, str] | None = None


def opened(checkout: Path, chosen: str) -> None:
    """Open the board of the task `chosen`, or of all tasks for the last row; refused with the
    board's own words when it fails."""
    task = () if chosen == row.ALL else ("--task", chosen)
    words = ("--repo", str(checkout), "board", "--follow", *task)
    ran = subprocess.run(
        [sys.executable, "-B", "-P", "-s", "-m", "lem", *words],
        capture_output=True,
        text=True,
        check=False,
    )
    if ran.returncode:
        raise Refusal(
            "board", why_of(ran), "lem doctor says whether the board server runs"
        )


def why_of(ran: subprocess.CompletedProcess[str]) -> str:
    """Why the board did not open: its refusal's words, else its last line."""
    said = refusal_of(ran.stdout)
    told = ran.stderr or ran.stdout
    lines = told.strip().splitlines()
    last = lines[-1] if lines else f"lem board exited {ran.returncode}"
    return said.get("why", last)


def refusal_of(printed: str) -> dict[str, str]:
    """The refusal of the envelope `printed`, empty when it holds none or is no envelope."""
    try:
        envelope = msgspec.json.decode(printed or "{}", type=Said)
    except msgspec.DecodeError:
        return {}
    return envelope.refusal or {}
