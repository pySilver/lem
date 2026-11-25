"""Jev's own form of a request and its reply, the same at every provider (`jev.build` and
`jev.read` on `main`): a POST of the model, the state and the questions, each a yes or no one
(`noul`) with what each answer means, and a reply with each question's probability of yes.

`LIMIT_BYTES` is OpenRouter's line: through it, a request with more than about 32,000 bytes of
text runs in a long-context mode that TypeSafe calls slower and less accurate (OpenRouter's
guide, read 2026-11-23). A request over it is never sent, and nothing is cut down to fit.
"""

import msgspec

LIMIT_BYTES = 32_000
OVER = "over"
OVER_ASKED = (
    "This finding is a defect that an agent saw in the change it worked on or in the code "
    "outside it, and called under the bar for an item of the backlog. Is the finding over the "
    "bar?"
)
OVER_MET = "The finding meets the bar: {0}."
OVER_UNMET = "The finding does not meet that bar."
SAME_ASKED = "Is the finding the same defect as this item of the backlog? The item, {0}"
SAME_ONE = (
    "The finding and the item are one defect, so the item holds the finding and no second "
    "item is needed."
)
SAME_TWO = (
    "The finding is another defect than the item's, in the same place or in another."
)


class Question(msgspec.Struct, frozen=True, kw_only=True):
    """A yes or no question, and what each answer means (`criteria` `true` and `false`)."""

    instructions: str
    criteria: dict[str, str]
    kind: str = msgspec.field(default="noul", name="type")


class Request(msgspec.Struct, frozen=True, kw_only=True):
    """One request: the model, the facts to decide on, and the questions by name."""

    model: str
    state: dict[str, str]
    questions: dict[str, Question]


class Answer(msgspec.Struct, frozen=True, kw_only=True):
    """One answer: its type, which a yes or no question's is, and the probability of yes."""

    noul: float
    kind: str = msgspec.field(default="noul", name="type")


class Reply(msgspec.Struct, frozen=True, kw_only=True):
    """The reply: an answer for each question."""

    answers: dict[str, Answer]


def question(instructions: str, meant: str, unmeant: str) -> Question:
    """A yes or no question, with what a yes means and what a no means."""
    return Question(
        instructions=instructions, criteria={"true": meant, "false": unmeant}
    )


def size_of(request: Request) -> int:
    """The bytes of a request's text, as Jev's limit counts them: the state's JSON and the
    questions'."""
    state = msgspec.json.encode(request.state)
    return len(state) + len(msgspec.json.encode(request.questions))


def scores_of(body: bytes, asked: Request) -> dict[str, float] | None:
    """Each question's probability of yes, or None for a reply that does not answer every
    question with a number from 0 to 1."""
    try:
        reply = msgspec.json.decode(body, type=Reply)
    except msgspec.DecodeError:
        return None
    said = {name: answer.noul for name, answer in reply.answers.items()}
    if set(said) != set(asked.questions):
        return None
    if any(answer.kind != "noul" for answer in reply.answers.values()):
        return None
    if not all(0 <= score <= 1 for score in said.values()):
        return None
    return said
