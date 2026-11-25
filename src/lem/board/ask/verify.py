"""Validate the answers the board takes from a card."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from lem.board.ask.shape import Pick, Posted, Prompt

SESSION = "The owner can ask a question back in the task’s session."
RELOAD = "The owner can load the card again."


def normalized(prompts: tuple[Prompt, ...], posted: Posted) -> Posted:
    """Use the card's labels and take a value for each required question."""
    if posted.status == "chat":
        raise Refusal("ask-note", "The board takes a choice with a note.", SESSION)
    if posted.answers.keys() != {prompt.id for prompt in prompts}:
        raise Refusal("ask-question", "The answer names different questions.", RELOAD)
    return replace(
        posted, answers={prompt.id: checked(prompt, posted) for prompt in prompts}
    )


def checked(prompt: Prompt, posted: Posted) -> Pick:
    """Take this answer according to the prompt's mode and the options it showed."""
    picked = posted.answers[prompt.id]
    labels = {option.id: option.label for option in prompt.options}
    if set(picked.selected) - labels.keys():
        raise Refusal(
            "ask-option", "The answer names a choice the card did not show.", RELOAD
        )
    if prompt.mode in ("single", "multi"):
        check_choices(prompt, picked)
    if (
        prompt.mode == "text"
        and not prompt.optional
        and not (picked.text or "").strip()
    ):
        raise Refusal(
            "ask-text", "The answer needs words.", "The owner can type an answer."
        )
    if prompt.mode == "tune" and picked.controls is None:
        raise Refusal("ask-tune", "The answer needs control values.", RELOAD)
    return replace(picked, labels=tuple(labels[option] for option in picked.selected))


def check_choices(prompt: Prompt, picked: Pick) -> None:
    """Check the count and leave a note alone for the task's session."""
    count = len(picked.selected)
    if not count and (picked.text or "").strip():
        raise Refusal("ask-note", "The board takes a choice with a note.", SESSION)
    if too_many(prompt, picked):
        raise Refusal("ask-option", "The answer has too many choices.", RELOAD)
    minimum = max(1, prompt.minimum) if prompt.mode == "multi" else 1
    if count < minimum and (count or not prompt.optional):
        raise Refusal(
            "ask-option",
            "The answer needs a choice.",
            "The owner can choose an option.",
        )


def too_many(prompt: Prompt, picked: Pick) -> bool:
    """Whether the selection repeats options or exceeds the limit."""
    maximum = 1 if prompt.mode == "single" else prompt.maximum
    count = len(picked.selected)
    repeated = len(set(picked.selected)) != count
    return repeated or (maximum is not None and count > maximum)


def label_of(posted: Posted) -> str:
    """The labels of the choices, or a description of the other answer modes."""
    labels = tuple(
        label for picked in posted.answers.values() for label in picked.labels
    )
    if labels:
        return ", ".join(labels)
    if any(picked.text for picked in posted.answers.values()):
        return "An answer in words"
    return "The answer"


def note_of(posted: Posted) -> str | None:
    """The owner's note and text answers, in order."""
    return (
        "\n".join(picked.text for picked in posted.answers.values() if picked.text)
        or None
    )
