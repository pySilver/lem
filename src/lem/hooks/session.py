"""The `session-start` hook: a task's Claude Code session on record, and the plugin's folder for
the session's commands.

A task's session has `LEM_TASK=SLUG` from its launch line (`lem session open`). For it, the hook
appends one framed line to `tasks/SLUG/sessions.jsonl` (the design's part 3): a line end, the JSON
of `records.sessions.SessionLine` and a line end, in one write on a file opened to append, so
that two writers never mix their bytes. The line says what the hook saw: the Claude Code session
(`session_id`), its transcript (`transcript_path`), the source, and the agterm session it runs in
(`AGTERM_SESSION_ID`). A hook never writes `task.json` and never waits on a lock. After a
compaction it gives the task's record and handoff (`precompact.restored`).

In every session it appends `export LEM_PLUGIN_ROOT=...` to the file `CLAUDE_ENV_FILE` names,
which the session's Bash tool runs before each command, so that a `lem` of that session checks
the plugin's version too; and it says, as a `systemMessage` shown to the owner, the version line
and the line of another `lem` first on the PATH (`other.py`). Claude Code's hooks reference, read
2026-11-25: a SessionStart hook's plain stdout is context for Claude, and `systemMessage` of its
JSON is a warning shown to the user.
"""

import json
import time

from lem.hooks import other, precompact, raw, where

TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Mapping

# The form of a line, `records.sessions.VERSION`, and the sources it may name.
VERSION = 1
SOURCES = ("startup", "resume", "clear", "compact", "fork")
SESSIONS = "sessions.jsonl"
SOURCE = "source"


def answer(environ: Mapping[str, str], behind: str | None) -> str:
    """The hook's whole work, and what it prints: the task's context, with the lines for the
    owner beside it when there are any."""
    plugin = environ.get("CLAUDE_PLUGIN_ROOT", "")
    if plugin:
        keep_root(environ.get("CLAUDE_ENV_FILE", ""), plugin)
    another = other.other_lem(environ.get("PATH", ""), other.own_command())
    lines = [line for line in (behind, another) if line]
    said = "" if behind else recorded(environ)
    return shown(lines, said) if lines else said


def shown(lines: list[str], said: str) -> str:
    """The lines for the owner as a `systemMessage`, and the task's context `said` beside them
    as the session's context."""
    message: dict[str, object] = {"systemMessage": "\n".join(lines)}
    if said.strip():
        message["hookSpecificOutput"] = {
            "hookEventName": "SessionStart",
            "additionalContext": said,
        }
    encoded = json.dumps(message, ensure_ascii=False)
    return f"{encoded}\n"


def recorded(environ: Mapping[str, str]) -> str:
    """Put the session on record in its task's folder, and give the task's context after a
    compaction once its line is on record; nothing for a session that is no task's, for an
    input that is no SessionStart event, or when the folder does not take the line."""
    found = raw.event()
    try:
        folder = task_of(found, environ)
    except OSError, ValueError:
        return ""
    frame = framed(found, folder, environ) if folder else None
    if folder is None or frame is None:
        return ""
    kept = raw.append(f"{folder}/{SESSIONS}", frame)
    compacted = raw.text(found, SOURCE) == "compact"
    return precompact.restored(folder) if kept and compacted else ""


def task_of(found: raw.Event, environ: Mapping[str, str]) -> str | None:
    """The folder of the task of a SessionStart event; None for any other input."""
    if raw.text(found, "hook_event_name") != "SessionStart":
        return None
    return where.task_folder(found, environ)


def framed(found: raw.Event, folder: str, environ: Mapping[str, str]) -> bytes | None:
    """The framed line of the session the event names, for the task of `folder`, in the
    agterm session of `environ`; None when the event names no Claude Code session, no
    transcript, or a source of no known name."""
    line = {
        "v": VERSION,
        "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        SOURCE: raw.text(found, SOURCE),
        "claude": raw.text(found, "session_id"),
        "transcript": raw.text(found, "transcript_path"),
        "task": folder.rpartition("/")[2],
    }
    if not all(line.values()) or line[SOURCE] not in SOURCES:
        return None
    pane = environ.get("AGTERM_SESSION_ID", "").strip() or None
    encoded = json.dumps({**line, "pane": pane}, ensure_ascii=False).encode()
    return b"".join((b"\n", encoded, b"\n"))


def keep_root(target: str, plugin: str) -> None:
    """Append `export LEM_PLUGIN_ROOT='PLUGIN'` to the file `target`, when one is named."""
    if target:
        quoted = plugin.replace("'", r"'\''")
        raw.append(target, f"export LEM_PLUGIN_ROOT='{quoted}'\n".encode())
