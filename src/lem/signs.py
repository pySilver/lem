"""The signs of work of a task's Claude Code session, from Claude Code's own files,
for `lem session list`.

    read_signs(records, session, turns, processes, table, slug, named, mains)
                    the pure rule: {"sign", "shell", "signs", "turn"} from the facts below
    turn_of(lines)  the pure rule of `turn`, over a transcript's lines from its end
    facts_of(records, session, table, slug)
                    the facts, read from the files the records name

Four facts tell whether a task's session still works, beside the task's own events
(which the board's model reads): when its main thread or one of its subagents last wrote
a turn (`sign`), whether a shell command of the session runs now (`shell`), whether
those could be read at all (`signs`), and whether the newest turn of the session's main
thread still runs (`turn`: `"runs"`, `"ended"`, or None when no record tells). The board
server's guard of a stopped session (`serve.py`) sends a message only when `shell` is
false and the task's newest sign of work is old: with `signs` true the newest of `sign`
and of the task's events, with `signs` false the task's events alone. A held task of the
owner's whose `turn` runs is Lem's work and no row of what waits for him until that turn
ends (`lem_board_model.put_sessions`).

Where each fact is, as read on this Mac with Claude Code 2.1.330 on 2026-11-22:

- The task's Claude Code sessions are its `session.transcript` events, which the
  plugin's SessionStart hook logs (`session_hook.py`): `claude`, the Claude Code
  session's id, `transcript`, the path of its transcript, and `session`, the agterm
  session the hook ran in (`AGTERM_SESSION_ID`). Only the records whose `session` is the
  task's newest session count, in no regard to case: the old pane's `/clear`, or a
  background host of Claude Code that runs with another pane's environment, writes a
  record of another session. A record with no `session` counts for none.
- A record of the task's newest session whose transcript's first prompt is the launch
  line of another task counts for none either: a fork that another task's session makes
  in a background host started from this task's pane is logged under this task and this
  pane (6fe214ec, a fork of the session of merge-leaves-board-lock, logged under
  board-card-search on 2026-11-22). The task a first prompt names is `lem_tokens`' rule
  (`first_prompt`, `task_named`), read only for the records of the newest session, so
  that no old pane's transcript is opened; a first prompt that names no task (a
  `/clear`) keeps the record's task.
- A transcript is `FOLDER/projects/NAME/ID.jsonl`, one JSON record a line. Its newest
  sign is the `timestamp` of its newest record whose `type` is `user` or `assistant` (a
  prompt, a tool's result, a reply), read from the file's end; never the file's time. A
  message that reaches an idle or parked pane writes a `queue-operation` record and runs
  no turn, and `attachment`, `system`, `cost-state`, `continued-in` and `api-request`
  records are no turn either, nor a `user` record that `turn` skips (a local command's
  text, a compaction's summary).
- `turn` is read from the newest decisive record of the main transcript, from its end,
  and of the session's records only from the transcript whose main thread wrote the
  newest turn (`turn_of`). An `assistant` record with `stop_reason` `tool_use` runs,
  unless its tool is the question widget (`AskUserQuestion`), which asks the owner and
  so ends the turn; one with any other `stop_reason` (`end_turn`, `stop_sequence`,
  `refusal`, `max_tokens`) ended, and one with none is skipped. A `user` record that is
  an interrupt (`[Request interrupted`) ended; one of a local command (its text starts
  with `<command-name>`, `<command-message>`, `<command-args>`, `<local-command-`,
  `<bash-input>`, `<bash-stdout>` or `<bash-stderr>`) or a compaction's summary
  (`isCompactSummary`) is skipped, since none runs a turn; any other `user` record (a
  prompt, a tool's result, a task notification, a skill's text) runs. Every other type,
  and every `isSidechain` record, is skipped. Three probes of 2026-11-23 over the 300
  newest transcripts on this Mac, Claude Code 2.1.294 to 2.1.330: the main thread's
  assistant records stopped 53,528 times on `tool_use`, 5,411 on `end_turn`, 29 on
  `stop_sequence` (an API error's message), 3 on null and 1 on `refusal`; a
  `turn_duration` record followed 4,114 of 4,122 ended turns but none of 8 interrupts,
  so it is no mark of an end; and Claude Code's own `status` in `sessions/PID.json` read
  `busy` for 4 of 26 live sessions whose main transcript had ended on `end_turn`, so it
  is no mark of a running turn. A subagent's transcript is never read for `turn`: an
  interview's scout runs in the background while the session's turn has ended on its
  question to the owner.
- A subagent writes `FOLDER/projects/NAME/ID/subagents/agent-*.jsonl` (each with an
  `agent-*.meta.json` beside it), read by the same rule.
- The process of a Claude Code session is `FOLDER/sessions/PID.json`, with `pid` and
  `sessionId`, in the folder that holds the transcript (its third parent), never one
  found from this process's own `CLAUDE_CONFIG_DIR`.
- A command of the Bash tool, a background one too (`run_in_background`), is a direct
  child of that pid in `ps -A -o pid=,ppid=,command=` whose command line sources
  `shell-snapshots/snapshot-`. A subagent's Bash command has the same parent and the
  same form (seen with a subagent's `sleep 40`, 2026-11-22). Other children, a hook's
  process or `caffeinate`, are no shell command.

`signs` is false, and `turn` None, when no record of the session names a transcript,
when no process file of the transcript's folder names one of the session's Claude Code
ids, or when no such pid is in the process table: with no process to read there is no
evidence that no shell runs, and a guard that restarted such a session could put two
agents on one task. So the guard counts only the task's events for it
(`lem_board_model.stop_due`): the status message, then the owner's row "stopped", and
never a fresh session that the owner did not open.
"""  # noqa: E501 - the table of the module's functions keeps its columns

