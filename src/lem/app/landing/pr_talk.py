"""The plan talk as one line of the pull request's checks (`main:land.talked`): who argued
the plan with its defender, its turns and positions, then each other count of the talk."""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.model.task.talk import bound

if TYPE_CHECKING:
    from lem.records.work import Talk

# The counts of a plan talk after its turns and positions, one form for one and one for
# more, in the words of the pull request.
TALK_SAYS = MappingProxyType(
    {
        "questions": (
            "question in the reviewer's first list",
            "questions in the reviewer's first list",
        ),
        "repaired": ("repaired by the defender", "repaired by the defender"),
        "design": (
            "of the open ones a design choice",
            "of the open ones a design choice",
        ),
        "unargued": (
            "raised after the list and not argued",
            "raised after the list and not argued",
        ),
        "root": ("repaired at the cause", "repaired at the cause"),
        "layer": ("layer over a cited decision", "layers over a cited decision"),
        "shared": ("decision two questions named", "decisions two questions named"),
    }
)


def many(count: int, forms: tuple[str, str]) -> str:
    """A count with the form of its noun for one or for more."""
    one, more = forms
    noun = one if count == 1 else more
    return f"{count} {noun}"


def counted(talk: Talk) -> str:
    """Each count of the plan talk after its turns and positions, in its words."""
    return ", ".join(
        many(getattr(talk, name), forms) for name, forms in TALK_SAYS.items()
    )


def turns_of(talk: Talk) -> str:
    """The turns the talk took, and its bound if it went over."""
    turns = many(talk.turns, ("turn", "turns"))
    limit = bound(talk)
    if talk.turns <= limit:
        return turns
    questions = many(talk.questions, ("question", "questions"))
    return f"{turns}, over the bound of {limit} for its {questions}"


def talked(talk: Talk) -> str:
    """The plan talk: who argued it, its turns and positions, then each other count."""
    turns = turns_of(talk)
    argued = f"{talk.reviewer} argued the plan with its defender, {turns}"
    settled = many(talk.settled, ("position", "positions"))
    left = f"{settled} settled by the two, {talk.open} left open"
    return f"- the plan talk: {argued}; {left}; {counted(talk)}"
