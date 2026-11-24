"""Lem's one command and the package's one entry.

`cli()` is the command `lem` (pyproject.toml, `[project.scripts]`): `lem NAME ARGS...`
runs the module of this package that NAME stands for (`names`), with ARGS as they came;
its stdin, stdout, stderr and exit status are the module's own.

    lem                  the names, one line each (also `lem help`, `lem --help`)
    lem version          Lem's version, the folder of its files and its commit, as JSON
    lem NAME ARGS...     the module NAME stands for; `lem NAME --help` is its own help

One command, so that one permission rule (`Bash(lem *)`) holds on every machine and
after every update.

Before a name, `lem NAME` takes a cheap look whether the board server of this machine
runs: it reads the server's pid from `serve.pid` in Lem's home folder, which the
server writes at its start and removes at a clean stop, and asks the kernel whether
that process lives (signal 0), with no import of Lem's other modules, no connect and no
process started. Only when the file is not there, or its process is gone, does it start
`lem serve --ensure` as a process of its own, with its output in the server's log, and
it goes on without a wait. `serve` itself, `board` and `doctor`, which look at the
server their own way, and `ask` and `jev` take no look (`NO_LOOK`), and
`LEM_SERVE=off` turns it off, which the test suites set.

`python -B src/lem/__main__.py NAME ARGS...` is the same command with no look: every
command of Lem that starts another as a process of its own starts it so, with its own
interpreter (`paths.MAIN`). Run by its path, this file puts the folder of the package
first on `sys.path` in place of its own folder, so that `lem` is the package and no
module of it is found under its bare name.

The module runs as a script ran before it was one of this package: as `__main__`, with
its own `if __name__ == "__main__":` lines, and `sys.argv` holds its file's name and
ARGS. Where the package is a checkout's, no bytecode is written, as with -B.
"""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if not os.path.isdir(os.path.join(HERE, "data")):
    # a checkout's package, which an installed app's data folder never is
    sys.dont_write_bytecode = True
if not __package__:
    # run by its path: sys.path[0] is this folder, which holds the modules by their bare
    # names
    sys.path[0] = os.path.dirname(HERE)

from lem import names  # noqa: E402 - after the line that puts the package on sys.path

# The commands that take no look at the board server: the server's own, the two that
# look at it their own way (`board` starts it and waits for it, and `doctor` only
# reports it), and the question page and the Jev model, which the launcher before the
# package ran as `lem-ask` and `lem-jev` with no look.
NO_LOOK = ("serve", "board", "doctor", "ask", "jev")
# The server's pid file and its log in Lem's home folder (lem.state.SERVE_PID and
# SERVE_LOG), by name: the look imports none of Lem's modules but the table of names,
# since that import was most of its cost (8 to 11 ms a call, medians of the builder of
# 2026-11-21).
PID_FILE = "serve.pid"
SERVE_LOG = "serve.log"


def main(argv: list[str]) -> None:
    """Run the module of the name ARGV[0] with the rest of ARGV, as a script."""
    if not argv or names.module(argv[0]) is None:
        sys.exit(
            f"lem: {argv[0]!r} is no command of Lem's; `lem help` lists the names"
            if argv
            else "lem: name a command of Lem's; `lem help` lists the names"
        )
    name, args = argv[0], argv[1:]
    module = str(names.module(name))
    import runpy

    sys.argv = [names.file_name(module), *args]
    runpy.run_module(f"lem.{module}", run_name="__main__", alter_sys=True)


def home() -> str | None:
    """Lem's home folder as lem.state.config() names it, or None where it refuses (a
    relative XDG_CONFIG_HOME)."""
    named = os.environ.get("XDG_CONFIG_HOME", "")
    if named and not os.path.isabs(named):
        return None
    return os.path.join(
        named or os.path.join(os.path.expanduser("~"), ".config"), "lem"
    )


def server_lives(folder: str) -> bool:
    """Whether the pid in the server's pid file is a process that lives. A file that
    does not read is no server."""
    try:
        with open(os.path.join(folder, PID_FILE), encoding="utf-8") as file:
            pid = int(file.read().split()[0])
    except OSError, ValueError, IndexError:
        return False
    if pid <= 0:
        # 0 and a negative pid name a process group, never one server
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # a process of another user holds the pid: it lives, and it is no server to
        # start here
        return True
    return True


def look_for_server() -> None:
    """Start the board server detached when its pid file names no process that lives.
    Every failure is silent: the look serves the board, and no command of Lem's waits
    for it or fails by it."""
    if os.environ.get("LEM_SERVE") == "off":
        return
    folder = home()
    if folder is None or server_lives(folder):
        return
    try:
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, SERVE_LOG), "ab") as log:
            subprocess.Popen(
                [
                    sys.executable,
                    "-B",
                    os.path.join(HERE, "__main__.py"),
                    "serve",
                    "--ensure",
                ],
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=log,
                start_new_session=True,
                close_fds=True,
                cwd=folder,
            )
    except Exception:  # noqa: BLE001 - the command goes on without the board
        return


def listing() -> str:
    """The text of `lem help`: every name with what it does, in one line each."""
    commands = names.COMMANDS
    width = max(len(name) for name in commands)
    lines = [
        (
            "lem NAME ARGS... runs one of Lem's scripts; "
            "`lem NAME --help` gives its own help."
        ),
        "",
    ]
    lines += [f"  {name:<{width}}  {about}" for name, (_, about) in commands.items()]
    lines += [
        (
            f"  {'version':<{width}}  Lem's version, the folder of its files "
            "and its commit, as JSON"
        ),
        f"  {'help':<{width}}  this list",
    ]
    return "\n".join(lines) + "\n"


def version() -> dict[str, object]:
    """`root`, the folder of Lem's files (`paths.ROOT`); `version`, from its manifest;
    `commit`, from the file `build-commit` of the package when the build wrote one, else
    git's HEAD when `root` is a checkout, else None."""
    from lem import paths

    found: dict[str, object] = {
        "root": str(paths.ROOT),
        "version": None,
        "commit": None,
    }
    try:
        with open(
            paths.ROOT / ".claude-plugin" / "plugin.json", encoding="utf-8"
        ) as manifest:
            found["version"] = json.load(manifest).get("version")
    except OSError, ValueError:
        pass
    try:
        with open(paths.PACKAGE / "build-commit", encoding="utf-8") as stamp:
            found["commit"] = stamp.read().strip() or None
    except OSError:
        if (paths.ROOT / ".git").exists():
            ran = subprocess.run(
                ["git", "-C", str(paths.ROOT), "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
                check=False,
            )
            if ran.returncode == 0:
                found["commit"] = ran.stdout.strip()
    return found


def cli() -> None:
    """The command `lem`: see the module's text."""
    args = sys.argv[1:]
    if not args or args[0] in ("help", "--help", "-h"):
        sys.stdout.write(listing())
        return
    name = args[0]
    if name == "version":
        print(json.dumps(version(), indent=2))
        return
    if name not in names.COMMANDS:
        sys.stderr.write(
            f"lem: {name!r} is no command of Lem's; the names are:\n\n" + listing()
        )
        sys.exit(1)
    if name not in NO_LOOK:
        look_for_server()
    main(args)


if __name__ == "__main__":
    main(sys.argv[1:])