import json
from datetime import UTC, datetime
from pathlib import Path

# a moment as Lem writes it
from lem import clock as lem_clock

# the task a transcript's first prompt names; the scripts' folder is on the path of
# every importer
from lem import tokens as lem_tokens

# typing's flag, without the import of typing, which a hook's start does not pay
TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

# the record types that are a turn of the session (see the module docstring, 2026-11-22)
TURNS = ("user", "assistant")
# what `turn` says of the session's main thread (see the module docstring, 2026-11-23)
RUNS, ENDED = "runs", "ended"
# the stop reason of an assistant record whose tool runs, and the one tool of it that
# asks the owner
TOOL_USE, ASKS = "tool_use", "AskUserQuestion"
# the start of a user record's text that is an interrupt, and of one that is a
# local command
INTERRUPT = "[Request interrupted"
LOCAL = (
    "<command-name>",
    "<command-message>",
    "<command-args>",
    "<local-command-",
    "<bash-input>",
    "<bash-stdout>",
    "<bash-stderr>",
)
# the mark of a Bash tool's command line: it sources the shell's snapshot first
SNAPSHOT = "shell-snapshots/snapshot-"
# how much of a transcript is read at a time from its end
BLOCK = 65536
EVENT = "session.transcript"


def own_records(records: list[dict], session: str | None) -> list[dict]:
    """The `session.transcript` records of the agterm session SESSION, in no regard to
    case, each with the strings `claude` and `transcript`."""
    if not session:
        return []
    want = session.upper()
    return [
        record
        for record in records
        if record.get("event", EVENT) == EVENT
        and isinstance(record.get("session"), str)
        and record["session"].upper() == want
        and isinstance(record.get("claude"), str)
        and record["claude"]
        and isinstance(record.get("transcript"), str)
        and record["transcript"]
    ]


def folder_of(transcript: str) -> str | None:
    """The Claude Code folder of a transcript `FOLDER/projects/NAME/ID.jsonl`, or None
    for a path that is not in that form."""
    parents = Path(transcript).parents
    return str(parents[2]) if parents[2:] and parents[1].name == "projects" else None


def when(text: object) -> datetime | None:
    if not isinstance(text, str) or not text:
        return None
    try:
        found = datetime.fromisoformat(text)
    except ValueError:
        return None
    return (found if found.tzinfo else found.replace(tzinfo=UTC)).astimezone(UTC)


