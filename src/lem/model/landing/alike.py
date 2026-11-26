"""Jev's read of whether a finding is the same defect as an item of the backlog
(`land.alike_named` and `land.check_alike` on `main`): the items it names, and what `file`
refuses when it names one for a defect about to get a file of its own.

A finding is kept by a digest of its `where`, title and run (`land.finding_key`), so that two
runs of one place and title are two findings, and Jev is never asked twice about one: a text
read twice moved by up to 0.11 (jev-advice.md of task backlog-refuted-items-and-jev,
2026-11-23), so a second ask could name an item the first did not.
"""

import hashlib

import msgspec

from lem.kernel.errors import Refusal
from lem.model.landing.items import BacklogItem, Defect, paragraphs
from lem.records.base import Frozen

# The score at or over which an item is named to the agent: a guess (2026-11-23), so that a weak
# match never reaches the agent's three, not measured on findings, of which no labeled sample
# exists (`SAME_AT` on `main`).
SAME_AT = 0.5
# The most items named for one finding: the agent reads each (criterion 8 of task
# backlog-refuted-items-and-jev, 2026-11-23).
ALIKE_MOST = 3
# The characters kept in a finding's digest.
KEY_LENGTH = 16


class Alike(Frozen, frozen=True, kw_only=True):
    """An item Jev reads as the same defect: its path, title, `where`, `worth`, and score."""

    path: str
    title: str
    where: str | None = None
    worth: str | None = None
    score: float
    jev: str


def key_of(defect: Defect) -> str:
    """The digest Jev's read of a finding is kept by: its `where`, its title and its run."""
    run = "\n\n".join(paragraphs(defect.what))
    told = (defect.where.strip(), defect.title.strip(), run)
    return hashlib.sha256(msgspec.json.encode(told)).hexdigest()[:KEY_LENGTH]


def alike_of(found: BacklogItem, score: float) -> Alike:
    """An item with Jev's score."""
    return Alike(
        path=found.path,
        title=found.title,
        where=found.where,
        worth=found.worth,
        score=score,
        jev=f"Jev: {score:.2f}",
    )


def named(
    scores: dict[str, float], shelved: tuple[BacklogItem, ...]
) -> tuple[Alike, ...]:
    """The items whose score is at or over `SAME_AT`, the highest first, `ALIKE_MOST` at
    most."""
    over = [
        alike_of(found, scores[found.path]) for found in shelved if found.path in scores
    ]
    kept = [one for one in over if one.score >= SAME_AT]
    kept.sort(key=lambda one: (-one.score, one.path))
    return tuple(kept[:ALIKE_MOST])


def told(one: Alike) -> str:
    """An item Jev named, as `file`'s refusal names it."""
    worth = one.worth or "none"
    return f'`{one.path}` "{one.title}" ({one.jev}, worth: {worth})'


def line_of(number: str, title: str, found: tuple[Alike, ...]) -> str:
    """One defect of `file`'s refusal, with the items Jev named for it."""
    named_items = ", ".join(map(told, found))
    return f'{number} "{title}": {named_items}'


def refused(lines: tuple[str, ...], slug: str) -> Refusal | None:
    """`file`'s refusal when Jev names an item for a defect about to get a file of its own:
    nothing is written, and the next run says for each `--same` or `--new`."""
    if not lines:
        return None
    listed = "; ".join(lines)
    first = lines[0].partition(" ")[0]
    return Refusal(
        "jev-same",
        f"{len(lines)} defect(s) to file may be one an item of the backlog holds already, by "
        f"Jev's read at {SAME_AT} or more: {listed}. Nothing is written",
        f"read each item named, then run lem land file {slug} again with, for each defect "
        f"named, --same {first}=PATH when that item holds the defect, or --new {first} when it "
        "is a defect of its own",
    )
