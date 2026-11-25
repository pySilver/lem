"""Move the previous landing's review files aside before an attempt can start again."""

from typing import TYPE_CHECKING

from lem.app.landing import review_files
from lem.kernel.errors import Refusal
from lem.model.task.ending import START_OVER
from lem.records.journal.task import StateNoted

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.record import Record


def pending(record: Record) -> bool:
    """Whether the last status change asks to start the landing over."""
    if record.task.status != "ready":
        return False
    moves = (entry for entry in reversed(record.journal) if boundary(entry))
    last = next(moves, None)
    if not isinstance(last, StateNoted):
        return False
    line = last.line or ""
    return line.startswith(f"{START_OVER}:")


def destination(reviews: Path, slug: str) -> str:
    """The next archive name, skipping the name of the review tool's own folder."""
    numbers = [
        int(entry.name.split("-")[1])
        for entry in reviews.iterdir()
        if review_files.LANDING.fullmatch(entry.name)
    ]
    number = max(numbers, default=0) + 1
    name = f"landing-{number}"
    after = number + 1
    return f"landing-{after}" if name == slug else name


def staged(reviews: Path, slug: str) -> Path:
    """The staging folder of an interrupted move, or the next folder to use."""
    found = [
        entry
        for entry in reviews.iterdir()
        if review_files.MOVING.fullmatch(entry.name)
    ]
    if not found:
        target = destination(reviews, slug)
        return reviews / f".{target}.moving"
    folder = found[0]
    if len(found) != 1 or folder.is_symlink() or not folder.is_dir():
        raise OSError("the review archive has an invalid staging folder")
    if completed(folder).exists():
        raise OSError("the staging folder and its review archive both exist")
    return folder


def completed(folder: Path) -> Path:
    """The archive's name once all the files are in the staging folder."""
    return folder.with_name(folder.name.removeprefix(".").removesuffix(".moving"))


def archive(reviews: Path, slug: str) -> None:
    """Archive the active entries, including those already staged by an interrupted move."""
    if not reviews.is_dir():
        return
    folder = staged(reviews, slug)
    entries = [
        entry
        for entry in reviews.iterdir()
        if entry.name != ".DS_Store" and not review_files.kept_folder(entry.name, slug)
    ]
    if not entries and not folder.is_dir():
        return
    folder.mkdir(exist_ok=True)
    for entry in entries:
        target = folder / entry.name
        if target.exists() or target.is_symlink():
            raise OSError(f"both the active and staged review contain {entry.name}")
    for entry in entries:
        entry.rename(folder / entry.name)
    folder.rename(completed(folder))


def before_start(record: Record, folder: Path) -> None:
    """Finish the archive under the step lock before the start changes the task's status."""
    if not pending(record):
        return
    slug = record.task.slug
    try:
        archive(folder / "reviews", slug)
    except OSError as error:
        raise Refusal(
            "review-archive",
            f"the previous landing's reviews could not move into their archive: {error}",
            f"the owner puts the reviews folder right, then runs lem land start {slug} again",
        ) from error


def boundary(entry: object) -> bool:
    """A start-over request or the start that consumes it."""
    if not isinstance(entry, StateNoted):
        return False
    line = entry.line or ""
    return entry.status == "landing" or line.startswith(f"{START_OVER}:")
