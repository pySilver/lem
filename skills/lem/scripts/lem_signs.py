"""The signs of work of a task's Claude Code session, from Claude Code's own files, for `lem session list`.

    read_signs(records, session, turns, processes, table)
                    the pure rule: {"sign", "shell", "signs"} from the facts below
    facts_of(records, session, table)
                    the facts, read from the files the records name

Three facts tell whether a task's session still works, beside the task's own events (which the
board's model reads): when its main thread or one of its subagents last wrote a turn (`sign`),
whether a shell command of the session runs now (`shell`), and whether the two could be read at all
(`signs`). The board server's guard of a stopped session (`serve.py`) sends a message only when
`shell` is false and the task's newest sign of work is old: with `signs` true the newest of `sign`
and of the task's events, with `signs` false the task's events alone.

Where each fact is, as read on this Mac with Claude Code 2.1.330 on 2026-11-22:

- The task's Claude Code sessions are its `session.transcript` events, which the plugin's
  SessionStart hook logs (`session_hook.py`): `claude`, the Claude Code session's id, `transcript`,
  the path of its transcript, and `session`, the agterm session the hook ran in
  (`AGTERM_SESSION_ID`). Only the records whose `session` is the task's newest session count, in no
  regard to case: the old pane's `/clear`, or a background host of Claude Code that runs with another
  pane's environment, writes a record of another session. A record with no `session` counts for none.
- A transcript is `FOLDER/projects/NAME/ID.jsonl`, one JSON record a line. Its newest sign is the
  `timestamp` of its newest record whose `type` is `user` or `assistant` (a prompt, a tool's result,
  a reply), read from the file's end; never the file's time. A message that reaches an idle or parked
  pane writes a `queue-operation` record and runs no turn, and `attachment`, `system`, `cost-state`,
  `continued-in` and `api-request` records are no turn either.
- A subagent writes `FOLDER/projects/NAME/ID/subagents/agent-*.jsonl` (each with an
  `agent-*.meta.json` beside it), read by the same rule.
- The process of a Claude Code session is `FOLDER/sessions/PID.json`, with `pid` and `sessionId`,
  in the folder that holds the transcript (its third parent), never one found from this process's
  own `CLAUDE_CONFIG_DIR`.
- A command of the Bash tool, a background one too (`run_in_background`), is a direct child of that
  pid in `ps -A -o pid=,ppid=,command=` whose command line sources `shell-snapshots/snapshot-`. A
  subagent's Bash command has the same parent and the same form (seen with a subagent's
  `sleep 40`, 2026-11-22). Other children, a hook's process or `caffeinate`, are no shell command.

`signs` is false when no record of the session names a transcript, when no process file of the
transcript's folder names one of the session's Claude Code ids, or when no such pid is in the
process table: with no process to read there is no evidence that no shell runs, and a guard that
restarted such a session could put two agents on one task. So the guard counts only the task's
events for it (`lem_board_model.stop_due`): the status message, then the owner's row "stopped",
and never a fresh session that the owner did not open.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

# the record types that are a turn of the session (see the module docstring, 2026-11-22)
TURNS = ("user", "assistant")
# the mark of a Bash tool's command line: it sources the shell's snapshot first
SNAPSHOT = "shell-snapshots/snapshot-"
# how much of a transcript is read at a time from its end
BLOCK = 65536
EVENT = "session.transcript"


def own_records(records: list[dict], session: str | None) -> list[dict]:
    """The `session.transcript` records of the agterm session SESSION, in no regard to case, each with
    the strings `claude` and `transcript`."""
    if not session:
        return []
    want = str(session).upper()
    return [record for record in records
            if record.get("event", EVENT) == EVENT and isinstance(record.get("session"), str) and record["session"].upper() == want
            and isinstance(record.get("claude"), str) and record["claude"] and isinstance(record.get("transcript"), str) and record["transcript"]]


def folder_of(transcript: str) -> str | None:
    """The Claude Code folder of a transcript `FOLDER/projects/NAME/ID.jsonl`, or None for a path that is
    not in that form."""
    parents = Path(transcript).parents
    return str(parents[2]) if len(parents) > 2 and parents[1].name == "projects" else None


def when(text: object) -> datetime | None:
    if not isinstance(text, str) or not text:
        return None
    try:
        found = datetime.fromisoformat(text)
    except ValueError:
        return None
    return (found if found.tzinfo else found.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)


def newest_turn(lines) -> str | None:
    """The `timestamp` of the first turn among LINES, a transcript's lines from its newest to its oldest
    (bytes or text), as Lem writes a time (`%Y-%m-%dT%H:%M:%SZ`); None when no line is a turn."""
    for raw in lines:
        try:
            record = json.loads(raw)
        except ValueError:
            continue
        if isinstance(record, dict) and record.get("type") in TURNS and (found := when(record.get("timestamp"))):
            return found.strftime("%Y-%m-%dT%H:%M:%SZ")
    return None


def table_rows(table: str) -> list[tuple[int, int, str]]:
    """The rows of `ps -A -o pid=,ppid=,command=`: pid, parent pid and command line."""
    rows = []
    for line in table.splitlines():
        parts = line.split(None, 2)
        if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
            rows.append((int(parts[0]), int(parts[1]), parts[2] if len(parts) > 2 else ""))
    return rows


def read_signs(records: list[dict], session: str | None, turns: dict[str, list], processes: dict[str, list], table: str | None) -> dict:
    """The signs of work of the agterm session SESSION, from the facts:

    RECORDS     the task's `session.transcript` events
    TURNS       {transcript: [newest turn of the transcript, of each subagent, ...]}, each a time or None
    PROCESSES   {Claude Code folder: [the process files of its `sessions/`, each a dict]}
    TABLE       the text of `ps -A -o pid=,ppid=,command=`, or None when it could not be read

    It gives `sign`, the newest of those turns or None, `shell`, whether a direct child of the
    session's Claude Code process sources the shell's snapshot, and `signs`, whether there was
    something to read: a record of the session, and a live process of it in a process file."""
    mine = own_records(records, session)
    times = [found for record in mine for text in turns.get(record["transcript"], []) if (found := when(text))]
    sign = max(times).strftime("%Y-%m-%dT%H:%M:%SZ") if times else None
    ids = {record["claude"] for record in mine}
    folders = {folder for record in mine if (folder := folder_of(record["transcript"]))}
    pids = {int(process["pid"]) for folder in folders for process in processes.get(folder, [])
            if isinstance(process, dict) and process.get("sessionId") in ids and str(process.get("pid", "")).isdigit()}
    rows = table_rows(table) if table is not None else []
    running = pids & {pid for pid, _, _ in rows}
    if not mine or not running:
        return {"sign": sign, "shell": False, "signs": False}
    shell = any(parent in running and SNAPSHOT in command for _, parent, command in rows)
    return {"sign": sign, "shell": shell, "signs": True}


def tail_lines(path: Path, block: int = BLOCK):
    """The lines of a file from its end to its start, as bytes, read BLOCK bytes at a time."""
    with path.open("rb") as handle:
        handle.seek(0, 2)
        end, rest = handle.tell(), b""
        while end > 0:
            start = max(0, end - block)
            handle.seek(start)
            lines = (handle.read(end - start) + rest).split(b"\n")
            end = start
            # the first piece may be the end of a line that starts in the block before
            rest = lines.pop(0) if start > 0 else b""
            yield from reversed(lines)


def file_turn(path: Path) -> str | None:
    try:
        return newest_turn(tail_lines(path))
    except OSError:
        return None


def facts_of(records: list[dict], session: str | None, table: str | None) -> dict:
    """The facts `read_signs` takes, read from the files the session's records name: the newest turn
    of each transcript and of each of its subagents, and the process files of each transcript's folder."""
    turns: dict[str, list] = {}
    processes: dict[str, list] = {}
    for record in own_records(records, session):
        transcript = Path(record["transcript"])
        subagents = sorted((transcript.parent / transcript.stem / "subagents").glob("agent-*.jsonl"))
        turns[record["transcript"]] = [file_turn(path) for path in (transcript, *subagents) if path.is_file()]
        folder = folder_of(record["transcript"])
        if folder and folder not in processes:
            found = []
            for path in sorted(Path(folder, "sessions").glob("*.json")):
                try:
                    found.append(json.loads(path.read_text(encoding="utf-8", errors="replace")))
                except (OSError, ValueError):
                    continue
            processes[folder] = found
    return {"records": records, "session": session, "turns": turns, "processes": processes, "table": table}


def signs_of(records: list[dict], session: str | None, table: str | None) -> dict:
    """`read_signs` over the facts read now."""
    return read_signs(**facts_of(records, session, table))
