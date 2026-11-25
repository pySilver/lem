"""The handler of a term while the checks run (`land.cmd_checks` on `main`): `--stop` sends the
run a term, which stops it from the gate to its judgment; once the run is judged, a term
changes nothing, and its result is kept whole."""

import contextlib
import dataclasses
import signal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Generator


@dataclasses.dataclass(kw_only=True, slots=True)
class Stopper:
    """Stops the run with `InterruptedError` once, until it is `done`: a second term while
    the first is handled (the cleanup of a command that ignores a term) changes nothing, so
    that the cleanup ends what the command started (`land.cmd_checks` on `main`)."""

    done: bool = False
    stopping: bool = False

    def __call__(self, number: int, _frame: object) -> None:
        """Stop the run, unless it is judged or stopping already."""
        if self.done or self.stopping:
            return
        self.stopping = True
        raise InterruptedError(number)

    @contextlib.contextmanager
    def held(self) -> Generator[None]:
        """The handler holds while the step runs, and the one before it after."""
        before = signal.signal(signal.SIGTERM, self)
        try:
            yield
        finally:
            signal.signal(signal.SIGTERM, before)
