"""Claude Code as it runs one of Lem's hooks: the line of the installed manifest,
`hooks/hooks.json`, through `hooks/run`, with `LEM_HOOK_BIN` set to this checkout's
`.venv/bin/lem-hook` and the test's own HOME and XDG_CONFIG_HOME (the entry's).

A stand-in app (`stand_in`) runs the same hook with another `sys.executable`, so that the `lem`
the hook starts beside its Python is a script of the test that writes down how it was called:
no hook of a test starts Lem's own `lem`.
"""

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from lem.kernel import folders

ROOT = Path(__file__).resolve().parents[2]
HOOK = Path(sys.prefix) / "bin" / "lem-hook"
SELECTORS = ("corrections", "serve", "session-start", "precompact", "stop")
SLUG = "fix-the-login"
# The PATH of a Claude Code that a GUI app started (the design's part 5): no `lem` on it.
GUI_PATH = "/usr/bin:/bin"
BAD_INPUTS = (b"", b"not json", b"[1, 2]", b"\xff\xfe\x00", b'{"cwd": 3, "source": 4}')
# How long a test waits for a process the hook started on its own, in seconds: a guess, long
# for a script that writes one line.
STARTED_WAIT = 10.0


def manifest() -> dict[str, Any]:
    """The installed manifest's hooks, by event."""
    return json.loads((ROOT / "hooks" / "hooks.json").read_text())["hooks"]


def manifest_lines() -> dict[str, str]:
    """Each selector's command line, as the installed manifest gives it."""
    commands = (
        hook["command"]
        for groups in manifest().values()
        for group in groups
        for hook in group["hooks"]
    )
    return {command.split('hooks/run" ')[1].split()[0]: command for command in commands}


LINES = manifest_lines()


def workspace(folder: Path) -> Path:
    """A main checkout that uses Lem, with this Lem's state and the folder of one task in it;
    the task's folder."""
    (folder / ".git").mkdir(parents=True)
    (folder / ".lem" / "state" / "tasks" / SLUG).mkdir(parents=True)
    (folder / ".lem" / "settings.toml").write_text("")
    (folder / ".lem" / "state" / folders.MARKER).write_bytes(folders.FORM)
    return folder / ".lem" / "state" / "tasks" / SLUG


def old_workspace(folder: Path) -> Path:
    """A main checkout of Lem 0.3: its state holds the event log and a task's files, and no
    marker; the folder."""
    (folder / ".git").mkdir(parents=True)
    (folder / ".lem" / "state" / "tasks" / SLUG).mkdir(parents=True)
    (folder / ".lem" / "settings.toml").write_text("")
    (folder / ".lem" / "state" / "events.jsonl").write_text('{"event": "task.state"}\n')
    (folder / ".lem" / "state" / "tasks" / SLUG / "state.md").write_text("building\n")
    (folder / ".lem" / "state" / "tasks" / SLUG / "handoff.md").write_text("task: x\n")
    return folder


def started(checkout: Path, source: str = "startup") -> bytes:
    """A SessionStart event of a session in `checkout`."""
    event = {
        "session_id": "c0ffee",
        "transcript_path": "/claude/projects/x/c0ffee.jsonl",
        "source": source,
        "cwd": str(checkout),
        "hook_event_name": "SessionStart",
    }
    return json.dumps(event).encode()


def hooked(
    selector: str, stdin: bytes, **environ: str
) -> subprocess.CompletedProcess[bytes]:
    """Run the manifest's line of `selector` as Claude Code runs it."""
    return subprocess.run(
        ["/bin/sh", "-c", LINES[selector]],
        input=stdin,
        env=claude_environ(environ),
        cwd=tempfile.gettempdir(),
        capture_output=True,
        timeout=30,
        check=False,
    )


def launched(selector: str, stdin: bytes, **environ: str) -> subprocess.Popen[bytes]:
    """Start the manifest's line of `selector` and return at once, its event written."""
    child = subprocess.Popen(
        ["/bin/sh", "-c", LINES[selector]],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=claude_environ(environ),
        cwd=tempfile.gettempdir(),
    )
    assert child.stdin is not None
    child.stdin.write(stdin)
    child.stdin.close()
    return child


def claude_environ(environ: dict[str, str]) -> dict[str, str]:
    """The environment Claude Code gives a hook of a task's session, with `environ` over it."""
    return {
        **os.environ,
        "PATH": GUI_PATH,
        "CLAUDE_PLUGIN_ROOT": str(ROOT),
        "LEM_HOOK_BIN": str(HOOK),
        "LEM_TASK": SLUG,
        **environ,
    }


def stand_in(folder: Path, delay: float = 0) -> tuple[Path, Path]:
    """A `lem-hook` in `folder` that runs this checkout's hooks as if its Python were
    `folder/bin/python`, and the `lem` beside that Python, a script that waits `delay` seconds,
    then writes its arguments and the bytes of the file its last argument names as one record in
    the folder `calls`; the hook and `calls`.

    Each call writes its record in a hidden file of its own and renames it when it is whole, so a
    reader sees whole records only. Workers the hook starts detached run at the same time, and
    with one shared file a call's arguments could land after another call's bytes on one line
    (a full run on a loaded Mac, 2026-11-27)."""
    bin_folder = folder / "bin"
    bin_folder.mkdir(parents=True)
    calls = folder / "calls"
    hook = bin_folder / "lem-hook"
    code = (
        "import sys; sys.executable = sys.argv.pop(1); "
        "from lem.hooks import main; main.main()"
    )
    hook.write_text(
        f"#!/bin/sh\nexec '{sys.executable}' -I -B -c '{code}' "
        f"'{bin_folder / 'python'}' \"$@\"\n"
    )
    lem = bin_folder / "lem"
    lem.write_text(
        f"#!/bin/sh\nsleep {delay}\n"
        f"mkdir -p '{calls}'\n"
        f"part=$(mktemp '{calls}/.XXXXXX')\n"
        'echo "$*" > "$part"\n'
        "for last do :; done\n"
        '[ -f "$last" ] && cat "$last" >> "$part" && echo >> "$part"\n'
        f'mv "$part" \'{calls}\'/"${{part##*/.}}"\n'
    )
    hook.chmod(0o755)
    lem.chmod(0o755)
    return hook, calls


def records_of(calls: Path) -> list[Path]:
    """The whole records in the folder `calls`, by name."""
    if not calls.exists():
        return []
    return sorted(path for path in calls.iterdir() if not path.name.startswith("."))


def recorded(calls: Path) -> list[str]:
    """The lines of the whole records in `calls`: each record a line of words, its call, which
    the bytes of a file may follow."""
    return [
        line for path in records_of(calls) for line in path.read_text().splitlines()
    ]


def calls_of(calls: Path, count: int) -> list[str]:
    """The lines of the records in `calls` once it holds `count` of them; what it holds after
    STARTED_WAIT seconds else."""
    deadline = time.monotonic() + STARTED_WAIT
    while time.monotonic() < deadline:
        if len(records_of(calls)) >= count:
            return recorded(calls)
        time.sleep(0.05)
    return recorded(calls)


def files_of(folder: Path) -> dict[str, bytes]:
    """Each file under `folder`, by its path, with its bytes."""
    return {
        str(path): path.read_bytes()
        for path in sorted(folder.rglob("*"))
        if path.is_file()
    }
