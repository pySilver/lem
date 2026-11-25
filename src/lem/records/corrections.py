"""The correction queue: a reply of the owner that the correction hook flagged as a lesson,
and its review (`corrections.py` on `main`)."""

from typing import Literal

from lem.records.base import Frozen, Moment


class Correction(Frozen, frozen=True, kw_only=True):
    """One flagged reply: when, in which session and folder, the owner's words, the agent's
    text before them, and Jev's probability that it is a lesson, or why it was not asked."""

    at: Moment
    session: str
    cwd: str
    owner: str
    previous: str
    p_lesson: float | None = None
    why: str | None = None


class CorrectionReview(Frozen, frozen=True, kw_only=True):
    """A review of a group of corrections: whether it is a lesson, the verdict, where the lesson
    goes, and its words."""

    at: Moment
    session: str
    group: str
    p_lesson: float | None = None
    reviewed: Moment
    decision: Literal["lesson", "not_lesson"]
    verdict: Literal["accepted", "changed", "rejected", "proposed", "missed", "unasked"]
    target: str | None = None
    lesson: str | None = None
