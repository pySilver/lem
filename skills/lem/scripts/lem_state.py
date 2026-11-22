"""Where Lem keeps one repository's state: `.lem/state/` of its main checkout.

Every script that reads or writes Lem's state asks `folder()` for its place, and nothing else
names it. The state is the tasks, the event log, the board's files, the watch's last look at the
forge, the landing lock, and the correction queue with its log and claims.

The main checkout is the first worktree git lists, where the settings are read from too. A task's
builder runs in a worktree of its own and still writes its state there: a worktree's removal does
not take it, and a session that replaces another finds it. Git never tracks it: the folder holds a
`.gitignore` of `*`, which hides the folder and itself, as the worktrees folder does, with no change
to a file git tracks. It is not in the git directory, because Codex's sandbox keeps `.git` read-only.

Three facts are the machine's and not a repository's, and their place is `config()`, a folder in the
home directory, the one Lem keeps there: whether the owner is there or away (`owner_mark()`,
`owner.jsonl`), this machine's own settings (`machine_file()`, `machine.toml`: `[load]`, the load
average under which the checks of a landing start, which the developer sets with `lem project load
--start N`, and `[serve]`, how the board server runs, which `lem serve --tailscale`, `--tailscale-off`,
`--port` and `--tailscale-port` write, `[peers]`, the other machines whose boards it shows beside
this one's, which `lem serve --join` and `--leave` write, `[seats]`, the developer's own seats of
the merge agent and of a task's session for every repository whose settings name none, `merger` and
`session`, each `"agent/model:effort"`, which he writes by hand, and `[handoff]`, the number of tokens
past which a task's session compacts itself, which `lem project handoff --tokens N` writes), and the
repositories whose boards `lem serve` shows
(`workspaces_file()`, `workspaces.json`, which `lem project task-dir`, `lem session open`, `lem board`
and `lem serve --add` write). A read never
makes that folder: only a write of one of the three does, and beside them it holds `load.lock`, which
spaces the starts of the checks that waited for the load, and the board server's `serve.lock` and
`serve.log`.
"""

import contextlib
import fcntl
import os
import subprocess
import tomllib
from pathlib import Path

STATE = Path(".lem") / "state"
# what the folder's own ignore file says: everything in it, and the file itself
IGNORE = "*\n"
# The event log of the state folder, and the lock beside it: each append takes it for its write, and
# `lem project prune` from its read of the log through the replace of the log by its new file, so that
# no append lands in the old file after prune read it (`events_lock`).
EVENTS = "events.jsonl"
EVENTS_LOCK = "events.lock"


class StateError(Exception):
    pass


