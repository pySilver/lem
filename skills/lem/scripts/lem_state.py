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
this one's, which `lem serve --join` and `--leave` write, `[handoff]`, the number of tokens past
which a task's session compacts itself, which `lem project handoff --tokens N` writes, and
`[corrections]`, the developer's yes or no to the correction queue, `collect`), and the
repositories whose boards `lem serve` shows
(`workspaces_file()`, `workspaces.json`, which `lem project task-dir`, `lem session open`, `lem board`
and `lem serve --add` write). Nothing overrides what `machine.toml` says. A read never
makes that folder: a write does, of one of the three, of the load gate or of the board server's start.
Beside them it holds `load.lock`, which spaces the starts of the checks that waited for the load,
`load.line/`, the machine's one line of the runs of the checks that wait, one locked file for each,
`machine.lock`, which one writer of `machine.toml` holds from its read to its rename (`write_machine`),
and the board server's `serve.lock` and `serve.log`.

The developer's own settings for every repository on the machine are the folder's `settings.toml`
(`home_settings_file()`), which `project.py` reads with a repository's two, `.lem/settings.toml`,
the team's, in git, and `.lem/settings.local.toml`, the developer's own for that one repository:
the nearest file that holds a setting wins. Each table of the four files is valid in some of them
only (`TABLE_PLACES`, the one map), and a table in another file is refused with the file where it
is valid (`misplaced`).
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
# under which the checks of a landing start (`land.py`, LOAD_START without it), `[serve]`, how the board
# server runs (`serve.py`), and the rest of MACHINE_KEYS. Each writer goes through `write_machine`, which
# keeps the other tables.
MACHINE = "machine.toml"
# The lock one writer of the machine's file holds from its read of the file to its rename of the new one,
# in the same folder: two writers in two panes would each write the file whole, and the later one would
# lose the other's table (the plan talk of one-home-folder-for-lem, 2026-11-23, question 1).
MACHINE_LOCK = "machine.lock"
# The lock that spaces two starts of the checks that waited for the load, in the same folder.
LOAD_LOCK = "load.lock"
# The machine's one line of the runs of the checks that wait for the load, a folder beside it: one
# file for each run that waits, which that run holds locked while it waits (`land.py` `wait_for_load`).
LOAD_LINE = "load.line"
# The output of the board server that starts on demand (`serve.py`), in the same folder.
SERVE_LOG = "serve.log"
# The board server's pid and its main port, one line `PID PORT`, which it writes at its start and removes
# at a clean stop (`serve.py` `listen`); `bin/lem` reads it by this name, with no import of this file.
SERVE_PID = "serve.pid"
# The keys of each table of the file, with the type each holds; what `write_machine` writes. The keys of
# `[peers]` are not fixed: each is a machine's name on the tailnet (PEER_NAME), and its value the port
# of that machine's tailnet door.
MACHINE_KEYS = {"load": {"start": (int, float)}, "serve": {"tailscale": bool, "port": int, "tailscale_port": int}, "peers": None,
                "handoff": {"tokens": int}, "corrections": {"collect": bool}}
# The lines that write each table, for a refusal of the file.
MACHINE_FIX = {"load": "`lem project load --start N` writes it", "serve": "`lem serve --port N` or `lem serve --tailscale` writes it",
               "peers": "`lem serve --join HOST` and `--leave HOST` write it",
               "handoff": "`lem project handoff --tokens N` writes it, and `--tokens default` takes it out",
               "corrections": "the developer writes it, as collect = false or collect = true"}
# A machine's name on the tailnet, as a key of `[peers]`: one DNS label, in lower case.
PEER_NAME = r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
# The developer's own settings for every repository on this machine, in the same folder, and a
# repository's two, at the root of its checkout: the team's, in git, and the developer's own for that
# one repository, which git does not track. The nearest file that holds a setting wins (`project.py`).
HOME_SETTINGS = "settings.toml"
TEAM_SETTINGS = Path(".lem") / "settings.toml"
LOCAL_SETTINGS = Path(".lem") / "settings.local.toml"
# The files where each table of Lem's settings is valid: `machine` (MACHINE), `home` (HOME_SETTINGS),
# `team` (TEAM_SETTINGS) and `local` (LOCAL_SETTINGS). What is true for the whole machine is in its file
# alone, and nothing overrides it; what guards a team's repository is in the team's file alone; the
# question page's defaults are the developer's (the plan of one-home-folder-for-lem, 2026-11-23,
# "How it works", decisions 2 and 3). Which keys of a table one file may hold is `project.py`'s
# (`HOME_KEYS`, `local_naps_off`).
TABLE_PLACES = {
    "load": ("machine",), "serve": ("machine",), "peers": ("machine",), "handoff": ("machine",), "corrections": ("machine",),
    "seats": ("home", "team", "local"),
    "ask": ("home",),
    "flow": ("team",), "checks": ("team",), "branch": ("team",), "paths": ("team",), "tracker": ("team",),
    "naps": ("team", "local"),
    "state": ("team", "local"),
}
PLACE_ORDER = ("home", "team", "local", "machine")


