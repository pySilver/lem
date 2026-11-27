"""How a sync of a feature ends when its merge is made: the checks red or stopped, origin's
branch moved again and again under the push, and the line for the owner of a sync that ran.
"""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from lem.model.task.sync_stops import Place
    from lem.records.landing.checks import Outcome


def red(place: Place, outcomes: tuple[Outcome, ...]) -> Refusal:
    """A command of the checks failed on the merge: the commands and their output."""
    failed = (one for one in outcomes if not one.passed)
    shown = "; ".join(map(output_of, failed))
    return Refusal(
        "red",
        f"the checks failed on the merge in {place.branch}: {shown}, in the folder that "
        f"lem task dir {place.slug} names; the merge stays in the worktree, and nothing "
        "was pushed",
        f"a builder repairs it in {place.worktree} and commits, {place.again}",
    )


def stopped(place: Place) -> Refusal:
    """The checks were stopped before their end."""
    return Refusal(
        "stopped",
        f"the checks of the merge in {place.branch} were stopped; the merge stays in the "
        "worktree, and nothing was pushed",
        f"run lem task sync {place.slug} again",
    )


def moved(place: Place, tries: int) -> Refusal:
    """Origin's branch moved under each push of the sync."""
    return Refusal(
        "lease",
        f"origin's {place.branch} moved under each of {tries} pushes of the sync, as parts "
        "merged into it; nothing was pushed",
        f"run lem task sync {place.slug} again",
    )


def unfetched(place: Place, said: str) -> Refusal:
    """Origin was not fetched, so the sync cannot see its base or its branch."""
    return Refusal(
        "fetch",
        f"the sync of {place.slug} needs origin as it is now: {said}",
        f"run lem task sync {place.slug} again once origin answers",
    )


def said(place: Place, tip: str, *, pushed: bool) -> str:
    """The line for the owner of a sync that ran: its push, or that there was nothing to take
    in."""
    short = tip[:7]
    if not pushed:
        return (
            f"{place.branch} holds origin/{place.base} already, as origin has it at "
            f"{short}: nothing to take in"
        )
    return f"{place.branch} took in origin/{place.base}, and origin has it at {short}"


def output_of(outcome: Outcome) -> str:
    """A command that failed, and the file of its output in the feature's folder."""
    return f"`{outcome.command}` (its output is {outcome.output})"
