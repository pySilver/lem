"""The tokens a task's Claude Code sessions spent, read from their transcripts.

    task_tokens(state, slug)    the four sums, how many sessions and subagents were read, and a
                                sentence of what the number leaves out; None when no transcript
                                the log names counts for the task
    transcripts_of(state, slug) the transcripts that count for the task, each once
    first_prompt(file)          the text of a transcript's first prompt; None when the file does not read
    task_named(text)            the task whose launch line TEXT is; None for any other text

The plugin's SessionStart hook of a task's session (`session_hook.py`) logs each Claude
Code session of the task as `session.transcript`, with the session's id (`claude`) and
the path of its transcript (`transcript`). A transcript is one JSON record a line; an
`assistant` record carries the reply's `message.usage`, and Claude Code writes one
record for each block of a reply, each with the same `message.id` and the same `usage`,
so a reply counts once by its id (read on 2026-11-21 in one transcript of Claude Code
2.1.327, a task session of a scratch repository: 166 assistant records of 58 replies,
the usage of one id the same in all its records). A session's subagents keep theirs
beside it, in `SESSION/subagents/agent-ID.jsonl` (the transcript's path less `.jsonl`),
each with a `.meta.json`; they count too. The four sums are `input_tokens`,
`output_tokens`, `cache_read_input_tokens` and `cache_creation_input_tokens`. A
transcript that is gone, or a line that does not read, is passed over and counted in
`missing` and `unread`.

A transcript counts for the task whose session it is, and that is read from the
transcript, not from its record: the hook logs a record with the task of its
environment, and Claude Code's background host keeps the environment of the pane that
started it. So a fork of one task's session made in a host that another task's pane
started is logged under that other task (6fe214ec, a fork, `source: fork` and
`sessionKind: bg` in its records, of the session of merge-leaves-board-lock, logged
under board-card-search on 2026-11-22; the probe of the task that found it, over the 98
`session.transcript` records of this repository's log on 2026-11-23, found that one
record and no other on another task than its first prompt names). A fork copies its
parent's first prompt, the launch line `lem session open` gives a task's session (`Read
TASK_DIR/session.md and follow it.`, `launch_line` in `session.py`). So each
`session.transcript` record of the log is read, whatever its task: a transcript counts
for the task its first prompt names when that prompt is a launch line, whole, and for
the task its record names when it is not (the owner's own words after a `/clear`) or
when the file does not read. A launch line of a task that ended still names that task.
The `transcripts` of a `task.summary`, which `lem project prune` writes in the place of
an ended task's events, are read as records of that summary's task, so a fork still
counts for its open task after the record of the task it was logged under became
that summary.

It counts only what Claude Code wrote on this machine: a Codex reviewer of a plan talk
or of a review round, an expert of another provider, and a session of the task on
another machine are not in it, and `covers` says so with the number.
"""

import json
import re
from pathlib import Path

# how a JSON-lines file is split into its lines; the scripts' folder is on the path of
# every importer
import lem_state

EVENT = "session.transcript"
# the one event that stands for the events of an ended task (project.py SUMMARY), with
# the `transcripts` of its `session.transcript` records
SUMMARY = "task.summary"
# the usage's keys, by the name of each sum
SUMS = {
    "input": "input_tokens",
    "output": "output_tokens",
    "cache_read": "cache_read_input_tokens",
    "cache_write": "cache_creation_input_tokens",
}
# the first prompt of a task's session, `launch_line` in session.py: TASK_DIR is the
# state folder's `tasks/SLUG`, and the state folder is `.lem/state` of the main checkout
# (lem_state STATE)
LAUNCH = re.compile(
    r"Read [^\n]*/\.lem/state/tasks/(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)/session\.md and "
    r"follow it\."
)


def task_named(text: str | None) -> str | None:
    """The slug of the task whose launch line TEXT is, whole; None for any other text,
    also one that holds such a path among other words (a path the owner pasted after
    a `/clear`)."""
    found = LAUNCH.fullmatch(text) if isinstance(text, str) else None
    return found["slug"] if found else None


