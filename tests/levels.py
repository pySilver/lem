"""The levels of Lem's tests (the design's part 8), and what each one runs.

A level is a folder of `tests/`, but `gates`, whose cases are `tests/gates.py`, and `full`, every
level whose folder exists. The entry gives pytest only what this module chose.
"""

import fcntl
import sys
from contextlib import AbstractContextManager, contextmanager, nullcontext
from pathlib import Path
from typing import TYPE_CHECKING

from lem.store.places import common_dir

if TYPE_CHECKING:
    from collections.abc import Iterator

# The levels with a folder of their own, in the order a full run takes them.
FOLDERS = ("unit", "model", "histories", "contract", "journeys", "hooks", "browser")
# A level's other folders: the ledger's check is a unit case of its own folder.
BESIDE = (("unit", ("ledger",)),)
LEVELS = ("gates", *FOLDERS, "full")
# The unit level runs on this many pytest-xdist workers: the 72 cases of tests/unit/core took
# 19.1 s in one process and 9.5 s on four (2026-11-25, the owner's Mac, load average 6 to 8).
WORKERS = 4
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
        folders = [str(found) for name in FOLDERS for found in folders_of(tests, name)]
        return [gates] if level == "gates" else [gates, *folders]
    folders = folders_of(tests, level)
    if not folders:
        raise WrongCall(
            f"{tests / level} does not exist: the level {level} has no case yet"
        )
    return [inside(folders, path) for path in paths] or [
        str(found) for found in folders
    ]


def folders_of(tests: Path, level: str) -> list[Path]:
    """The folders of `level` that exist: its own, and those `BESIDE` gives it."""
    beside = next((names for name, names in BESIDE if name == level), ())
    named = (tests / name for name in (level, *beside))
    return [folder for folder in named if folder.is_dir()]


def inside(folders: list[Path], path: str) -> str:
    """`path` made absolute, when its file or folder is in one of `folders`."""
    where, *case = path.split("::")
    resolved = Path(where).resolve()
    shown = ", ".join(map(str, folders))
    if not resolved.exists():
        raise WrongCall(f"{resolved} does not exist: name a file or folder of {shown}")
    if not any(resolved.is_relative_to(folder) for folder in folders):
        raise WrongCall(
            f"{resolved} is not in {shown}: run it with the level of its folder"
        )
    return "::".join((str(resolved), *case))


def real_state(tests: Path) -> Path | None:
    """The state folder of the checkout the tests are in (its main checkout, from a worktree
    too), which the owner's board server reads; None outside a repository."""
    found = next(
        (above / ".git" for above in tests.parents if (above / ".git").exists()), None
    )
    return None if found is None else common_dir(found).parent / ".lem" / "state"


def listing(state: Path | None) -> frozenset[str]:
    """What a run must leave as it found in the checkout's own state: the task folders, the
    files of this Lem's form in them, and its marker and claim lock."""
    if state is None or not (state / "tasks").is_dir():
        return frozenset()
    tasks = state / "tasks"
    found = {f"tasks/{entry.name}" for entry in tasks.iterdir()}
    found |= {
        str(path.relative_to(state))
        for name in ("task.json", "task.lock", "step.lock", "sessions.jsonl")
        for path in tasks.glob(f"*/{name}")
    }
    found |= {
        name
        for name in ("lem-state.json", "locks/workspace.lock")
        if (state / name).exists()
    }
    return frozenset(found)


def changed(state: Path | None, before: frozenset[str]) -> str | None:
    """The line that names what a run added to or removed from the checkout's own state."""
    after = listing(state)
    if after == before:
        return None
    added, removed = sorted(after - before), sorted(before - after)
    return (
        f"FAIL the run changed the checkout's own Lem state {state}: "
        f"added {', '.join(added) or 'nothing'}; removed {', '.join(removed) or 'nothing'}"
    )


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


def parallel(level: str, *, snapshots: bool) -> list[str]:
    """pytest's arguments for xdist's workers: the unit level's, but when inline-snapshot
    writes values, which it does in one process only."""
    if level != "unit" or snapshots:
        return []
    return ["-p", "xdist", "--numprocesses", str(WORKERS)]


def lock_of(level: str) -> AbstractContextManager[None]:
    """The full run's lock for `--level full`, and none for any other level."""
    return full_run_lock(FULL_LOCK) if level == "full" else nullcontext()
