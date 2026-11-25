"""The rest of a task's folder on the map: a page at its top, the pictures, the ladder's notes,
and every file the map does not know, in its folder among the working files; and the one rule
that places any path."""

from lem.board.views.artifacts import named, reviewed
from lem.board.views.artifacts.spots import MEDIA_FOLDER, PR, WORK, Spot, known

PAGES = frozenset(("html", "htm"))
LADDER = "ladder/"


def page(path: str) -> Spot | None:
    """An HTML page at the top of the folder: a document of the pull request."""
    suffix = path.rpartition(".")[2].lower()
    if "/" in path or suffix not in PAGES:
        return None
    return Spot(group=PR, title=path)


def folder(path: str) -> Spot | None:
    """A picture of `media/` or a note of the ladder, among the working files."""
    for prefix, name in ((MEDIA_FOLDER, "Pictures"), (LADDER, "The ladder's notes")):
        if path.startswith(prefix):
            return Spot(
                group=WORK, title=path.removeprefix(prefix), role="work", folder=name
            )
    return None


def loose(path: str) -> Spot:
    """A file the map does not know: a working file in its own folder, or at the top."""
    parent, _, name = path.rpartition("/")
    return Spot(
        group=WORK, title=name if parent else path, role="work", folder=parent or None
    )


RULES = (
    named.brief,
    named.breaker,
    named.report,
    named.gate,
    named.red,
    reviewed.review,
    reviewed.archive,
    reviewed.run,
    page,
    folder,
)


def place(path: str) -> Spot:
    """Where the file at `path` of the task's folder goes on the map."""
    found = known(path)
    if found is not None:
        return found
    placed = (rule(path) for rule in RULES)
    found = next((spot for spot in placed if spot is not None), None)
    return found or loose(path)
