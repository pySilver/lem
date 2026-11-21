"""One command of a sibling script, run in this process: the one way `land.py`, `criteria.py`,
and `decisions.py` call `project.py`, `criteria.py` and `decisions.py`.

A command of a sibling used to be a new `python3`, which compiled the script again, imported the
standard library again and asked git again where the checkout is: in the suite at cfc4831 that
was 12,147 of its 16,770 Python starts, and a landing step made 4 to 21 of them (counted by a
wrapper on each start, 2026-11-18). Here the sibling is imported once, kept in `sys.modules`,
and its `main(argv)` runs with stdout and stderr caught.
The result is what the process gave: the exit code as Python's own exit sets it, stdout and
stderr as text, and a traceback on stderr with exit 1 for an error that the script did not turn
into a message.

What makes this safe is the siblings' form, kept so: each `main(argv)` parses `argv`, not
`sys.argv`; each prints through `sys.stdout` and `sys.stderr` as they are at the time of the call,
and catches the output of every child it starts; each signal handler is put back in a `finally`;
and what a module keeps between two calls is only what cannot change while one command runs
(`lem_state`'s main checkout of a folder, `project.py`'s state folder for a root, and its "said
once" of the settings' copy). A command that needs a process of its own stays one: `APART`, and
so does a file in the sibling's place with no `def main(argv` of its own (a stand-in a test puts
there, which reads `sys.argv` as a process does).
"""

import contextlib
import importlib.util
import io
import re
import subprocess
import sys
import traceback
from pathlib import Path

# The commands that stay a process of their own, and why.
APART = {
    # It runs the tests of the criteria in two worktrees, each command in a process group of its
    # own, under a lock and a SIGTERM handler that end them; a stop of the landing has to stop it as
    # a process, never turn into a result the landing reads and goes on from. It is also the
    # slowest call by far, so one more start is nothing beside it.
    ("criteria.py", "red"): "runs the criteria's tests under its own SIGTERM handler",
    # It holds the machine's one lock for as long as its command runs, and a kill of its process
    # group has to end the command with it.
    ("project.py", "serial"): "holds the machine's lock for its command",
}


# whether each sibling file has the form a call in this process needs, read once
FORMS: dict[Path, bool] = {}


def in_form(path: Path) -> bool:
    """Whether the file defines `main(argv)` at its top level: only such a script runs in this process."""
    if path not in FORMS:
        try:
            FORMS[path] = re.search(r"^def main\(argv\b", path.read_text(encoding="utf-8"), re.M) is not None
        except (OSError, UnicodeDecodeError):
            FORMS[path] = False
    return FORMS[path]


def module(path: Path):
    """The sibling script as a module, imported once and kept. Every script that imports this file
    sets `sys.dont_write_bytecode` first, so the sibling writes no bytecode, as `-B` did."""
    # one module for each file: a copy of the scripts in another folder is a module of its own
    name = f"_lem_{path.stem}:{path}"
    found = sys.modules.get(name)
    if found is not None:
        return found
    spec = importlib.util.spec_from_file_location(name, path)
    found = importlib.util.module_from_spec(spec)
    sys.modules[name] = found
    try:
        spec.loader.exec_module(found)
    except BaseException:
        # a half-loaded module is never kept: the next call loads it again and fails the same way
        del sys.modules[name]
        raise
    return found


def exit_code(stop: SystemExit, err: io.StringIO) -> int:
    """The exit code a process gives for this `sys.exit`, with the text Python prints for it."""
    code = stop.code
    if code is None:
        return 0
    if isinstance(code, int):
        return code & 0xFF
    err.write(f"{code}\n")
    return 1


def run(path: Path, repo: Path, *args: str) -> subprocess.CompletedProcess:
    """`python3 -B PATH --repo REPO ARGS...`, in this process unless the command is in `APART` or
    the file is not in the form for it."""
    argv = ["--repo", str(repo), *args]
    if (path.name, args[0] if args else "") in APART or not in_form(path):
        return subprocess.run([sys.executable, "-B", str(path), *argv], capture_output=True, text=True, check=False)
    out, err = io.StringIO(), io.StringIO()
    code = 0
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            module(path).main(argv)
        except SystemExit as stop:
            code = exit_code(stop, err)
        except Exception:  # noqa: BLE001 - a crash of the sibling is its exit 1 with the traceback, as a process gave it
            err.write(traceback.format_exc())
            code = 1
    return subprocess.CompletedProcess([sys.executable, "-B", str(path), *argv], code, out.getvalue(), err.getvalue())
