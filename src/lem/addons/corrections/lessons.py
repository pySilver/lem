"""`lem corrections lessons`: the lessons earlier retros recorded, each with its file, its
verdict, how many entries it stood for and on which days, the most entries first
(`corrections.cmd_lessons` on `main`)."""

from typing import TYPE_CHECKING

from lem.addons.corrections import queue
from lem.records.base import Frozen
from lem.records.corrections import CorrectionReview

if TYPE_CHECKING:
    from pathlib import Path

type Key = tuple[str, str, str]


class Lesson(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """One lesson: its sentence, its file, its verdict, its entries and its days."""

    lesson: str
    target: str | None
    verdict: str
    entries: int
    days: tuple[str, ...]


def lessons(state: Path) -> tuple[Lesson, ...]:
    """Every lesson recorded, by its sentence, file and verdict, the most entries first."""
    found: dict[Key, list[CorrectionReview]] = {}
    for review in queue.lines(state / queue.REVIEWS, CorrectionReview):
        if review.decision == "lesson":
            key = (review.lesson or "", review.target or "", review.verdict)
            found.setdefault(key, []).append(review)
    rows = (lesson_of(key, reviews) for key, reviews in found.items())
    return tuple(sorted(rows, key=lambda row: -row.entries))


def lesson_of(key: Key, reviews: list[CorrectionReview]) -> Lesson:
    """One lesson and the reviews that recorded it."""
    lesson, target, verdict = key
    days = {review.at.date().isoformat() for review in reviews}
    return Lesson(
        lesson=lesson,
        target=target or None,
        verdict=verdict,
        entries=len(reviews),
        days=tuple(sorted(days)),
    )