def first_prompt(file: Path) -> str | None:
    """The text of the transcript's first prompt, its first `user` record that is not
    `isMeta`, read from the file's start up to that record; None when the file does not
    read or holds no such record. A prompt of text blocks gives their texts; one with
    another block is no text and gives ""."""
    try:
        with file.open("rb") as lines:
            for raw in lines:
                try:
                    record = json.loads(raw.decode("utf-8", errors="replace"))
                except ValueError:
                    continue
                if (
                    not isinstance(record, dict)
                    or record.get("type") != "user"
                    or record.get("isMeta")
                ):
                    continue
                content = (
                    record.get("message", {}).get("content")
                    if isinstance(record.get("message"), dict)
                    else None
                )
                if isinstance(content, str):
                    return content
                blocks = content if isinstance(content, list) else []
                if blocks and all(
                    isinstance(block, dict)
                    and block.get("type") == "text"
                    and isinstance(block.get("text"), str)
                    for block in blocks
                ):
                    return "\n".join(block["text"] for block in blocks)
                return ""
    except OSError:
        return None
    return None


def logged(state: Path) -> list[tuple[str, str]]:
    """Each transcript the log names, as (the task its record names, its path), in the
    log's order: each `session.transcript` record, and each of the `transcripts` of a
    `task.summary` as a record of the summary's task."""
    found: list[tuple[str, str]] = []
    try:
        lines = lem_state.jsonl_lines(
            (state / "events.jsonl").read_text(encoding="utf-8", errors="replace")
        )
    except OSError:
        return found
    for line in lines:
        if f'"{EVENT}"' not in line and f'"{SUMMARY}"' not in line:
            continue
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if not isinstance(record, dict) or not isinstance(record.get("task"), str):
            continue
        if record.get("event") == EVENT:
            paths = [record.get("transcript")]
        elif record.get("event") == SUMMARY and isinstance(
            record.get("transcripts"), list
        ):
            paths = record["transcripts"]
        else:
            continue
        found += [
            (record["task"], path) for path in paths if isinstance(path, str) and path
        ]
    return found


def transcripts_of(state: Path, slug: str) -> list[str]:
    """The transcripts that count for the task, each once, in the order they were
    logged: of every transcript the log names, under any task, each whose first prompt
    names the task, and each whose first prompt names no task and whose record names the
    task. Each file's first prompt is read once."""
    found: list[str] = []
    named: dict[str, str | None] = {}
    for task, path in logged(state):
        if path not in named:
            named[path] = task_named(first_prompt(Path(path)))
        mine = named[path] == slug or (named[path] is None and task == slug)
        if mine and path not in found:
            found.append(path)
    return found


def add_file(file: Path, sums: dict, seen: set, counts: dict) -> bool:
    """Add the usage of each reply of one transcript file to SUMS, a reply once by its
    id (SEEN); False when the file does not read."""
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
        if (
            not isinstance(record, dict)
            or record.get("type") != "assistant"
            or not isinstance(record.get("message"), dict)
        ):
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
    """The tokens of the task's Claude Code sessions on this machine and of their
    subagents: `input`, `output`, `cache_read`, `cache_write`; `sessions` and
    `subagents`, how many files of each were read; `missing`, the transcripts the log
    names that are gone; `unread`, the lines that did not read; and `covers`, what the
    number holds and leaves out. None when no transcript the log names counts for the
    task (`transcripts_of`)."""
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
    gone = (
        (
            f"; {counts['missing']} transcript{'s' if counts['missing'] != 1 else ''} "
            f"the log names {'are' if counts['missing'] != 1 else 'is'} gone"
        )
        if counts["missing"]
        else ""
    )
    covers = (
        f"the Claude Code sessions of the task on this machine ({counts['sessions']}) "
        f"and their subagents ({counts['subagents']}){gone}; a Codex reviewer, an "
        "expert of another provider and a session on another machine are not in it"
    )
    return {**sums, **counts, "covers": covers}
