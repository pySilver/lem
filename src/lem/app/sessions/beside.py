"""What the terminal's and the harness's adapters give beside their ports, which a task's session
needs: a session's new name, the program in its main pane, a line still in its mailbox, and the
newest sign of a transcript's main thread.

`notes/sessions.md` asks `core` to put them on the ports (`Terminal.rename`, `Pane.agent`, a read
of the mailbox, a main-thread sign on `Signs`). Until then a use case takes them here, and a
terminal or a harness that lacks them is a fault that names what it lacks, never a session run
without them.
"""

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from lem.kernel.errors import Fault

if TYPE_CHECKING:
    from collections.abc import Mapping
    from datetime import datetime

    from lem.ports.harness import Transcript

# The words of the program in a session's main pane: empty for a shell that holds it, None while
# the terminal has not drawn the pane.
type Foreground = tuple[str, ...] | None


@runtime_checkable
class Looks(Protocol):
    """The terminal's looks beside its port."""

    def rename(self, session: str, name: str) -> None: ...
    def foregrounds(self) -> Mapping[str, Foreground]: ...
    def waiting(self, session: str, line: str) -> bool: ...


@runtime_checkable
class MainSigns(Protocol):
    """The harness's newest sign of a transcript's main thread alone, beside its port's
    `signs` (which counts its subagents too)."""

    def main_sign(self, transcript: Transcript) -> datetime | None: ...


def looks(terminal: object) -> Looks:
    """The terminal's looks; a fault for a terminal that has none."""
    if isinstance(terminal, Looks):
        return terminal
    raise Fault(
        f"{type(terminal).__name__} gives no rename, foregrounds or waiting: a task's "
        "session needs them beside the Terminal port (notes/sessions.md)"
    )


def main_signs(harness: object) -> MainSigns:
    """The harness's main-thread signs; a fault for a harness that has none."""
    if isinstance(harness, MainSigns):
        return harness
    raise Fault(
        f"{type(harness).__name__} gives no main_sign: a task's session needs it beside the "
        "Harness port (notes/sessions.md)"
    )
