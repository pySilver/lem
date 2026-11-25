"""A question to the owner, on the board or in a card, and his answer: the first answer
counts (`answers.py` on `main`).

A question's id names the question and the moment it was asked, so a question asked again is a
new one; an answer carries the id and the digest the owner was shown, and an answer to an older
question or of another digest is refused.
"""

from typing import Literal

from lem.records.base import Frozen, Moment

type Topic = Literal["plan", "breaker", "skip", "criterion", "card"]


class Answer(Frozen, frozen=True, kw_only=True):
    """His answer: the option and its label, his note, from where and on what, and when."""

    option: str
    label: str
    note: str | None = None
    source: Literal["board", "session", "card"]
    via: Literal["local", "door"] | None = None
    device: Literal["phone", "computer"] | None = None
    agent: str | None = None
    at: Moment


class Question(Frozen, frozen=True, kw_only=True):
    """A question: its id, topic and words, the options, the note shown with it, the digest of
    what it shows, when it was asked, and his answer once he gave one."""

    id: str
    topic: Topic
    question: str
    options: tuple[str, ...]
    note: str | None = None
    digest: str | None = None
    asked: Moment
    answer: Answer | None = None
    took_effect: str | None = None
