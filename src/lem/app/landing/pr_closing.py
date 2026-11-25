"""The last lines of the pull request's checks (`main:land.untalked`,
`stand_in_line`, `careful_line`): the plan talk, or why a careful request had none; each seat
that stood in for another, a fact and no reason of not green; and the careful call."""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.app.landing import pr_talk
from lem.model.landing import propose_careful, propose_gates
from lem.model.landing.green_words import reason
from lem.model.landing.review import newest
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.app.landing.pr_inputs import Lines
    from lem.model.landing.propose_facts import Facts
    from lem.records.record import Record
    from lem.records.work import StandIn

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


def became(record: Record, facts: Facts) -> list[str]:
    """How a request with no talk due became careful after its plan."""
    shape = record.task.shape
    how = ["by the request's shape"] if shape and shape.careful else []
    if propose_careful.edits(facts):
        how.append("by its change to the settings")
    if propose_careful.review_call(record):
        how.append("by its review")
    return how


def talk(record: Record, facts: Facts) -> Lines:
    """The plan talk when the plan called for one; else, for a careful request, that it had
    none since it became careful after its plan, and how."""
    held = record.task.talk
    if propose_gates.talk_due(record) and held is not None:
        return (pr_talk.talked(held),)
    how = became(record, facts)
    if not how:
        return ()
    listed = " and ".join(how)
    return (f"- no plan talk: the request became careful after its plan, {listed}",)


def agent_of(line: str) -> str:
    """The agent of a seat's line (`agent/model:effort`) by the name a person knows it by."""
    agent = line.partition("/")[0].partition(":")[0]
    return AGENTS.get(agent, agent)


def stand_in(found: StandIn) -> str:
    """A seat that stood in for another: which, for which, and why."""
    seat, error = SEATS[found.seat], ERRORS[found.error]
    agent = agent_of(found.failed)
    took = found.took or "nothing"
    return f"- {seat} was `{took}` in place of `{found.failed}`: {agent} {error}"


def careful_line(record: Record, careful: tuple[str, ...]) -> str:
    """Whether the request is careful, each reason it is, and the newest review's call with
    its reason when the review said no."""
    listed = "; ".join(careful)
    line = f"- careful: yes, {listed}" if careful else "- careful: no"
    last = newest(record.landing or Landing())
    if last is None or last.careful is None:
        return f"{line}; no review that answered made the call"
    if last.careful:
        return line
    said = reason(last.careful_why or "no reason given")
    return f"{line}; the review says no: {said}"


def lines(
    record: Record, facts: Facts, careful: tuple[str, ...], *, full: bool
) -> Lines:
    """The plan talk on the standard track, each stand-in, and the careful call."""
    talks = talk(record, facts) if full else ()
    stood = tuple(map(stand_in, record.task.stand_ins))
    return (*talks, *stood, careful_line(record, careful))
