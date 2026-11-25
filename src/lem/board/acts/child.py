"""A command of Lem that an act runs as a process of its own: one whose package the board may not
import (an add-on's, the top row of the design's part 2, beside the board), run by this install's
interpreter, as `board/start.py` runs the server, with the automatic start of the server off.
"""

import os
import subprocess
import sys
from typing import TYPE_CHECKING

import msgspec

from lem.kernel import paths
from lem.kernel.envelope import Envelope
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from pathlib import Path

# How long such a command may take, in seconds: one write of a few files (a guess).
TIMEOUT = 60
# The last characters of what a command that printed no envelope wrote to its errors.
TAIL = 200


def command(checkout: Path, words: tuple[str, ...]) -> list[str]:
    """`lem --repo CHECKOUT WORDS` of this interpreter, with no bytecode written, no unsafe
    folder on the path, and no user site."""
    return [
        sys.executable,
        "-B",
        "-P",
        "-s",
        "-m",
        "lem",
        "--repo",
        str(checkout),
        *words,
    ]


def finished(
    checkout: Path, words: tuple[str, ...]
) -> subprocess.CompletedProcess[bytes]:
    """Run the command to its end; refused when it took over TIMEOUT."""
    package = str(paths.PACKAGE.parent)
    environ = {**os.environ, "PYTHONPATH": package, "LEM_SERVE": "off"}
    try:
        return subprocess.run(
            command(checkout, words),
            capture_output=True,
            check=False,
            cwd=checkout,
            env=environ,
            timeout=TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        shown = " ".join(words)
        why = f"lem {shown} did not end in {TIMEOUT} seconds"
        raise Refusal("child", why, "run it in a session") from None


def ran(checkout: Path, *words: str) -> Envelope:
    """The envelope the command printed; refused when it printed none."""
    done = finished(checkout, words)
    try:
        return msgspec.json.decode(done.stdout, type=Envelope)
    except msgspec.DecodeError:
        shown = " ".join(words)
        said = done.stderr.decode(errors="replace").strip()[-TAIL:]
        why = f"lem {shown} printed no envelope: {said}"
        raise Refusal("child", why, "run it in a session") from None
