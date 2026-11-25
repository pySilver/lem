"""The feed's words of a landing's entries: a review round, the careful call the review made, a
proposal that is not green, and a wait of the checks or of the merge (`review`, `careful.missed`,
`proposed`, `gate.wait` and `merge.wait` of `main`'s `SAYS`)."""

from typing import TYPE_CHECKING

from lem.board.views import rounds
from lem.board.views.activity.told import ALERT, BAD, CLOCK, DONE, EYE, QUIET, YOU, Told
from lem.board.views.telling import BEHIND

if TYPE_CHECKING:
    from lem.records.journal.landing import (
        CarefulMissed,
        CheckWait,
        MergeWait,
        NotGreen,
        ReviewRound,
    )


def review(entry: ReviewRound) -> Told:
    """A review round: its kind, its verdict and its counts."""
    look = DONE if rounds.verdict(entry.review) == "clean" else BAD
    return Told(look, EYE, "Review", rounds.line(entry.review))


def careful(entry: CarefulMissed) -> Told:
    """A review of the fast track that made the careful call the shape missed."""
    said = f"round {entry.round}: {entry.why}"
    return Told(BAD, ALERT, "Careful by the review, not by the plan", said)


def not_green(entry: NotGreen) -> Told:
    """A proposal that is not green, with its reasons."""
    reasons = " · ".join(entry.reasons)
    return Told(YOU, ALERT, "Proposed: not green", reasons)


def check_wait(entry: CheckWait) -> Told:
    """A wait of the checks: behind another run, a minute after one, or for the load."""
    return Told(QUIET, CLOCK, "The checks wait", waits_for(entry))


def waits_for(entry: CheckWait) -> str:
    """What the checks wait for, in the words after "The checks wait"."""
    if entry.behind:
        repo = (entry.behind_repo or "").rpartition("/")[2]
        name = f"{entry.behind} of {repo}" if repo else entry.behind
        why = BEHIND[entry.why or "first"]
        return f"behind {name}, {why}"
    if entry.after:
        return f"a minute after the checks of {entry.after} started"
    return f"for the load: {entry.load}, they start below {entry.start_below}"


def merge_wait(entry: MergeWait) -> Told:
    """A merge that waits for another task's merge."""
    behind = entry.behind or "another task"
    said = f"for the merge of {behind}"
    return Told(QUIET, CLOCK, "The merge call waits", said)
