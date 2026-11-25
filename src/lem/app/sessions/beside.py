"""The newest sign of a transcript's main thread, beside the harness port's signs."""

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from lem.kernel.errors import Fault

if TYPE_CHECKING:
    from datetime import datetime

    from lem.ports.harness import Transcript


@runtime_checkable
class MainSigns(Protocol):
    """The harness's newest sign of a transcript's main thread alone, beside its port's
    `signs` (which counts its subagents too)."""

    def main_sign(self, transcript: Transcript) -> datetime | None: ...


def main_signs(harness: object) -> MainSigns:
    """The harness's main-thread signs; a fault for a harness that has none."""
    if isinstance(harness, MainSigns):
        return harness
    raise Fault(
        f"{type(harness).__name__} gives no main_sign: a task's session needs it beside the "
        "Harness port (notes/sessions.md)"
    )
