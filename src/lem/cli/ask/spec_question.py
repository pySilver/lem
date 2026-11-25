"""Question ids and options as the card's runtime reads them."""

import re

import msgspec

from lem.cli.ask import spec_types as shape

FIELDS = frozenset(field.encode_name for field in msgspec.structs.fields(shape.Page))
POSITION = re.compile(
    r"^\s*(?:criterion|story|option|item|task|step|choice|variant|approach|fork|finding|issue|"
    r"point|case|scenario|alternative|proposal|version|question)\s*[#№]?\s*(?:\d+|[a-z])\s*[.):]?\s*$",
    re.IGNORECASE,
)
KEY_OPTIONS = 9  # the card gives one number key to each option


def own(wires: dict[str, object]) -> dict[str, object]:
    """The fields the page reads. The spec's private keys stay on the page."""
    keys = filter(lambda key: not key.startswith("_"), wires)
    return {key: wires[key] for key in keys}


def question_of(wires: dict[str, object], fallback: str, title: str) -> str:
    """Check the question and give the id its page uses."""
    question = msgspec.convert(own(wires), shape.Question)
    named = question.id or fallback
    if not (question.prompt or title):
        raise ValueError(f"question {named!r} has no prompt")
    for control in question.controls or ():
        msgspec.convert(own(control), shape.Control)
    options_of(question.options or [], named)
    return named


def questions(page: shape.Page, wires: dict[str, object], *, multi: bool) -> None:
    """Check each question and refuse ids that appear twice."""
    if not multi:
        question_of(
            {key: wires[key] for key in wires.keys() - FIELDS}, "answer", page.title
        )
        return
    if not page.questions:
        raise ValueError("questions needs a non-empty list")
    ids = [
        question_of(question, f"q{index}", page.title)
        for index, question in enumerate(page.questions, 1)
    ]
    unique(ids, "question")


def options_of(options: list[str | dict[str, object]], question: str) -> None:
    """Check each option and refuse ids that appear twice."""
    if len(options) > KEY_OPTIONS:
        raise ValueError(f"question {question!r} has more than {KEY_OPTIONS} options")
    ids = [option_of(option, index) for index, option in enumerate(options, 1)]
    unique(ids, "option")


def option_of(wire: str | dict[str, object], index: int) -> str:
    """Check a label and give the id the option has on its page."""
    option = (
        shape.Option(id=wire, label=wire)
        if isinstance(wire, str)
        else msgspec.convert(own(wire), shape.Option)
    )
    named = option.id or f"o{index}"
    if POSITION.fullmatch(option.label or named) and not says_what(option):
        raise ValueError(
            f"option {named!r} only counts; add its words or show its details"
        )
    return named


def says_what(option: shape.Option) -> bool:
    """Whether the option says what it means beside its label."""
    details = (
        option.subtitle,
        option.detail,
        option.pros,
        option.cons,
        option.tags,
        option.preset,
    )
    return (
        any(details)
        or option.preview is not None
        or isinstance(option.recommended, str)
    )


def unique(ids: list[str], where: str) -> None:
    """Refuse an id that appears twice."""
    if len(ids) != len(set(ids)):
        raise ValueError(f"duplicate {where} ids: {ids}")
