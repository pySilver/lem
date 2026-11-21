"""The tokens a task's Claude Code sessions spent, read from their transcripts.

    task_tokens(state, slug)    the four sums, how many sessions and subagents were read, and a
                                sentence of what the number leaves out; None when the task's log
                                names no transcript

The plugin's SessionStart hook of a task's session (`session_hook.py`) logs each Claude Code session
of the task as `session.transcript`, with the session's id (`claude`) and the path of its transcript
(`transcript`). A transcript is one JSON record a line; an `assistant` record carries the reply's
`message.usage`, and Claude Code writes one record for each block of a reply, each with the same
`message.id` and the same `usage`, so a reply counts once by its id (read on 2026-11-21 in one
transcript of Claude Code 2.1.327, a task session of a scratch repository: 166 assistant records of 58
replies, the usage of one id the same in all its records). A session's subagents keep theirs beside it, in
`SESSION/subagents/agent-ID.jsonl` (the transcript's path less `.jsonl`), each with a `.meta.json`;
they count too. The four sums are `input_tokens`, `output_tokens`, `cache_read_input_tokens` and
`cache_creation_input_tokens`. A transcript that is gone, or a line that does not read, is passed
over and counted in `missing` and `unread`.

It counts only what Claude Code wrote on this machine: a Codex reviewer of a plan talk or of a
review round, an expert of another provider, and a session of the task on another machine are not
in it, and `covers` says so with the number.
"""

import json
from pathlib import Path

EVENT = "session.transcript"
# the usage's keys, by the name of each sum
SUMS = {"input": "input_tokens", "output": "output_tokens", "cache_read": "cache_read_input_tokens", "cache_write": "cache_creation_input_tokens"}


def transcripts_of(state: Path, slug: str) -> list[str]:
    """The transcripts the task's log names, each once, in the order they were logged."""
    found: list[str] = []
    log = state / "events.jsonl"
    try:
        lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return found
    for line in lines:
        if f'"{EVENT}"' not in line:
            continue
        try:
            record = json.loads(line)
        except ValueError:
            continue
        path = record.get("transcript") if isinstance(record, dict) and record.get("event") == EVENT and record.get("task") == slug else None
        if isinstance(path, str) and path and path not in found:
            found.append(path)
    return found


def add_file(file: Path, sums: dict, seen: set, counts: dict) -> bool:
    """Add the usage of each reply of one transcript file to SUMS, a reply once by its id (SEEN); False
    when the file does not read."""
    try:
        lines = file.read_bytes().splitlines()
    except OSError:
        return False
    for raw in lines:
        try:
            record = json.loads(raw.decode("utf-8", errors="replace"))
        except ValueError:
            counts["unread"] += 1
            continue
        if not isinstance(record, dict) or record.get("type") != "assistant" or not isinstance(record.get("message"), dict):
            continue
        message = record["message"]
        usage = message.get("usage")
        if not isinstance(usage, dict):
            continue
        key = message.get("id") or record.get("uuid")
        if key is not None:
            if key in seen:
                continue
            seen.add(key)
        for name, field in SUMS.items():
            value = usage.get(field)
            if isinstance(value, int) and not isinstance(value, bool):
                sums[name] += value
    return True


def task_tokens(state: Path, slug: str) -> dict | None:
    """The tokens of the task's Claude Code sessions on this machine and of their subagents: `input`,
    `output`, `cache_read`, `cache_write`; `sessions` and `subagents`, how many files of each were read;
    `missing`, the transcripts the log names that are gone; `unread`, the lines that did not read; and
    `covers`, what the number holds and leaves out. None when the log names no transcript of the task."""
    named = transcripts_of(state, slug)
    if not named:
        return None
    sums = dict.fromkeys(SUMS, 0)
    counts = {"sessions": 0, "subagents": 0, "missing": 0, "unread": 0}
    seen: set = set()
    for path in named:
        main = Path(path)
        if not add_file(main, sums, seen, counts):
            counts["missing"] += 1
            continue
        counts["sessions"] += 1
        folder = main.with_suffix("") / "subagents"
        for agent in sorted(folder.glob("agent-*.jsonl")) if folder.is_dir() else []:
            if add_file(agent, sums, seen, counts):
                counts["subagents"] += 1
    gone = f"; {counts['missing']} transcript{'s' if counts['missing'] != 1 else ''} the log names {'are' if counts['missing'] != 1 else 'is'} gone" if counts["missing"] else ""
    covers = (f"the Claude Code sessions of the task on this machine ({counts['sessions']}) and their subagents ({counts['subagents']}){gone}; "
              "a Codex reviewer, an expert of another provider and a session on another machine are not in it")
    return {**sums, **counts, "covers": covers}
