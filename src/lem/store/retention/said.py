"""The owner's line of one run of retention, and the server's log line of its hourly run
(`project.cmd_prune` and `serve.prune_line` on `main`)."""

from typing import TYPE_CHECKING

from lem.kernel import clock

if TYPE_CHECKING:
    from lem.store.retention.files import Failed, Skipped
    from lem.store.retention.run import Pruned

# Bytes in a decimal megabyte, as the line shows them.
MEGABYTE = 1_000_000


def said(run: Pruned) -> str:
    """What the run did, or would do."""
    verb = "would remove" if run.dry_run else "removed"
    replace = "would replace" if run.dry_run else "replaced"
    day = clock.minute(run.before)[:10]
    size = run.bytes / MEGABYTE
    return (
        f"{verb} {run.files} files of {len(run.tasks)} ended tasks with nothing new since "
        f"{day}, so that each keeps only its small record (its record, its sessions, its "
        f"request and the aside of a park), {replace} the {run.entries} journal entries of "
        f"{len(run.summarized)} such tasks with one summary each, and {verb} "
        f"{len(run.folders)} old folders and copies, {size:.1f} MB"
    )


def quiet(run: Pruned) -> bool:
    """Whether the run removed, folded, skipped and failed nothing: the server logs no line
    for it. A file removed counts when it was empty too."""
    counts = (run.files, run.bytes, run.entries)
    lists = (run.folders, run.skipped, run.failed)
    return not any(counts) and not any(lists)


def logged(run: Pruned) -> str:
    """The server's log line of a run that did something: what it did, then each skip and
    each failure."""
    parts = [f"lem prune: {said(run)}"]
    parts.extend(map(skipped_line, run.skipped))
    parts.extend(map(failed_line, run.failed))
    return "; ".join(parts)


def skipped_line(skipped: Skipped) -> str:
    """One path that stayed, and why."""
    return f"skipped {skipped.path}: {skipped.why}"


def failed_line(failed: Failed) -> str:
    """One removal that failed, and the error."""
    return f"failed {failed.path}: {failed.error}"
