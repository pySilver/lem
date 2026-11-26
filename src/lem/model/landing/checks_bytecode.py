"""Which ignored `__pycache__` folders the checks remove before their first command
(`land.bytecode_candidates`, `folders_above` and `bytecode_of` on `main`).

An ignored `__pycache__` that was there before the run is a leftover of someone's Python (a
builder's test run without `-B`), not of the commands, and a suite that looks for bytecode would
go red on it with no defect of the code. Python rebuilds it from the source, so it goes; every
other ignored file stays, and a cache inside an ignored folder stays with that folder.
"""

CACHE = "__pycache__"
type Paths = tuple[str, ...]


def candidates(listed: Paths) -> Paths:
    """Each folder named `__pycache__` in git's list of what it ignores (`ls-files --ignored
    --directory`), which names a folder with its final slash: a file or a link of that name is
    none."""
    return tuple(sorted(entry for entry in listed if cached(entry)))


def cached(entry: str) -> bool:
    """Whether git's entry names a folder `__pycache__`."""
    if not entry.endswith("/"):
        return False
    bare = entry.rstrip("/")
    return bare.rpartition("/")[-1] == CACHE


def folders_above(found: Paths) -> Paths:
    """Each proper folder above a candidate (`build` for `build/__pycache__/`), the paths whose
    ignore rules the choice asks git for."""
    above: set[str] = set()
    for candidate in found:
        parts = candidate.removesuffix("/").split("/")[:-1]
        depths = range(1, len(parts) + 1)
        above.update("/".join(parts[:depth]) for depth in depths)
    return tuple(sorted(above))


def stale(listed: Paths, ignored: frozenset[str]) -> Paths:
    """The `__pycache__` folders to remove, from git's two lists: what it ignores in the
    worktree, and the folders above a candidate that a rule ignores. A `__pycache__` inside an
    ignored folder is part of that folder and stays, also when git lists it on its own because
    that folder holds a tracked file."""
    return tuple(
        candidate for candidate in candidates(listed) if not inside(candidate, ignored)
    )


def inside(candidate: str, ignored: frozenset[str]) -> bool:
    """Whether a folder above `candidate` is one that a rule ignores."""
    return bool(set(folders_above((candidate,))) & ignored)
