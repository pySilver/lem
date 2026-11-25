"""What the load gate reads of the machine: its load average, the clock, and this machine's
start number (`land.load_now` on `main`, `state.load_start` there)."""

import dataclasses
import os
import time
import tomllib
from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

# Lem's own start number, when the developer set none on this machine (`LOAD_START` on `main`).
START = 40.0
MACHINE = "machine.toml"
FIX = "lem settings set load.start 40 --machine sets a number; 0 takes the gate away"


def load_now() -> float:
    """The machine's load average of the last minute, as `uptime` gives it."""
    return round(os.getloadavg()[0], 1)


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class Gauges:
    """What the gate reads of the machine: its load average, the clock in seconds of the
    epoch, and the pause between two looks. A test gives its own."""

    load: Callable[[], float] = load_now
    clock: Callable[[], float] = time.time
    sleep: Callable[[float], None] = time.sleep


def start_number(home: Path) -> float | None:
    """This machine's `[load] start` of `machine.toml`, else Lem's 40; None for 0, when the
    developer took the gate away. A negative number is refused with the line that sets one.
    A stand-in until `settings/machine.py` reads it (`notes/land-checks.md`)."""
    path = home / MACHINE
    try:
        table = tomllib.loads(path.read_text(encoding="utf-8")).get("load", {})
    except FileNotFoundError:
        return START
    except tomllib.TOMLDecodeError as error:
        raise Refusal("machine", f"{path} is not TOML: {error}", FIX) from error
    number = table.get("start", START)
    if not isinstance(number, int | float) or number < 0:
        raise Refusal(
            "machine",
            f"load.start in {path} is {number!r}, and it is a load average above 0, or 0 "
            "for no gate",
            FIX,
        )
    return float(number) if number else None
