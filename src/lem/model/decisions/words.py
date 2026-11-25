"""The words a command keeps in a record: UTF-8 text, each run of spaces as one where the words
are a sentence. An argument of other bytes is refused before any record holds it, as `main`'s
`state.unreadable_argument` refused it."""

from lem.kernel.errors import Refusal


def spaced(text: str) -> str:
    """A text with each run of spaces as one; one that is no UTF-8 text is refused before any
    record holds it."""
    return " ".join(text_of(text).split())


def text_of(text: str) -> str:
    """A text as given; one that is no UTF-8 text (an argument of other bytes) is refused."""
    try:
        text.encode("utf-8")
    except UnicodeEncodeError:
        raise Refusal(
            "not-text", f"{text!r} is not UTF-8 text", "give it in UTF-8"
        ) from None
    return text