def newest_turn(lines: Iterable[str | bytes]) -> str | None:
    """The `timestamp` of the first turn among LINES, a transcript's lines from its
    newest to its oldest (bytes or text), as Lem writes a time (`%Y-%m-%dT%H:%M:%SZ`);
    None when no line is a turn. A `user` record that runs no turn (`runs_none`) is
    none: the output of the owner's `/cost` is no work of the session."""
    for raw in lines:
        try:
            record = json.loads(raw)
        except ValueError:
            continue
        found = (
            when(record.get("timestamp"))
            if isinstance(record, dict)
            and record.get("type") in TURNS
            and not runs_none(record)
            else None
        )
        if found:
            return lem_clock.stamp(found)
    return None


def runs_none(record: dict) -> bool:
    """Whether a `user` record runs no turn: a local command's text or a compaction's
    summary (`turn_of` skips both)."""
    if record.get("type") != "user":
        return False
    texts = texts_of(record)
    return bool(
        record.get("isCompactSummary") or (texts and texts[0].startswith(LOCAL))
    )


def texts_of(record: dict) -> list[str]:
    """The text of a record's message: its content when that is a string, else each of
    its text parts."""
    message = record.get("message")
    body = message.get("content") if isinstance(message, dict) else None
    if isinstance(body, str):
        return [body]
    if isinstance(body, list):
        return [
            part["text"]
            for part in body
            if isinstance(part, dict)
            and part.get("type") == "text"
            and isinstance(part.get("text"), str)
        ]
    return []


def turn_of(lines: Iterable[str | bytes]) -> str | None:
    """`RUNS` or `ENDED` by the newest decisive record among LINES, a main transcript's
    lines from its newest to its oldest (bytes or text), by the rule of the module
    docstring; None when no record decides."""
    for raw in lines:
        try:
            record = json.loads(raw)
        except ValueError:
            continue
        if not isinstance(record, dict) or record.get("isSidechain"):
            continue
        if record.get("type") == "assistant":
            message = (
                record["message"] if isinstance(record.get("message"), dict) else {}
            )
            reason = message.get("stop_reason")
            if not reason:
                continue
            if reason != TOOL_USE:
                return ENDED
            body = message.get("content")
            asks = isinstance(body, list) and any(
                isinstance(part, dict)
                and part.get("type") == "tool_use"
                and part.get("name") == ASKS
                for part in body
            )
            return ENDED if asks else RUNS
        if record.get("type") == "user":
            texts = texts_of(record)
            if any(text.startswith(INTERRUPT) for text in texts):
                return ENDED
            if runs_none(record):
                continue
            return RUNS
    return None


def table_rows(table: str) -> list[tuple[int, int, str]]:
    """The rows of `ps -A -o pid=,ppid=,command=`: pid, parent pid and command line."""
    rows = []
    for line in table.splitlines():
        # a line of fewer parts leaves "" in their place, which is no pid
        pid, ppid, command = [*line.split(None, 2), "", ""][:3]
        if pid.isdigit() and ppid.isdigit():
            rows.append((int(pid), int(ppid), command))
    return rows


def read_signs(  # noqa: PLR0913, PLR0917 - over the limit before the limit was set
    records: list[dict],
    session: str | None,
    turns: dict[str, list],
    processes: dict[str, list],
    table: str | None,
    slug: str,
    named: dict[str, str | None],
    mains: dict[str, list],
) -> dict:
    """The signs of work of the agterm session SESSION of the task SLUG, from the facts:

    RECORDS     the task's `session.transcript` events
    TURNS       {transcript: [newest turn of the transcript, of each subagent, ...]}, each a time or None
    PROCESSES   {Claude Code folder: [the process files of its `sessions/`, each a dict]}
    TABLE       the text of `ps -A -o pid=,ppid=,command=`, or None when it could not be read
    NAMED       {transcript: the task its first prompt names, or None}
    MAINS       {transcript: [newest turn of its main thread, `turn_of` its main thread]}

    Of the session's records, one whose transcript names another task than SLUG counts
    for none. It gives `sign`, the newest of those turns or None, `shell`, whether a
    direct child of the session's Claude Code process sources the shell's snapshot,
    `signs`, whether there was something to read: a record of the session, and a live
    process of it in a process file, and `turn`, the main thread's turn of the
    transcript whose main thread wrote the newest turn, None when `signs` is false."""  # noqa: E501 - the table of the facts keeps its columns
    mine = [
        record
        for record in own_records(records, session)
        if named.get(record["transcript"]) in (None, slug)
    ]
    times = [
        found
        for record in mine
        for text in turns.get(record["transcript"], [])
        if (found := when(text))
    ]
    sign = lem_clock.stamp(max(times)) if times else None
    ids = {record["claude"] for record in mine}
    folders = {folder for record in mine if (folder := folder_of(record["transcript"]))}
    pids = {
        int(process["pid"])
        for folder in folders
        for process in processes.get(folder, [])
        if isinstance(process, dict)
        and process.get("sessionId") in ids
        and str(process.get("pid", "")).isdigit()
    }
    rows = [] if table is None else table_rows(table)
    running = pids & {pid for pid, _, _ in rows}
    if not mine or not running:
        return {"sign": sign, "shell": False, "signs": False, "turn": None}
    shell = any(
        parent in running and SNAPSHOT in command for _, parent, command in rows
    )
    newest = [
        (found, main[1])
        for record in mine
        if len(main := mains.get(record["transcript"]) or []) == 2  # noqa: PLR2004 - MAINS holds a pair
        and (found := when(main[0]))
    ]
    turn = max(newest, key=lambda pair: pair[0])[1] if newest else None
    return {"sign": sign, "shell": shell, "signs": True, "turn": turn}


