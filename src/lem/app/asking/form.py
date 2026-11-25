"""The names the question runtime gives to the questions and options of a checked spec."""

import msgspec

from lem.app.asking.shape import Card, Mode, Option, Prompt

type Spec = dict[str, object]


def metadata(spec: Spec, page: str, session: str) -> Card:
    """The card as the board may answer it."""
    questions = spec.get("questions")
    title = str(spec.get("title") or "")
    if isinstance(questions, list):
        prompts = tuple(
            prompt_of(question, f"q{index}", title)
            for index, question in enumerate(questions, 1)
        )
    else:
        prompts = (prompt_of(spec, "answer", title),)
    return Card(page=page, session=session, prompts=prompts)


def prompt_of(wire: Spec, default: str, title: str) -> Prompt:
    """One question, as the card will show it."""
    choices = choices_of(wire)
    named = wire.get("id") or default
    return msgspec.convert(
        {
            "id": named,
            "prompt": wire.get("prompt") or title,
            "mode": mode_of(wire, choices),
            "options": choices,
            "optional": wire.get("optional", False),
            "minimum": wire.get("min", 0),
            "maximum": wire.get("max"),
        },
        Prompt,
    )


def mode_of(wire: Spec, choices: tuple[Option, ...]) -> Mode:
    """The mode set by the spec, or the one inferred by the page."""
    given = wire.get("mode")
    if given in ("single", "multi", "text", "tune"):
        return msgspec.convert(given, Mode)
    if wire.get("controls") is not None:
        return "tune"
    return "single" if choices else "text"


def option_of(wire: str | Spec, index: int) -> Option:
    """An option of the given name and label, or the page's own id."""
    if isinstance(wire, str):
        return Option(id=wire, label=wire)
    named = str(wire.get("id") or f"o{index}")
    return Option(id=named, label=str(wire.get("label") or named))


def choices_of(wire: Spec) -> tuple[Option, ...]:
    """The card's choices in display order."""
    listed = wire.get("options")
    if not isinstance(listed, list):
        return ()
    numbered = enumerate(listed, 1)
    return tuple(option_of(option, index) for index, option in numbered)
