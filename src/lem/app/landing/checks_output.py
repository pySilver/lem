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


class Cut(InterruptedError):
    """A stop while a command ran: what the command wrote up to its end, and the outcomes of
    the run so far, its own last."""

    def __init__(
        self, number: int, body: bytes, outcomes: tuple[object, ...] = ()
    ) -> None:
        """Keep the signal, the output and the outcomes."""
        super().__init__(number)
        self.number = number
        self.body = body
        self.outcomes = outcomes


def waited(argv: list[str], cwd: Path, output: IO[bytes], grace: float) -> int:
    """Run `argv` in its group, and give its exit code once the group ended."""
    with grouped(argv, cwd, output, grace) as proc:
        return proc.wait()


def ended(argv: list[str], cwd: Path, grace: float) -> tuple[int, bytes]:
    """Run `argv` in its group, and give its exit code and output, once the group ended; a
    stop gives what the command wrote up to its end, in a `Cut`."""
    with tempfile.TemporaryFile() as output:
        try:
            code = waited(argv, cwd, output, grace)
        except InterruptedError as stop:
            output.seek(0)
            raise Cut(stop.args[0], output.read()) from None
        output.seek(0)
        return code, output.read()
