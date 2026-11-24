"""One command of a sibling, run in this process: the one way `land`, `criteria`,
`decisions` and the board server call the commands `project`, `criteria`, `decisions`,
`land` and `session`, by the name `lem` gives each.

A command of a sibling used to be a new `python3`, which compiled the script again,
imported the standard library again and asked git again where the checkout is: in the
suite at cfc4831 that was 12,147 of its 16,770 Python starts, and a landing step made 4
to 21 of them (counted by a wrapper on each start, 2026-11-18). Here the sibling is
imported once, kept in `sys.modules`, and its `main(argv)` runs with stdout and stderr
caught. The result is what the process gave: the exit code as Python's own exit sets it,
stdout and stderr as text, and a traceback on stderr with exit 1 for an error that the
module did not turn into a message.

What makes this safe is the siblings' form, kept so: each `main(argv)` parses `argv`,
not `sys.argv`; each prints through `sys.stdout` and `sys.stderr` as they are at the
time of the call, and catches the output of every child it starts; each signal handler
is put back in a `finally`; and what a module keeps between two calls is only what
cannot change while one command runs (`lem_state`'s main checkout of a folder,
`project.py`'s state folder for a root, and its "said once" of the settings' copy). A
command that needs a process of its own stays one, started through the package's entry
(`paths.MAIN`): `APART`, and so does a module file in the command's place with no
`def main(argv` of its own (a stand-in a test puts in a copy of the package, which reads
`sys.argv` as a process does).

Each of the three takes a result the same way (`checked`): a sibling that failed is
its own refusal, of the error class it names, so that each still raises its own.
"""

import contextlib
import io
import re
import subprocess
import sys
import traceback

from lem import names, paths

# typing's flag, without the import of typing, which a hook's start does not pay
TYPE_CHECKING = False
if TYPE_CHECKING:
    from pathlib import Path
    from types import ModuleType

# The commands that stay a process of their own, and why.
APART = {
    # It runs the tests of the criteria in two worktrees, each command in a process
    # group of its own, under a lock and a SIGTERM handler that end them; a stop of the
    # landing has to stop it as a process, never turn into a result the landing reads
    # and goes on from. It is also the slowest call by far, so one more start is nothing
    # beside it.
    ("criteria", "red"): "runs the criteria's tests under its own SIGTERM handler",
    # It holds the machine's one lock for as long as its command runs, and a kill of its
    # process group has to end the command with it.
    ("project", "serial"): "holds the machine's lock for its command",
}


# whether the module of each command has the form a call in this process needs, read
# once
FORMS: dict[str, bool] = {}


def file_of(name: str) -> Path:
    """The file of the module that the command NAME runs, in this package."""
    return paths.PACKAGE / f"{names.COMMANDS[name][0]}.py"


def in_form(name: str) -> bool:
    """Whether the module of the command NAME defines `main(argv)` at its top level:
    only such a module runs in this process."""
    if name not in FORMS:
        try:
            FORMS[name] = (
                re.search(
                    r"^def main\(argv\b",
                    file_of(name).read_text(encoding="utf-8"),
                    re.MULTILINE,
                )
                is not None
            )
        except OSError, UnicodeDecodeError:
            FORMS[name] = False
    return FORMS[name]


def loaded(name: str) -> ModuleType:
    """The module of the command NAME, imported once and kept in `sys.modules`: one of
    the commands that a sibling runs in this process, each imported here by its name."""
    if name == "project":
        from lem import project as found
    elif name == "criteria":
        from lem import criteria as found
    elif name == "decisions":
        from lem import decisions as found
    elif name == "land":
        from lem import land as found
    elif name == "session":
        from lem import session as found
    else:
        raise ValueError(f"{name} is no command that a sibling runs in this process")
    return found


def exit_code(stop: SystemExit, err: io.StringIO) -> int:
    """The exit code a process gives for this `sys.exit`, with the text Python prints
    for it."""
    code = stop.code
    if code is None:
        return 0
    if isinstance(code, int):
        return code & 0xFF
    err.write(f"{code}\n")
    return 1


def run(name: str, repo: Path, *args: str) -> subprocess.CompletedProcess:
    """`lem NAME --repo REPO ARGS...`, as `python3 -B MAIN NAME ...`: in this process
    unless the command is in `APART` or its module is not in the form for it."""
    argv = ["--repo", str(repo), *args]
    command = [sys.executable, "-B", str(paths.MAIN), name, *argv]
    if (name, args[0] if args else "") in APART or not in_form(name):
        return subprocess.run(command, capture_output=True, text=True, check=False)
    out, err = io.StringIO(), io.StringIO()
    code = 0
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            loaded(name).main(argv)
        except SystemExit as stop:
            code = exit_code(stop, err)
        except Exception:  # noqa: BLE001 - a crash of the sibling is its exit 1 with the traceback, as a process gave it
            err.write(traceback.format_exc())
            code = 1
    return subprocess.CompletedProcess(command, code, out.getvalue(), err.getvalue())


def checked(
    name: str, repo: Path, *args: str, error: type[Exception], check: bool = True
) -> subprocess.CompletedProcess:
    """`run`, as a module that calls its sibling takes it: a failure is that module's
    own refusal ERROR, with the sibling's message less its `NAME.py: ` (with CHECK
    false the caller reads the exit itself), and a line the sibling wrote on stderr
    when it succeeded is the caller's to say too, as project.py's of the settings read
    from the base branch."""
    ran = run(name, repo, *args)
    file = names.file_name(names.COMMANDS[name][0])
    if check and ran.returncode != 0:
        raise error(
            ran.stderr.strip().removeprefix(f"{file}: ") or f"{file} {args[0]} failed"
        )
    if ran.returncode == 0 and ran.stderr:
        sys.stderr.write(ran.stderr)
    return ran
