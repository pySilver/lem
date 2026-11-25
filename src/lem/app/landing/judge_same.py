"""Jev's read of whether a finding is the same defect as each item of the backlog at the tip
(`land.ask_alike` and `land.check_alike` on `main`), through the `Judge` port.

Every item is asked, each that no earlier run asked about, as the tip's commit has it (its
title, `where` and first line), never as a builder's edit in the worktree has it
(`land.cmd_alike` reads HEAD on `main`). With `jev.findings = false` in the team's settings
nothing is sent.
"""

from typing import TYPE_CHECKING

from lem.app.landing import jev_kept
from lem.model.landing import alike
from lem.model.landing.items import Defect
from lem.ports import judge as port
from lem.settings.load import team_of

if TYPE_CHECKING:
    from pathlib import Path

    from lem.app.landing.frame import Context
    from lem.kernel.errors import Refusal
    from lem.model.landing.filing_place import Shelf
    from lem.model.landing.items import BacklogItem
    from lem.records.landing.review import Finding

type Shelved = tuple[BacklogItem, ...]
type Said = tuple[port.Score, ...]


def asked(
    judge: port.Judge, defect: Defect, shelved: Shelved, known: jev_kept.Scores
) -> jev_kept.Scores | port.NotAsked:
    """The score of each item for the defect: those `known` kept, and Jev's for the rest;
    None for an item Jev gave no score."""
    fresh = tuple(one for one in shelved if one.path not in known)
    if not fresh:
        return known
    told = port.Defect(where=defect.where, title=defect.title, what=defect.what)
    said = judge.same_items(told, tuple(map(candidate_of, fresh)))
    if isinstance(said, port.NotAsked):
        return said
    return {**known, **scores_of(said, fresh)}


def candidate_of(one: BacklogItem) -> port.Candidate:
    """An item of the backlog as Jev reads it: as the tip's commit holds it."""
    return port.Candidate(
        path=one.path, title=one.title, where=one.where, first=one.first
    )


def scores_of(said: Said, fresh: Shelved) -> jev_kept.Scores:
    """Jev's score of each item asked, by its path in the repository; None for an item it
    gave no score."""
    found: jev_kept.Scores = dict.fromkeys(one.path for one in fresh)
    scored = {one.path: one.score for one in said if one.path in found}
    return {**found, **scored}


def scored(scores: jev_kept.Scores) -> dict[str, float]:
    """The items Jev gave a score."""
    return {path: score for path, score in scores.items() if score is not None}


def found_for(
    context: Context, finding: Finding, shelf: Shelf, kept: jev_kept.Kept
) -> str:
    """The line of `file`'s refusal for one defect whose items Jev names, empty when it names
    none; the scores are kept either way."""
    defect = Defect(where=finding.where, title=finding.title, what=finding.what)
    key = alike.key_of(defect)
    known = kept.alike.get(key, {})
    said = asked(context.ports.judge, defect, shelf.shelved, known)
    if isinstance(said, port.NotAsked):
        return ""
    kept.alike[key] = said
    found = alike.named(scored(said), shelf.shelved)
    return alike.line_of(finding.id, finding.title, found) if found else ""


def sends(checkout: Path) -> bool:
    """Whether the team sends a finding's text to Jev: `jev.findings` of the base's settings
    file (`settings.load.team_of`)."""
    return team_of(checkout).jev.findings


def checked(
    context: Context, asks: tuple[Finding, ...], shelf: Shelf
) -> Refusal | None:
    """`file`'s look before it writes anything: each defect about to get a file of its own
    against every item at the tip. The refusal names each defect Jev reads as one an item
    holds."""
    if not asks or not shelf.shelved:
        return None
    if not sends(context.workspace.checkout):
        return None
    kept = jev_kept.read(context.folder)
    lines = [found_for(context, one, shelf, kept) for one in asks]
    jev_kept.write(context.folder, kept)
    named = tuple(line for line in lines if line)
    first = named[0].split(" ", 1)[0] if named else ""
    return alike.refused(named, first, context.record.task.slug)
