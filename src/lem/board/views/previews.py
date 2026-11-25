"""Read the bodies a page shows and keep the other files as metadata."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.board.views import folder
from lem.board.views.artifacts import listing, pictures, spots
from lem.board.views.artifacts.tab import first_of
from lem.board.views.criteria.asking import fast
from lem.board.views.panel import review, stopped
from lem.model.criteria import waits

if TYPE_CHECKING:
    from pathlib import Path

    from lem.board.inputs.layout import Viewer
    from lem.board.views.artifacts.mapped import Entry
    from lem.board.views.world import Seen


def read(seen: Seen, viewer: Viewer, where: Path, worktree: Path) -> Seen:
    """Read only this page's previews, including a selected plan from its worktree."""
    names = names_of(seen, viewer)
    plan = seen.plan_file
    if (
        plan is not None
        and viewer.task == seen.record.task.slug
        and viewer.tab == "artifacts"
    ):
        entry = picked(seen, viewer.path)
        if entry is not None and entry.first:
            plan = replace(plan, text=folder.text_of(worktree, plan.stat.path))
    return replace(seen, prose=folder.prose_of(where, names), plan_file=plan)


def names_of(seen: Seen, viewer: Viewer) -> tuple[str, ...]:
    """The task folder's files this page uses, in their folder's order."""
    task = seen.record.task
    panel = viewer.task == task.slug
    names: set[str] = set()
    inline = viewer.view == "waits" and viewer.may_act and fast(task)
    if waits.hold_of(task) is not None and (
        inline or (panel and viewer.tab == "criteria")
    ):
        names.add(spots.CRITERIA_DOC)
    if panel and viewer.tab == "overview":
        names.update(overview(seen))
    if panel and viewer.tab == "artifacts":
        names.update(artifacts(seen, viewer.path))
    return tuple(name for name in seen.files if name in names)


def overview(seen: Seen) -> tuple[str, ...]:
    """The task outcome, its open merge review and its breaker's document."""
    task = seen.record.task
    breaker = stopped.stopped(task)
    names = ["task.md"]
    if task.status == "open":
        names.append(review.NAME)
    if breaker is not None:
        names.append(breaker.document or "breaker.md")
    return tuple(names)


def picked(seen: Seen, path: str | None) -> Entry | None:
    """The preview the Artifacts tab selects from the file list."""
    entries = listing.entries_of(seen)
    chosen = next((one for one in entries if one.path == path), None)
    return chosen or first_of(listing.map_of(seen), entries)


def artifacts(seen: Seen, path: str | None) -> tuple[str, ...]:
    """The selected preview and the documents needed to place media in the map."""
    selected = picked(seen, path)
    names = [selected.path] if selected is not None and not selected.first else []
    if any(name.startswith(spots.MEDIA_FOLDER) for name in seen.files):
        names.extend(
            entry.path for entry in listing.entries_of(seen) if pictures.read(entry)
        )
    return tuple(names)
