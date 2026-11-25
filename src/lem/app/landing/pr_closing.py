"""The last lines of the pull request's checks (`main:land.talked`, `untalked`,
`stand_in_line`, `careful_line`): the plan talk, or why a careful request had none; each seat
that stood in for another, a fact and no reason of not green; and the careful call."""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.app.landing.pr_inputs import Lines
from lem.model.landing import propose_careful, propose_gates
from lem.model.landing.green_words import reason
from lem.model.landing.review import newest
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.model.landing.propose_facts import Facts
    from lem.records.record import Record
    from lem.records.work import StandIn, Talk

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
SEATS = MappingProxyType(
    {"reviewer": "the reviewer", "planner": "the planner", "merger": "the merge agent"}
)
AGENTS = MappingProxyType({"claude": "Claude Code", "codex": "Codex"})
ERRORS = MappingProxyType(
    {
        "missing": "is not on this Mac",
        "login": "had no login",
        "tokens": "had no tokens",
        "model": "did not know the model",
    }
)


def many(count: int, forms: tuple[str, str]) -> str:
    """A count with the form of its noun for one or for more."""
    one, more = forms
    return f"{count} {one if count == 1 else more}"


def talked(talk: Talk) -> str:
    """The plan talk: who argued it, its turns and positions, then each other count."""
    counts = ", ".join(
        many(getattr(talk, name), forms) for name, forms in TALK_SAYS.items()
    )
    turns = many(talk.turns, ("turn", "turns"))
    settled = many(talk.settled, ("position", "positions"))
    argued = f"{talk.reviewer} argued the plan with its defender, {turns}"
    return f"- the plan talk: {argued}; {settled} settled by the two, {talk.open} left open; {counts}"


def talk(record: Record, facts: Facts) -> Lines:
    """The plan talk when the plan called for one; else, for a careful request, that it had
    none since it became careful after its plan, and how."""
    held = record.task.talk
    if propose_gates.talk_due(record) and held is not None:
        return (talked(held),)
    how = [
        *(
            ["by the request's shape"]
            if record.task.shape and record.task.shape.careful
            else []
        ),
        *(["by its change to the settings"] if propose_careful.edits(facts) else []),
        *(["by its review"] if propose_careful.review_call(record) else []),
    ]
    if not how:
        return ()
    listed = " and ".join(how)
    return (f"- no plan talk: the request became careful after its plan, {listed}",)


def stand_in(found: StandIn) -> str:
    """A seat that stood in for another: which, for which, and why."""
    seat = SEATS[found.seat]
    agent = found.failed.partition("/")[0].partition(":")[0]
    why = f"{AGENTS.get(agent, agent)} {ERRORS[found.error]}"
    took = found.took or "nothing"
    return f"- {seat} was `{took}` in place of `{found.failed}`: {why}"


def careful_line(record: Record, careful: tuple[str, ...]) -> str:
    """Whether the request is careful, each reason it is, and the newest review's call with
    its reason when the review said no."""
    line = f"- careful: yes, {'; '.join(careful)}" if careful else "- careful: no"
    last = newest(record.landing or Landing())
    if last is None or last.careful is None:
        return f"{line}; no review that answered made the call"
    if not last.careful:
        return f"{line}; the review says no: {reason(last.careful_why or 'no reason given')}"
    return line


def lines(
    record: Record, facts: Facts, careful: tuple[str, ...], *, full: bool
) -> Lines:
    """The plan talk on the standard track, each stand-in, and the careful call."""
    talks = talk(record, facts) if full else ()
    stood = tuple(map(stand_in, record.task.stand_ins))
    return (*talks, *stood, careful_line(record, careful))
