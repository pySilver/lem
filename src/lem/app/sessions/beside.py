"""What the terminal's and the harness's adapters give beside their ports, which a task's session
needs: a session's new name, the program in its main pane, a line still in its mailbox, and the
folder `--plugin-dir` names.

`notes/sessions.md` asks `core` to put them on the ports (`Terminal.rename`, `Pane.agent`, a read
of the mailbox, `Harness.plugin_folder`). Until then a use case takes them here, and a terminal or
a harness that lacks them is a fault that names what it lacks, never a session run without them.
"""

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from lem.kernel.errors import Fault

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

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
class Plugins(Protocol):
    """The harness's folder for `--plugin-dir`, None where the project loads the installed
    plugin."""

    def plugin_folder(self, plugin_dir: Path) -> Path | None: ...


def looks(terminal: object) -> Looks:
    """The terminal's looks; a fault for a terminal that has none."""
    if isinstance(terminal, Looks):
        return terminal
    raise Fault(
        f"{type(terminal).__name__} gives no rename, foregrounds or waiting: a task's "
        "session needs them beside the Terminal port (notes/sessions.md)"
    )


def plugins(harness: object) -> Plugins:
    """The harness's plugin folder; a fault for a harness that has none."""
    if isinstance(harness, Plugins):
        return harness
    raise Fault(
        f"{type(harness).__name__} gives no plugin_folder: a task's session needs it "
        "beside the Harness port (notes/sessions.md)"
    )
