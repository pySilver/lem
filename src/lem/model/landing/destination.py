"""The task's base branch stays the same across the rounds of its landing."""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from lem.records.landing.record import Landing


def recorded(landing: Landing | None) -> str | None:
    """The destination recorded at the start, if the landing has begun."""
    started = landing.started if landing else None
    return started.base_ref if started else None


def missing(branch: str) -> Refusal:
    """The task cannot land when origin has no branch at its destination."""
    return Refusal(
        "no-base",
        f"origin has no branch {branch}, the base of the task",
        f"push {branch} to origin, then run the step again",
    )
