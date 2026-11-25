"""One command of the checks in a process group of its own, its output to a file, and the group
ended however the wait for it ends: a term, its grace, then a kill for what is left (`land.
end_group` on `main`)."""

import contextlib
import os
import tempfile
from typing import IO, TYPE_CHECKING

from lem.kernel import procs

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path
    from subprocess import Popen

# How long a command's group has to end after its kill, and after its term unless the caller
# gives more, in seconds (`GRACE` on `main`).
GRACE = 1.0


@contextlib.contextmanager
def grouped(
    argv: list[str], cwd: Path, output: IO[bytes], grace: float
) -> Generator[Popen[bytes]]:
    """A command in a group of its own, its output to `output`; the group is ended however
    the wait for it ends."""
    proc = procs.start_group(argv, cwd, os.environ, output)
    try:
        yield proc
    finally:
        procs.stop_group(proc, grace, GRACE, whole_group=True)


def ended(argv: list[str], cwd: Path, grace: float) -> tuple[int, bytes]:
    """Run `argv` in its group, and give its exit code and output, once the group ended."""
    with tempfile.TemporaryFile() as output:
        with grouped(argv, cwd, output, grace) as proc:
            code = proc.wait()
        output.seek(0)
        return code, output.read()
