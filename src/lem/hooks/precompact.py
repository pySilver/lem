"""A task's compaction: the summary's form before it, and the task's record and handoff after.

Claude Code takes a PreCompact hook's output as the instructions of the summary, and a
SessionStart hook's for the source `compact` as context after it (its hooks reference, read
2026-11-21). The summary is the handoff, under its five headings; after it the session reads its
task's status, hold and newest state line from `task.json`, and `handoff.md` as it is. Both read
whole files and wait on no lock: `task.json` is written whole, by a rename.
"""

from lem.hooks import raw, where

TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Mapping

# The line of `session.md` that names the phase its session opened in (`app.sessions.brief`).
PHASE = "phase: "
TRUTH = (
    "The task's record is the truth; where handoff.md is older than the record, follow the "
    "record."
)


def answer(environ: Mapping[str, str], behind: str | None) -> str:
    """The summary's instructions for a task's session; nothing for another session, or for an
    input that is no PreCompact event."""
    found = raw.event()
    if raw.text(found, "hook_event_name") != "PreCompact":
        return ""
    folder = where.task_folder(found, environ)
    if folder is None:
        return ""
    slug = folder.rpartition("/")[2]
    return instructions(slug, phase_in(folder))


def phase_in(folder: str) -> str | None:
    """The phase the task's newest session opened in, from its `session.md`."""
    try:
        brief = raw.read_bytes(f"{folder}/session.md").decode(errors="replace")
    except OSError:
        return None
    named = (line for line in brief.splitlines() if line.startswith(PHASE))
    return next((line.removeprefix(PHASE).strip() for line in named), None)


def instructions(slug: str, phase: str | None) -> str:
    """The summary's form, the handoff's."""
    of = f"task {slug}, phase {phase}" if phase else f"task {slug}"
    return (
        f"This summary is the handoff of {of}, under five headings: Settled; Open; Next "
        "step; Failed; Changed files, each path with its status. Link a plan, a record or a "
        "commit by path or id; copy none of their text.\n"
    )


def restored(folder: str) -> str:
    """What a task's session reads after its compaction: its record's newest state, then
    `handoff.md` as it is."""
    slug = folder.rpartition("/")[2]
    try:
        handoff = raw.read_bytes(f"{folder}/handoff.md").decode(errors="replace")
    except OSError:
        handoff = "none in the task's folder"
    return "\n".join(
        (
            f"Lem's task {slug}, after the compaction. {TRUTH}",
            "",
            f"## The task now (`lem task show {slug}` gives the whole record)",
            "",
            newest_state(folder),
            "",
            "## handoff.md",
            "",
            handoff.strip(),
            "",
        )
    )


def newest_state(folder: str) -> str:
    """The task's status, its hold, and its newest state line, from `task.json`."""
    import json

    try:
        record = json.loads(raw.read_bytes(f"{folder}/task.json"))
    except OSError, ValueError:
        return "the task's record does not read"
    task = record.get("task") if isinstance(record, dict) else None
    if not isinstance(task, dict):
        return "the task's record holds no task"
    status = task.get("status")
    hold = kind_of(task.get("hold")) or "none"
    line = newest_line(record.get("journal"))
    return f"status: {status}; hold: {hold}; newest state line: {line}"


def kind_of(entry: object) -> object:
    """The `kind` of a record's union member, or None for anything else."""
    return entry.get("kind") if isinstance(entry, dict) else None


def newest_line(journal: object) -> str:
    """The line of the newest state entry of the journal `journal`."""
    entries = journal if isinstance(journal, list) else []
    lines = [entry.get("line") for entry in entries if kind_of(entry) == "state"]
    written = [line for line in lines if isinstance(line, str)]
    return written[-1] if written else "none written yet"
