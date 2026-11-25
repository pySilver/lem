"""Where `--record` looks for the review agent's answer and which files are archived."""

import os
import re
from functools import partial
from pathlib import Path

from lem.kernel.errors import Refusal

LANDING = re.compile(r"landing-\d+")
MOVING = re.compile(r"\.landing-\d+\.moving")
WHERE = "--record names a file by its path, or by its path inside the task's folder"


def task_file(given: str, directory: Path) -> Path:
    """The file `--record` names: from the working directory (or absolute), else a relative
    path in the task's folder `directory`. Refused with each place it looked."""
    path = Path(given)
    first = path if path.is_absolute() else Path.cwd() / path
    if first.is_file():
        return first
    if path.is_absolute():
        raise Refusal("record-file", f"{given} is not a file", WHERE)
    second = directory / path
    if second.is_file():
        return second
    looked = f"the working directory ({first}) nor in the task's folder ({second})"
    raise Refusal("record-file", f"{given} is a file neither in {looked}", WHERE)


def kept_folder(name: str, slug: str) -> bool:
    """Whether a folder of `reviews/` keeps the reviews of a landing before: `landing-N`
    (not the review tool's own folder of a task named so), or the hidden folder a move of
    them fills."""
    landing = LANDING.fullmatch(name) is not None and name != slug
    return landing or MOVING.fullmatch(name) is not None


def kept_in(look: tuple[Path, Path], slug: str) -> str | None:
    """The folder of a landing before under the look's root that holds its path, or None."""
    root, path = look
    parts = path.relative_to(root).parts if path.is_relative_to(root) else ()
    if len(parts) > 1 and kept_folder(parts[0], slug):
        return parts[0]
    return None


def looks_of(reviews: Path, record: Path) -> tuple[tuple[Path, Path], ...]:
    """The record under the reviews' folder as named, and with its links resolved."""
    named = Path(os.path.normpath(reviews.absolute()))
    given = Path(os.path.normpath(record.absolute()))
    return ((named, given), (reviews.resolve(), record.resolve()))


def landing_before(folder: Path, record: Path, slug: str) -> Refusal | None:
    """The refusal of a record kept in the folder of a landing before, whatever its attempt
    and tip say, looked for as named and with its links resolved (`land.landing_before` on
    `main`): after a restart at the same tip its attempt is due again."""
    reviews = folder / "reviews"
    looks = map(partial(kept_in, slug=slug), looks_of(reviews, record))
    kept = next(filter(None, looks), None)
    if kept is None:
        return None
    where = reviews / kept
    return Refusal(
        "landing-before",
        f"{record} is a review of a landing before, kept in {where}: it records nothing of "
        "this landing",
        f"lem land read {slug} says the review that is due, and --record names the file of "
        "that review",
    )
