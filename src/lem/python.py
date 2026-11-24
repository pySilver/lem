"""The Python that runs Lem's scripts: 3.11 or newer, found by itself when the first
`python3` is older.

Lem's scripts need Python 3.11 (they read the settings with `tomllib`), and a Mac whose
developer does not work in Python has only the system's `python3`, 3.9. So whatever
starts a script of Lem asks `find()` for a newer one when the `python3` it runs under is
older, and starts the script with that: the plugin's hooks, which `hooks/hooks.json`
starts as

    python3 src/lem/python.py NAME ARGS...

with NAME the hook's module of this package, and only when this file and a `python3` are
there: in a plugin folder without it (an update in progress), python3 would exit 2,
which Claude Code reads as a blocking error (a compaction blocked). Under a Python of
3.11 or newer the hook's module runs in this process, so a hook costs no second start of
Python; under an older one this process becomes this file under the newer Python, which
runs it. Either way the module runs as Python runs a script (`run()`), and this file
loads nothing more on the way to it: the search for a Python imports its tools inside
its functions. When the machine has none, the hook does nothing and prints nothing,
since Claude Code takes a hook's output as context and a hook that fails must not fail
the session: `lem doctor`'s row `python3` says so, with the fix. The command `lem` runs
on the Python of its own install, and needs none of this.
"""

# This file loads under an old python3 too (the system's 3.9 on a Mac), since it is what
# finds the newer one: so an annotation that 3.9 cannot evaluate is a string, and it
# imports nothing of Lem's. A hook runs it by its path, before the package is on
# sys.path, so it finds the package from its own place.

import os
import sys

FLOOR: "tuple[int, int]" = (3, 11)
# Where Homebrew links its newest Python, on Apple silicon and on Intel: looked at after
# PATH, for a PATH (a hook's, a keymap's) that leaves Homebrew's folder out.
FALLBACKS = ("/opt/homebrew/bin/python3", "/usr/local/bin/python3")
FIX = "`brew install python`, or `uv python install` where uv is the tool"
# uv, for a developer whose Pythons are uv's own, which stand on no PATH: asked last,
# and only for a Python that is already there (`--no-python-downloads`), since a command
# of Lem downloads nothing by itself. `--no-project`, so that the folder's own
# `.python-version` does not narrow the answer. After PATH, where uv's installer and
# Homebrew put it.
UV_FALLBACKS = (
    os.path.expanduser("~/.local/bin/uv"),
    "/opt/homebrew/bin/uv",
    "/usr/local/bin/uv",
)
UV_ASKS = (
    "python",
    "find",
    "--no-project",
    "--no-python-downloads",
    f">={FLOOR[0]}.{FLOOR[1]}",
)
# `python3.N`, the name every installer (python.org, Homebrew, uv, mise) gives each
# minor version. No list of N: the folders of PATH are read for every such name, so a
# version newer than this file is found too.
NAMED = r"python3\.(\d+)"


def runnable(path: str) -> bool:
    return os.path.isfile(path) and os.access(path, os.X_OK)


