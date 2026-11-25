"""The line the board shows of the end of a merge the server made (`NOTES` of
`serve.merge_in_thread` on `main`): merged, or why not with the way on; and, when the owner's
merge still stands after a refusal (the base moved again), that it stands for the tip he saw,
so that a press of his starts nothing new."""

from typing import TYPE_CHECKING

import msgspec

from lem.kernel.errors import Refusal
from lem.model.landing import merge_standing
from lem.store import tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.kernel.envelope import Envelope
    from lem.kernel.errors import Fault

MERGED = (
    "Merged: {slug} is on the base. Within a minute the board's server wakes the task's "
    "session, or opens one, which removes its worktree."
)


def completed(slug: str, outcome: Envelope) -> str:
    """Say what the forge did: a merge, a place in the queue, or another end."""
    found = msgspec.json.decode(outcome.outcome) if outcome.outcome else {}
    if isinstance(found, dict) and "commit" in found:
        return MERGED.format(slug=slug)
    if isinstance(found, dict) and "queued" in found:
        queue = found["queued"]
        return f"Queued: GitHub accepted the merge of {slug} in {queue}."
    return f"Lem recorded the result of the merge call for {slug}."


def refused(state: Path, slug: str, error: Refusal | Fault) -> str:
    """The line of a merge that did not go: its why, the way on, and whether the owner's merge
    still stands."""
    why = said_of(error)
    if isinstance(error, Refusal) and error.code == "github":
        return f"The merge did not go: {why}"
    standing = merge_standing.standing_of(tasks.read(state, slug))
    if standing is None:
        return f"The merge did not go: {why}"
    tip = standing.tip
    return f"The owner's merge still stands for {tip}, and Lem merges it when it may: {why}"


def said_of(error: Refusal | Fault) -> str:
    """A refusal's why and its way on, or a fault's line."""
    if isinstance(error, Refusal):
        return f"{error.why}; {error.fix}"
    return str(error)
