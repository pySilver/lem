"""The criteria of Jev's two question types."""

import msgspec

from lem.addons.jev.records import Choice, Noul, Question
from lem.kernel.errors import Refusal

MIN_CHOICES = 2


def invalid(why: str) -> Refusal:
    """The owner can correct the spec before sending anything."""
    return Refusal("jev-spec", why, "correct the spec and run lem jev check SPEC")


def criteria(name: str, asked: Question) -> dict[str, str] | None:
    """Each choice has a meaning; a noul names both meanings or neither."""
    if isinstance(asked, Choice):
        meanings = asked.choices
        labels = meanings.values()
        valid = all(map(str.strip, labels))
        if len(meanings) < MIN_CHOICES or not valid:
            raise invalid(f"question {name!r} needs two or more choices with meanings")
        return meanings
    return binary(name, asked)


def binary(name: str, asked: Noul) -> dict[str, str] | None:
    """Yes and no both have text or both are absent."""
    positive, negative = asked.positive, asked.negative
    if positive is msgspec.UNSET and negative is msgspec.UNSET:
        return None
    if not isinstance(positive, str) or not isinstance(negative, str):
        raise invalid(f"question {name!r} needs text for both yes and no, or neither")
    if not (positive.strip() and negative.strip()):
        raise invalid(f"question {name!r} needs non-empty criteria")
    return {"true": positive, "false": negative}