def version(path: str) -> "tuple[int, int] | None":
    """The (major, minor) of the Python at PATH: from its name when the name has it,
    else asked of it."""
    import re
    import subprocess

    named = re.fullmatch(NAMED, os.path.basename(path))
    if named:
        return 3, int(named.group(1))
    try:
        ran = subprocess.run(
            [path, "-I", "-c", "import sys; print(*sys.version_info[:2])"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    parts = ran.stdout.split()
    if (
        ran.returncode != 0
        or len(parts) != 2  # noqa: PLR2004 - a major and a minor number
        or not all(part.isdigit() for part in parts)
    ):
        return None
    return int(parts[0]), int(parts[1])


def from_uv(folders: "list[str]", fallbacks: "tuple[str, ...]") -> "str | None":
    """The Python of FLOOR or newer that uv knows, or None: uv from FOLDERS, else the
    first of FALLBACKS."""
    import subprocess

    uv = next(
        (
            path
            for path in [os.path.join(folder, "uv") for folder in folders]
            + list(fallbacks)
            if runnable(path)
        ),
        None,
    )
    if uv is None:
        return None
    try:
        ran = subprocess.run(
            [uv, *UV_ASKS],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    path = ran.stdout.strip()
    return (
        path
        if ran.returncode == 0 and runnable(path) and (version(path) or (0, 0)) >= FLOOR
        else None
    )


def find(
    search: "str | None" = None,
    *,
    python3: bool = True,
    fallbacks: "tuple[str, ...]" = FALLBACKS,
    uv: "tuple[str, ...]" = UV_FALLBACKS,
) -> "str | None":
    """The path of a Python of FLOOR or newer, or None. In this order: `python3` on the
    search path (PATH when SEARCH is None) when it is new enough, which a caller that
    runs under that python3 skips with python3=False; the newest `python3.N` of FLOOR or
    newer on the search path, the first of its name in the path's order; the first of
    FALLBACKS that is new enough; the one uv knows (`from_uv`), with uv from the search
    path or from UV."""
    import re

    folders = [
        folder
        for folder in (os.environ.get("PATH", "") if search is None else search).split(
            os.pathsep
        )
        if folder
    ]
    if python3:
        first = next(
            (
                os.path.join(folder, "python3")
                for folder in folders
                if runnable(os.path.join(folder, "python3"))
            ),
            None,
        )
        if first is not None and (version(first) or (0, 0)) >= FLOOR:
            return first
    best = None
    for folder in folders:
        try:
            names = sorted(os.listdir(folder))
        except OSError:
            continue
        for name in names:
            named = re.fullmatch(NAMED, name)
            if (
                not named
                or (3, int(named.group(1))) < FLOOR
                or (best is not None and int(named.group(1)) <= best[0])
            ):
                continue
            if runnable(os.path.join(folder, name)):
                best = (int(named.group(1)), os.path.join(folder, name))
    if best is not None:
        return best[1]
    brewed = next(
        (
            path
            for path in fallbacks
            if runnable(path) and (version(path) or (0, 0)) >= FLOOR
        ),
        None,
    )
    return brewed or from_uv(folders, uv)


def hook(argv: "list[str]") -> None:
    """Start the module ARGV[0] of this package with the rest of ARGV, as a hook: see
    the module's text."""
    if not argv:
        return
    name, args = argv[0], argv[1:]
    here = os.path.dirname(os.path.abspath(__file__))
    if sys.version_info >= FLOOR:
        run(os.path.join(here, name + ".py"), args)
        return
    python = find(python3=False)
    if python is not None:
        os.execv(python, [python, "-B", os.path.join(here, "python.py"), name, *args])


def run(path: str, args: "list[str]") -> None:
    """Run the module of this package at PATH with ARGS as Python runs a script: as
    `__main__`, with its own `if __name__ == "__main__":` lines, and `sys.argv` holds
    PATH and ARGS. The package's folder takes this file's place first on sys.path, so
    that `lem` is the package. No `runpy`: its imports would be a cost of every hook.

    In a plugin folder that is not whole, the module ends as on a machine with no
    Python, with nothing printed: when its file is gone or cannot be compiled, and when
    a module of the package that it imports is gone, cannot be read or cannot be
    compiled. Whatever else the module raises, its own `sys.exit` too, is its own."""
    sys.dont_write_bytecode = True
    sys.argv = [path, *args]
    package = os.path.dirname(path)
    sys.path[0] = os.path.dirname(package)
    try:
        with open(path, "rb") as file:
            code = compile(file.read(), path, "exec")
    except (OSError, SyntaxError, ValueError):
        return
    main = type(sys)("__main__")
    main.__file__ = path
    sys.modules["__main__"] = main
    try:
        exec(code, vars(main))  # noqa: S102 - the plugin's own module, run as a script
    except ImportError as error:
        if (error.name or "").split(".")[0] != os.path.basename(package):
            raise
    except SyntaxError as error:
        if os.path.dirname(os.path.abspath(error.filename or "")) != package:
            raise
    except OSError as error:
        # a file of the package that cannot be read (mode 0) is as one that is gone
        if os.path.dirname(os.path.abspath(str(error.filename or ""))) != package:
            raise


if __name__ == "__main__":
    hook(sys.argv[1:])
