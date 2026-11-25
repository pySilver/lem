"""The levels of Lem's tests (the design's part 8), and what each one runs.

A level is a folder of `tests/`, but `gates`, whose cases are `tests/gates.py`, and `full`, every
level whose folder exists. The entry gives pytest only what this module chose.
"""

import fcntl
import sys
from contextlib import AbstractContextManager, contextmanager, nullcontext
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

# The levels with a folder of their own, in the order a full run takes them.
FOLDERS = ("unit", "model", "histories", "contract", "journeys", "hooks", "browser")
LEVELS = ("gates", *FOLDERS, "full")
# One full run at a time on a machine: two at once took the load average over 400 and slowed
# every time-bound check (the design's part 8). A fixed path, read before the entry sets TMPDIR.
FULL_LOCK = Path("/tmp/lem-full-run.lock")


class WrongCall(Exception):
    """A selection the entry refuses, with the line that says why and what to run instead."""


def selection(tests: Path, level: str, paths: list[str]) -> list[str]:
    """What pytest collects for `level`: PATHS when the level takes them, each a file or folder
    inside the level's folder (a file may name a case after `::`), else the level's folder."""
    gates = str(tests / "gates.py")
    if level in {"gates", "full"}:
        if paths:
            raise WrongCall(
                f"--level {level} takes no paths: run it alone, or name a level "
                "with a folder (--level unit tests/unit/core)"
            )
        folders = (tests / name for name in FOLDERS if (tests / name).is_dir())
        return [gates] if level == "gates" else [gates, *map(str, folders)]
    folder = tests / level
    if not folder.is_dir():
        raise WrongCall(f"{folder} does not exist: the level {level} has no case yet")
    return [inside(folder, path) for path in paths] or [str(folder)]


def inside(folder: Path, path: str) -> str:
    """`path` made absolute, when its file or folder is in `folder`."""
    where, *case = path.split("::")
    resolved = Path(where).resolve()
    if not resolved.exists():
        raise WrongCall(f"{resolved} does not exist: name a file or folder of {folder}")
    if not resolved.is_relative_to(folder):
        raise WrongCall(
            f"{resolved} is not in {folder}: run it with the level of its folder"
        )
    return "::".join((str(resolved), *case))


@contextmanager
def full_run_lock(path: Path) -> Iterator[None]:
    """Hold the machine's lock of a full run; wait, and say so, while another run holds it."""
    with path.open("a") as held:
        try:
            fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(
                f"waits for the full run that holds {path}", file=sys.stderr, flush=True
            )
            fcntl.flock(held, fcntl.LOCK_EX)
        yield


def lock_of(level: str) -> AbstractContextManager[None]:
    """The full run's lock for `--level full`, and none for any other level."""
    return full_run_lock(FULL_LOCK) if level == "full" else nullcontext()
