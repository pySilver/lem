"""Jev's read of whether a finding is the same defect as each item of the backlog at the tip
(`land.ask_alike` and `land.check_alike` on `main`), through the `Judge` port.

Every item is asked, each that no earlier run asked about; the items go to the port by their
paths in the worktree, which the adapter reads. With `jev.findings = false` in the team's
settings nothing is sent.
"""

from typing import TYPE_CHECKING

from lem.app.landing import jev_kept, review_settings
from lem.model.landing import alike
from lem.model.landing.items import Defect
from lem.ports import judge as port

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
    judge: port.Judge,
    worktree: Path,
    defect: Defect,
    shelved: Shelved,
    known: jev_kept.Scores,
) -> jev_kept.Scores | port.NotAsked:
    """The score of each item for the defect: those `known` kept, and Jev's for the rest;
    None for an item Jev gave no score. The port reads each item by its path on disk."""
    named = {
        str(worktree / one.path): one.path for one in shelved if one.path not in known
    }
    if not named:
        return known
    told = port.Defect(where=defect.where, title=defect.title, what=defect.what)
    said = judge.same_items(told, tuple(named))
    if isinstance(said, port.NotAsked):
        return said
    return {**known, **scores_of(said, named)}


def scores_of(said: Said, named: dict[str, str]) -> jev_kept.Scores:
    """Jev's score of each item asked, by its path in the repository; None for an item it
    gave no score."""
    fresh: jev_kept.Scores = dict.fromkeys(named.values())
    for one in said:
        relative = named.get(one.path or "")
        if relative:
            fresh[relative] = one.score
    return fresh


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
    said = asked(context.ports.judge, context.worktree, defect, shelf.shelved, known)
    if isinstance(said, port.NotAsked):
        return ""
    kept.alike[key] = said
    found = alike.named(scored(said), shelf.shelved)
    return alike.line_of(finding.id, finding.title, found) if found else ""


def checked(
    context: Context, asks: tuple[Finding, ...], shelf: Shelf
) -> Refusal | None:
    """`file`'s look before it writes anything: each defect about to get a file of its own
    against every item at the tip. The refusal names each defect Jev reads as one an item
    holds."""
    if not asks or not shelf.shelved:
        return None
    if not review_settings.read(context.workspace.checkout).jev.findings:
        return None
    kept = jev_kept.read(context.folder)
    lines = [found_for(context, one, shelf, kept) for one in asks]
    jev_kept.write(context.folder, kept)
    named = tuple(line for line in lines if line)
    first = named[0].split(" ", 1)[0] if named else ""
    return alike.refused(named, first, context.record.task.slug)