@contextlib.contextmanager
def events_lock(state: Path):
    """Hold the lock of the event log in the state folder STATE, waiting for another holder."""
    with (state / EVENTS_LOCK).open("a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield


def jsonl_lines(text: str) -> list[str]:
    """The lines of a JSON-lines text, split at "\\n" alone. Every reader of such a file splits with
    this: str.splitlines also breaks at U+2028, U+2029 and U+0085, which json.dumps(ensure_ascii=False)
    and Claude Code's transcripts keep as they are inside a string, and a record cut there is no JSON."""
    return text.split("\n")


def git(start: Path, args: list, timeout: float | None) -> str | None:
    try:
        ran = subprocess.run(["git", "-C", str(start), *args], capture_output=True, text=True, check=False, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return ran.stdout if ran.returncode == 0 else None


# The main checkout of each folder this process found one for. It cannot change while one command
# runs, and a command that calls its siblings in its own process asks for it many times, so git is
# asked once for each folder. Only the path is kept: the list of worktrees, which a command may
# change, is asked again each time. A process that runs many commands calls `forget()` between two.
CHECKOUTS = {}


def forget() -> None:
    CHECKOUTS.clear()


def main_checkout(start: Path, timeout: float | None = None) -> Path:
    """The checkout every worktree hangs off: the first entry `git worktree list` gives."""
    key = os.path.abspath(start)
    if key in CHECKOUTS:
        return CHECKOUTS[key]
    # -z ends each field with a NUL: a path may hold a line break, and a split on lines would cut it
    listed = git(start, ["worktree", "list", "--porcelain", "-z"], timeout)
    first = next((field[len("worktree "):] for field in (listed or "").split("\0") if field.startswith("worktree ")), None)
    if not first:
        raise StateError(f"git lists no worktree for {start}: Lem's state belongs to a repository, so run this inside its checkout")
    CHECKOUTS[key] = Path(first)
    return CHECKOUTS[key]


def config() -> Path:
    """Lem's folder in the home directory: `$XDG_CONFIG_HOME/lem` when that variable is set and not
    empty, else `~/.config/lem`. Nothing here makes it."""
    named = os.environ.get("XDG_CONFIG_HOME", "")
    if not named:
        return Path.home() / ".config" / "lem"
    if not os.path.isabs(named):
        # a relative path would be read from the folder each command starts in, so two repositories would read two marks
        raise StateError(f"XDG_CONFIG_HOME is {named!r}, a relative path: Lem keeps the owner's status under it for every repository, so set it to an absolute path, or unset it for ~/.config")
    return Path(named) / "lem"


# The owner's status, the machine's: one line for each away and back he said, appended (`project.py owner`).
OWNER_MARK = "owner.jsonl"


def owner_mark() -> Path:
    """The file of the owner's status, which every repository on this machine reads; it may not exist."""
    return config() / OWNER_MARK


# The settings of this machine, one file for every repository on it: `[load] start`, the load average
# under which the checks of a landing start (`land.py`, LOAD_START without it), and `[serve]`, how the board server runs
# (`serve.py`). Each writer writes the file whole and keeps the other's table.
MACHINE = "machine.toml"
# The lock that spaces two starts of the checks that waited for the load, in the same folder.
LOAD_LOCK = "load.lock"
# The output of the board server that starts on demand (`serve.py`), in the same folder.
SERVE_LOG = "serve.log"
# The board server's pid and its main port, one line `PID PORT`, which it writes at its start and removes
# at a clean stop (`serve.py` `listen`); `bin/lem` reads it by this name, with no import of this file.
SERVE_PID = "serve.pid"
# The keys of each table of the file, with the type each holds; what `write_machine` writes. The keys of
# `[peers]` are not fixed: each is a machine's name on the tailnet (PEER_NAME), and its value the port
# of that machine's tailnet door.
MACHINE_KEYS = {"load": {"start": (int, float)}, "serve": {"tailscale": bool, "port": int, "tailscale_port": int}, "peers": None, "seats": {"merger": str, "session": str},
                "handoff": {"tokens": int}}
# The lines that write each table, for a refusal of the file.
MACHINE_FIX = {"load": "`lem project load --start N` writes it", "serve": "`lem serve --port N` or `lem serve --tailscale` writes it",
               "peers": "`lem serve --join HOST` and `--leave HOST` write it",
               "seats": 'the developer writes it by hand, as merger = "agent/model:effort" and session = "agent/model:effort"',
               "handoff": "`lem project handoff --tokens N` writes it, and `--tokens default` takes it out"}
# A machine's name on the tailnet, as a key of `[peers]`: one DNS label, in lower case.
PEER_NAME = r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"


def machine_file() -> Path:
    """The file of this machine's own settings, which every repository on it reads; it may not exist."""
    return config() / MACHINE


def machine_tables() -> dict:
    """The tables of the machine's file, as it reads; none when there is no file. A file that does not
    read as TOML is refused with the lines that write it again."""
    file = machine_file()
    fix = f"{MACHINE_FIX['load']} again, with only its own table, and {MACHINE_FIX['serve']} and {MACHINE_FIX['peers']} again, the same way"
    try:
        text = file.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    except OSError as error:
        raise StateError(f"{file} cannot be read ({error.strerror}); {fix}") from error
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise StateError(f"{file} does not read as TOML ({error}); {fix}") from error


def machine_table(name: str) -> dict:
    """One table of the machine's file, its keys checked; none when the file or the table is absent."""
    table = machine_tables().get(name, {})
    file, fix = machine_file(), MACHINE_FIX[name]
    if not isinstance(table, dict):
        raise StateError(f"{name} in {file} is no table; {fix}")
    for key, value in table.items():
        if MACHINE_KEYS[name] is None:
            import re
            if not re.fullmatch(PEER_NAME, key) or isinstance(value, bool) or not isinstance(value, int) or not 0 < value < 65536:
                raise StateError(f"{name}.{key} in {file} is no machine's name with a port of its door; delete the line, or {fix}")
            continue
        kind = MACHINE_KEYS[name].get(key)
        if kind is None:
            raise StateError(f"{name}.{key} in {file} is no setting of Lem's (the keys of [{name}] are {', '.join(MACHINE_KEYS[name])}); delete the line, or {fix}")
        if (isinstance(value, bool) and kind is not bool) or not isinstance(value, kind):
            raise StateError(f"{name}.{key} in {file} is {value!r}, of the wrong type; {fix}")
    return table


def write_machine(name: str, values: dict | None) -> None:
    """Write table `name` of the machine's file as `values`, or take it out with None, and keep every
    other table as it reads. The file is written whole: a temporary file beside it, then a rename over
    it. A file that does not read is written again with this table only. With no table left, the file
    goes. Two writers at the same moment may lose one change, which its command writes again."""
    import tempfile
    try:
        tables = {key: value for key, value in machine_tables().items() if key in MACHINE_KEYS and key != name}
    except StateError:
        tables = {}
    if values is not None:
        tables[name] = values
    file = machine_file()
    if not tables:
        file.unlink(missing_ok=True)
        return
    lines = ["# this machine's own settings, for every repository on it"]
    for table in MACHINE_KEYS:
        if table not in tables or not isinstance(tables[table], dict):
            continue
        lines += ["", f"[{table}]", f"# {MACHINE_FIX[table]}"]
        for key, value in tables[table].items():
            if (key in MACHINE_KEYS[table] if MACHINE_KEYS[table] is not None else isinstance(key, str)) and isinstance(value, (bool, int, float, str)):
                if isinstance(value, str):
                    # a seat the developer wrote by hand, kept as he wrote it
                    import json
                    shown = json.dumps(value)
                else:
                    shown = ("true" if value else "false") if isinstance(value, bool) else (str(int(value)) if isinstance(value, float) and value.is_integer() else str(value))
                lines.append(f"{key} = {shown}")
    file.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=file.parent, prefix=f".{file.name}.", suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as out:
            out.write("\n".join(lines) + "\n")
        os.chmod(temporary, 0o644)
        os.replace(temporary, file)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


# The repositories whose boards `lem serve` shows: a JSON list of their main checkouts' absolute paths,
# in the order they came in. One file for the machine.
WORKSPACES = "workspaces.json"


def workspaces_file() -> Path:
    """The list of the repositories `lem serve` shows; it may not exist."""
    return config() / WORKSPACES


def workspaces() -> list[str]:
    """The main checkouts in the list, as written, in its order; none when there is no file. A path
    whose folder is gone stays in the list: the server leaves it out, and only `lem serve --remove`
    takes it out."""
    file = workspaces_file()
    fix = f"`lem serve --remove DIR` and `--add DIR` write it again, or delete {file} and run `lem board` in each repository"
    try:
        text = file.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []
    except OSError as error:
        raise StateError(f"{file} cannot be read ({error.strerror}); {fix}") from error
    import json
    try:
        listed = json.loads(text)
    except ValueError as error:
        raise StateError(f"{file} does not read as JSON ({error}); {fix}") from error
    if not isinstance(listed, list) or not all(isinstance(path, str) and os.path.isabs(path) for path in listed):
        raise StateError(f"{file} is not a list of absolute paths; {fix}")
    return listed


def write_workspaces(paths: list[str]) -> None:
    """Write the list whole: a temporary file beside it, then a rename over it, so that a server that
    reads it while it is written reads the old list or the new one. Two writers at the same moment
    may lose one entry, which the next `lem board` of that repository writes again."""
    import json
    import tempfile
    file = workspaces_file()
    file.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=file.parent, prefix=f".{file.name}.", suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as out:
            out.write(json.dumps(paths, indent=2) + "\n")
        os.chmod(temporary, 0o644)
        os.replace(temporary, file)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def register(checkout: Path) -> bool:
    """Put a main checkout into the list; False when it was there already, and then nothing is written."""
    path = os.path.realpath(checkout)
    listed = workspaces()
    if path in listed:
        return False
    write_workspaces([*listed, path])
    return True


def unregister(checkout: Path) -> bool:
    """Take a main checkout out of the list; False when it was not there, and then nothing is written."""
    listed = workspaces()
    path = os.path.realpath(checkout)
    # a path as written, or as it resolves now: a folder that is gone resolves to itself
    kept = [entry for entry in listed if entry not in (path, os.path.abspath(checkout))]
    if len(kept) == len(listed):
        return False
    write_workspaces(kept)
    return True


# The number of tokens past which a task's session compacts itself with the handoff's form, the owner's
# for all his repositories (`[handoff] tokens`): "lets keep the limit at 600K for now (default
# settings)" (2026-11-21, on the shape of task 4). 0 turns Lem's number off, and Claude Code then
# compacts at its own trigger. Under the floor is refused, as Claude Code refuses a window under
# 100,000 (`research-compaction.md`, read 2026-11-21).
HANDOFF_TOKENS = 600_000
HANDOFF_FLOOR = 100_000


def handoff_tokens():
    """The number Lem gives each session it opens as `CLAUDE_CODE_AUTO_COMPACT_WINDOW`: the machine's
    `[handoff] tokens`, else HANDOFF_TOKENS; None for 0, when Lem sets nothing. A negative number, one
    under HANDOFF_FLOOR, a bool and a float are refused with the line that writes a good one."""
    table = machine_table("handoff")
    if "tokens" not in table:
        return HANDOFF_TOKENS
    value = table["tokens"]
    if value == 0:
        return None
    if value < HANDOFF_FLOOR:
        raise StateError(f"handoff.tokens in {machine_file()} is {value!r}, and it is 0 (Claude Code's own trigger) or {HANDOFF_FLOOR} or more, "
                         f"since Claude Code refuses a window under {HANDOFF_FLOOR}; {MACHINE_FIX['handoff']}")
    return value


# The load average under which the checks of a landing start on a machine with no `[load] start` of its
# own, the owner's for every new user: "also `lem` default should be set to 40, so new users will get it
# that way" (2026-11-22, after the retro, where he set his own Mac's number to 40). `start = 0`, which
# `lem project load --start none` writes, is a machine with no gate.
LOAD_START = 40


def load_start():
    """The load average under which the checks of a landing start on this machine: the developer's
    `[load] start`, else LOAD_START; None for 0, when he took the gate away. A file that does not read,
    or a negative number, is refused with the line that writes a good one."""
    table = machine_table("load")
    if "start" not in table:
        return float(LOAD_START)
    value = table["start"]
    if value == 0:
        return None
    if value < 0:
        raise StateError(f"load.start in {machine_file()} is {value!r}, and it is a load average above 0, or 0 for no gate; {MACHINE_FIX['load']}")
    return float(value)


def folder(start: Path, timeout: float | None = None) -> Path:
    """The state folder of the repository `start` is in, made when it is absent."""
    new = main_checkout(start, timeout) / STATE
    new.mkdir(parents=True, exist_ok=True)
    ignore = new / ".gitignore"
    if not ignore.is_file():
        ignore.write_text(IGNORE, encoding="utf-8")
    return new
