"""The plugin's two hooks of a task's session (`lem session open`): the form of a compaction's
summary, the task's files put back after it, and the record of each Claude Code session of the task.

    PreCompact (auto|manual)    prints the summary's instructions: the handoff's five headings
    SessionStart (compact)      prints the task's newest state block word for word, then handoff.md
                                with its time
    SessionStart (any source)   logs `session.transcript` in the task's event log, once for each
                                Claude Code session and agterm session: its id (`claude`), the path
                                of its transcript (`transcript`) and the source, as the hook's input
                                names them (`session_id`, `transcript_path`, `source`: the hooks
                                reference, read 2026-11-21), and the agterm session it runs in
                                (`session`, from `AGTERM_SESSION_ID`, which agterm sets in each
                                pane's environment; null outside agterm); it prints nothing for a
                                start, a resume, a clear or a fork

A task's session has `LEM_TASK=SLUG` in its environment, which `lem session open` puts into the
launch line. Without it, or without the task's directory in the state folder of the repository the
session runs in, the hook prints nothing and exits 0: a session that is no task's is no business of
Lem's. Claude Code takes a PreCompact hook's output as the instructions of the summary, and a
SessionStart hook's for the source `compact` as context after it (its hooks reference, read for the
shape of task 4, 2026-11-21). The record is one line appended to `events.jsonl`, in the form `lem project
log` writes, under the log's lock (`lem_state.events_lock`), as every writer of the log appends. It exits
0 whatever happens, a failure too.

The record says what the hook saw, not whose transcript it is. Its `task` and its `session` are the
hook's environment's, `LEM_TASK` and `AGTERM_SESSION_ID`, and Claude Code's background host keeps the
environment of the pane that started it: a fork that another task's session makes in that host is
logged under the first pane's task (6fe214ec, a fork of the session of merge-leaves-board-lock,
logged under board-card-search on 2026-11-22). The hook cannot tell: its input names no parent
session. No hook reads a transcript. The readers, `lem_tokens` and `lem_signs`, take a transcript's
task from its first prompt, the launch line of the task's session, and the record's `task` only when
that prompt names no task (`lem_tokens`).

The plugin starts it through `lem_python.py` beside this file, as the other hooks.
"""

import os
import sys

# How long git may take to name the main checkout. A guess: it answers in milliseconds, and a stuck
# git must not hold the hook.
GIT_TIMEOUT = 2
# a task's slug, as project.py's SLUG
SLUG = r"[a-z0-9]+(?:-[a-z0-9]+)*"
TRUTH = "The task's state is the truth; where handoff.md is older than the state, follow the state."


def instructions(slug: str, phase: str | None) -> str:
    """What a PreCompact hook prints: the summary's form, the handoff's."""
    of = f"task {slug}, phase {phase}" if phase else f"task {slug}"
    return (f"This summary is the handoff of {of}, under five headings: Settled; Open; Next step; Failed; "
            "Changed files, each path with its status. Link a plan, a record or a commit by path or id; copy none of their text.")


def restored(slug: str, block: str | None, handoff: str | None, written: str | None) -> str:
    """What a SessionStart hook prints after a compaction: the newest state block word for word, then
    handoff.md with its time, under the rule that the state wins."""
    lines = [f"Lem's task {slug}, after the compaction. {TRUTH}", "", "## The newest state block (state.md)", "", block.strip() if block else "none written yet", ""]
    if handoff is not None:
        lines += [f"## handoff.md, written {written}", "", handoff.strip(), ""]
    else:
        lines += ["## handoff.md", "", "none in the task directory", ""]
    return "\n".join(lines)


def newest_phase(log, slug: str) -> str | None:
    """The phase of the task's newest `session.open` in the event log, the lines of LOG."""
    import json
    phase = None
    for line in log:
        if f'"{slug}"' not in line or '"session.open"' not in line:
            continue
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if record.get("event") == "session.open" and record.get("task") == slug:
            phase = record.get("phase")
    return phase


def transcript_record(log, slug: str, claude: str, session: str | None) -> bool:
    """Whether the event log, the lines of LOG, already holds this Claude Code session of the task in
    this agterm session: a background host of Claude Code that runs with another pane's environment
    logs the same Claude id under another `session` (`lem_signs`). A record's `task` and `session` are
    the hook's environment's, which that host keeps from the pane that started it, so a record may
    name a transcript of another task; the readers take a transcript's task from its first prompt
    (`lem_tokens`)."""
    import json
    for line in log:
        if f'"{slug}"' not in line or '"session.transcript"' not in line:
            continue
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if record.get("task") == slug and record.get("claude") == claude and record.get("session") == session:
            return True
    return False


def keep_transcript(state, slug: str, event: dict, session: str | None = None) -> None:
    """Log the task's Claude Code session, its id and its transcript's path from the hook's input, and
    SESSION, the agterm session the hook runs in, once for each Claude id and agterm session."""
    import json
    from datetime import datetime, timezone
    claude, transcript = event.get("session_id"), event.get("transcript_path")
    if not (isinstance(claude, str) and claude and isinstance(transcript, str) and transcript):
        return
    import lem_state
    log = state / lem_state.EVENTS
    # under the log's lock, as `lem project log` appends: a prune that rewrites the log either comes
    # after this record or put its new file in place before the read
    with lem_state.events_lock(state):
        with (log.open(encoding="utf-8", errors="replace") if log.is_file() else open(os.devnull)) as lines:
            if transcript_record(lines, slug, claude, session):
                return
        record = {"ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "event": "session.transcript", "task": slug,
                  "claude": claude, "transcript": transcript, "source": str(event.get("source") or ""), "session": session}
        with log.open("a", encoding="utf-8") as out:
            out.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> None:
    import json
    import os
    import re
    from datetime import datetime, timezone
    from pathlib import Path

    slug = os.environ.get("LEM_TASK", "").strip()
    if not re.fullmatch(SLUG, slug):
        return
    here = Path(__file__).resolve().parent
    sys.path.insert(0, str(here))
    import lem_state

    try:
        event = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        event = {}
    if not isinstance(event, dict):
        return
    folder = event.get("cwd") if isinstance(event.get("cwd"), str) else None
    folder = folder or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    try:
        state = lem_state.main_checkout(Path(folder), timeout=GIT_TIMEOUT) / lem_state.STATE
    except lem_state.StateError:
        return
    directory = state / "tasks" / slug
    if not directory.is_dir():
        return
    name = event.get("hook_event_name")
    if name == "PreCompact":
        log = state / "events.jsonl"
        with (log.open(encoding="utf-8", errors="replace") if log.is_file() else open(os.devnull)) as lines:
            print(instructions(slug, newest_phase(lines, slug)))
    elif name == "SessionStart":
        keep_transcript(state, slug, event, os.environ.get("AGTERM_SESSION_ID", "").strip() or None)
    if name == "SessionStart" and event.get("source") == "compact":
        written = (directory / "state.md").read_text(encoding="utf-8", errors="replace") if (directory / "state.md").is_file() else ""
        block = written.strip().split("\n\n")[0] if written.strip() else None
        handoff = directory / "handoff.md"
        text = handoff.read_text(encoding="utf-8", errors="replace") if handoff.is_file() else None
        when = datetime.fromtimestamp(handoff.stat().st_mtime, timezone.utc).strftime("%Y-%m-%dT%H:%MZ") if text is not None else None
        print(restored(slug, block, text, when))


if __name__ == "__main__":
    try:
        main()
    except BaseException:  # noqa: BLE001 - a hook that fails must not fail the session
        pass
    sys.exit(0)