def machine_file() -> Path:
    """The file of this machine's own settings, which every repository on it reads; it may not exist."""
    return config() / MACHINE


def home_settings_file() -> Path:
    """The developer's own settings file for every repository on this machine; it may not exist."""
    return config() / HOME_SETTINGS


def shown(path: Path) -> str:
    """A file of the home directory as a person writes it, `~/.config/lem/settings.toml`; any other
    path as it is."""
    try:
        return "~/" + path.relative_to(Path.home()).as_posix()
    except ValueError:
        return str(path)


def place_name(place: str) -> str:
    """The name of one file of TABLE_PLACES, as a refusal gives it."""
    if place == "machine":
        return shown(machine_file())
    if place == "home":
        return shown(home_settings_file())
    return (TEAM_SETTINGS if place == "team" else LOCAL_SETTINGS).as_posix()


def misplaced(table: str, place: str) -> str | None:
    """Why the file of PLACE may not hold the table, with the file where it is valid; None when it may,
    or when Lem knows no such table (the reader names the tables it knows)."""
    valid = TABLE_PLACES.get(table)
    if valid is None or place in valid:
        return None
    where = [place_name(one) for one in PLACE_ORDER if one in valid]
    named = where[0] if len(where) == 1 else ", ".join(where[:-1]) + f" or {where[-1]}"
    return f"[{table}] is not valid in this file: its place is {named}; move the table there"


@contextlib.contextmanager
def machine_lock():
    """Hold the lock of the machine's file, waiting for another writer; the folder is made for it."""
    folder = config()
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / MACHINE_LOCK).open("a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield


def machine_tables() -> dict:
    """The tables of the machine's file, as it reads; none when there is no file. A file that does not
    read as TOML, or that holds a table Lem does not know or one whose place is another file, is
    refused with the file and the fix."""
    file = machine_file()
    fix = f"correct {file} by hand: the tables it may hold are {', '.join(f'[{name}]' for name in MACHINE_KEYS)}"
    try:
        text = file.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    except OSError as error:
        raise StateError(f"{file} cannot be read ({error.strerror}); {fix}") from error
    except UnicodeDecodeError as error:
        raise StateError(f"{file} is not UTF-8 text (byte {error.start} does not read); {fix}") from error
    try:
        tables = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise StateError(f"{file} does not read as TOML ({error}); {fix}") from error
    for name in tables:
        if name not in TABLE_PLACES:
            raise StateError(f"{file}: [{name}] is no table of Lem's; {fix}")
        wrong = misplaced(name, "machine")
        if wrong:
            raise StateError(f"{file}: {wrong}")
    return tables


def checked_table(tables: dict, name: str) -> dict:
    """One table of the machine's file, of the tables it read, its keys checked; none when absent."""
    table = tables.get(name, {})
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


def machine_table(name: str) -> dict:
    """One table of the machine's file, its keys checked; none when the file or the table is absent."""
    return checked_table(machine_tables(), name)


def write_machine(name: str, values: dict | None) -> None:
    """Write table `name` of the machine's file as `values`, or take it out with None, and keep every
    other table as it reads. It writes over nothing it cannot keep: the whole file is read and each of
    its tables checked first, and a file that does not read, or that holds a table or a key that is not
    valid there, is refused with the file and the fix, and stays as it is. The file is written whole: a
    temporary file beside it, then a rename over it, under the lock of MACHINE_LOCK from the read to
    the rename, so that two writers at one moment each keep the other's table. With no table left, the
    file goes."""
    import tempfile
    file = machine_file()
    with machine_lock():
        found = machine_tables()
        tables = {table: dict(checked_table(found, table)) for table in found if table != name}
        if values is not None:
            tables[name] = values
        if not tables:
            file.unlink(missing_ok=True)
            return
        lines = ["# this machine's own settings, for every repository on it; nothing overrides them"]
        for table in MACHINE_KEYS:
            if table not in tables:
                continue
            lines += ["", f"[{table}]", f"# {MACHINE_FIX[table]}"]
            for key, value in tables[table].items():
                shown_value = ("true" if value else "false") if isinstance(value, bool) else (str(int(value)) if isinstance(value, float) and value.is_integer() else str(value))
                lines.append(f"{key} = {shown_value}")
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
