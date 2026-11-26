"""What the owner reads about a rebase and its resolution (`land.sync_line` on `main`)."""

from typing import TYPE_CHECKING

from lem.model.landing import careful_words, carry, resolution

if TYPE_CHECKING:
    from lem.records.landing.propose import Proposed
    from lem.records.landing.record import Landing
    from lem.records.record import Record


def rebased(landing: Landing, made: Proposed) -> str | None:
    """The code review that carried, and whether its must-fix carried with it."""
    prior = carry.newest(landing)
    if prior is None or carry.source(landing, made) != prior.tip:
        return None
    suffix = ", and its open must-fix" if prior.counts.must_fix else ""
    return f"The review carried over the rebase{suffix}."


def reviewed(landing: Landing, made: Proposed) -> str | None:
    """The read the proposal took after the base moved."""
    read = resolution.read_of(landing)
    if read is not None and read.answered and read == landing.reviews[-1]:
        return "one read of the resolution"
    return rebased(landing, made)


def resolved(paths: tuple[str, ...]) -> str:
    """The files a builder resolved."""
    if len(paths) == 1:
        return f"one conflict in {paths[0]}, resolved by a builder"
    listed = ", ".join(paths)
    return f"conflicts in {len(paths)} files, {listed}, resolved by a builder"


def passed(landing: Landing, base: str) -> bool:
    """The checks passed on the base the proposal names."""
    checked = landing.checked
    return checked is not None and checked.base == base and checked.outcome == "passed"


def merge_line(landing: Landing, made: Proposed) -> str:
    """Whether the merge review carried over the resolution, and why a careful one needs a read."""
    if made.merge_review == "carried":
        return (
            "the merge review carried over the resolved conflict: "
            "the resolution read found nothing"
        )
    if made.careful or careful_words.review_reason(landing):
        return "a fresh merge agent reads it: the request is careful"
    return "a fresh merge agent reads it"


def summary(record: Record, made: Proposed) -> str | None:
    """One line of a conflicting pull request brought onto the base by a builder."""
    landing = record.landing
    if landing is None or landing.started is None or not landing.started.conflicting:
        return None
    conflict = landing.resolution
    if (
        conflict is None
        or conflict.before == conflict.after
        or conflict.base != made.base
        or not passed(landing, made.base)
    ):
        return None
    base = landing.started.base_ref
    parts = (
        f"rebased on {base} after the forge called it conflicting",
        resolved(conflict.files),
        reviewed(landing, made),
        merge_line(landing, made),
        "the checks passed again",
    )
    return "; ".join(filter(None, parts))


def sentence(line: str) -> str:
    """The summary as a sentence in the pull request."""
    first, rest = line[0].upper(), line[1:]
    return f"{first}{rest}."
