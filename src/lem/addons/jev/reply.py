"""The provider's answers, checked against the questions sent."""

import msgspec

from lem.addons.jev.records import Probability, Request
from lem.kernel.errors import Refusal
from lem.records.base import Frozen

type Answer = ChoiceAnswer | NoulAnswer


class ChoiceAnswer(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """The choice and its probabilities."""

    type: str = "choice"
    choice: str
    confidence: Probability
    probabilities: dict[str, Probability]


class NoulAnswer(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """The probability of yes."""

    type: str = "noul"
    noul: Probability


class ProviderReply(Frozen, frozen=True, kw_only=True):
    """The provider may omit its usage information."""

    answers: dict[str, object]
    model: str | None = None
    usage: dict[str, object] | None = None


class Reply(msgspec.Struct, frozen=True, kw_only=True):
    """The model, the checked answers, and the cost when the provider gives it."""

    model: str | None
    answers: dict[str, Answer]
    cost: object


def invalid(why: str) -> Refusal:
    """A provider reply the owner cannot use."""
    return Refusal(
        "jev-reply", why, "check the owner's provider and repeat lem jev ask SPEC"
    )


def answer(name: str, kind: str, given: object) -> Answer:
    """Check one answer, including the type when the provider names it."""
    try:
        found = msgspec.convert(given, NoulAnswer if kind == "noul" else ChoiceAnswer)
    except msgspec.ValidationError as error:
        raise invalid(
            f"the reply's answer to question {name!r} is invalid: {error}"
        ) from error
    if found.type != kind or (
        isinstance(found, ChoiceAnswer) and not found.probabilities
    ):
        raise invalid(
            f"question {name!r} has the wrong answer type or empty probabilities"
        )
    return found


def read(raw: bytes, asked: Request) -> Reply:
    """Read a reply that has one answer for every question."""
    try:
        found = msgspec.json.decode(raw, type=ProviderReply)
    except msgspec.DecodeError as error:
        raise invalid(f"the provider's reply does not read: {error}") from error
    if found.answers.keys() != asked.questions.keys():
        raise invalid("the provider's reply does not answer every question")
    return Reply(
        model=found.model,
        answers={
            name: answer(name, query.type, found.answers[name])
            for name, query in asked.questions.items()
        },
        cost=(found.usage or {}).get("cost"),
    )