def tail_lines(path: Path, block: int = BLOCK) -> Iterator[bytes]:
    """The lines of a file from its end to its start, as bytes, read BLOCK bytes at
    a time."""
    with path.open("rb") as stream:
        stream.seek(0, 2)
        end, rest = stream.tell(), b""
        while end > 0:
            start = max(0, end - block)
            stream.seek(start)
            lines = (stream.read(end - start) + rest).split(b"\n")
            end = start
            # the first piece may be the end of a line that starts in the block before
            rest = lines.pop(0) if start > 0 else b""
            yield from reversed(lines)


def file_turn(path: Path) -> str | None:
    try:
        return newest_turn(tail_lines(path))
    except OSError:
        return None


def file_main(path: Path) -> list:
    """[the newest turn, `turn_of`] of the main transcript at PATH, each read from
    its end."""
    try:
        return [newest_turn(tail_lines(path)), turn_of(tail_lines(path))]
    except OSError:
        return [None, None]


def facts_of(
    records: list[dict], session: str | None, table: str | None, slug: str
) -> dict:
    """The facts `read_signs` takes, read from the files the session's records name: the
    task each transcript's first prompt names, and, for a transcript that names no other
    task than SLUG, the newest turn of it and of each of its subagents, the newest turn
    and the turn of its main thread alone, and the process files of its folder. No file
    of a record of another session is opened."""
    turns: dict[str, list] = {}
    mains: dict[str, list] = {}
    processes: dict[str, list] = {}
    named: dict[str, str | None] = {}
    for record in own_records(records, session):
        if record["transcript"] not in named:
            named[record["transcript"]] = lem_tokens.task_named(
                lem_tokens.first_prompt(Path(record["transcript"]))
            )
        if named[record["transcript"]] not in (None, slug):
            continue
        transcript = Path(record["transcript"])
        subagents = sorted(
            (transcript.parent / transcript.stem / "subagents").glob("agent-*.jsonl")
        )
        turns[record["transcript"]] = [
            file_turn(path) for path in (transcript, *subagents) if path.is_file()
        ]
        if transcript.is_file():
            mains[record["transcript"]] = file_main(transcript)
        folder = folder_of(record["transcript"])
        if folder and folder not in processes:
            found = []
            for path in sorted(Path(folder, "sessions").glob("*.json")):
                try:
                    found.append(
                        json.loads(path.read_text(encoding="utf-8", errors="replace"))
                    )
                except OSError, ValueError:
                    continue
            processes[folder] = found
    return {
        "records": records,
        "session": session,
        "turns": turns,
        "processes": processes,
        "table": table,
        "slug": slug,
        "named": named,
        "mains": mains,
    }


def signs_of(
    records: list[dict], session: str | None, table: str | None, slug: str
) -> dict:
    """`read_signs` over the facts read now, for the task SLUG."""
    return read_signs(**facts_of(records, session, table, slug))
