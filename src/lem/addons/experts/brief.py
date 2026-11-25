"""Render one question in words for the experts to read independently."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lem.addons.experts.records import Record


def render(asked: Record, people: str) -> str:
    """The brief names the facts, evidence, audience and exact answer form."""
    asked_by = "The owner asks one expert this question."
    if len(asked.experts) > 1:
        asked_by = "The owner asks each expert to read this independently."
    return f"""# A question for the experts

{asked_by} The owner decides.
Read only. Change no file, run nothing that writes, and commit nothing.
The checkout is `{asked.checkout}`.

## The question

{asked.question}
{context(asked.context)}
{options(asked.options)}
## The files that matter

{listed(asked.files)}

{people}
## Your answer

Give only your last message in the form below.

{form(asked.options)}
"""


def context(words: str) -> str:
    """The decision and how it came up, if the caller gives it."""
    return f"\n## What is being decided\n\n{words}\n" if words else ""


def options(offered: tuple[str, ...]) -> str:
    """The choices word for word, or the instruction to answer in words."""
    if not offered:
        return "No options were given. Answer the question itself.\n"
    listed = enumerate(offered, 1)
    lines = (f"{number}. {word}" for number, word in listed)
    numbered = "\n".join(lines)
    return f"## The options, word for word\n\n{numbered}\n"


def listed(paths: tuple[str, ...]) -> str:
    """The files the question points to."""
    return (
        "\n".join(f"- {path}" for path in paths)
        or "- Read what the question points to."
    )


def form(offered: tuple[str, ...]) -> str:
    """The answer shape the record command checks."""
    if offered:
        return (
            "    pick: ONE OPTION, COPIED WORD FOR WORD FROM THE OPTIONS ABOVE\n"
            "    why: two to four sentences. Cite what decides it.\n\n"
            "    none fits\n"
            "    why: two to four sentences. Say why and what would fit."
        )
    return "    answer: one to three sentences.\n    why: Say what decides it."
