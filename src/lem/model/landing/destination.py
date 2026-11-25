"""The task's base branch stays the same across the rounds of its landing."""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from lem.records.landing.record import Landing
    from lem.records.record import Record


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


def same_pull(record: Record, shown: tuple[int, str] | None) -> Refusal | None:
    """Why the pull request the forge shows is not the one on record: none, or another
    repository's or number's address (H 2, in the configured repository)."""
    slug = record.task.slug
    kept = record.landing.pull if record.landing else None
    if kept is not None and shown == (kept.number, kept.url):
        return None
    address = shown[1] if shown else "no pull request"
    return Refusal(
        "no-pull",
        f"the forge shows {address}, not the pull request on record",
        f"lem land next {slug}",
    )
