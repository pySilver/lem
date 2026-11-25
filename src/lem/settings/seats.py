"""A seat, `agent/model:effort`, read into its parts by the rule of the seat it stands in.

The reviewer, the planner, each expert and the fallback are written whole (the owner,
2026-11-18: "explicitly `agent/model:effort` in all 3"); a part left out of the merge agent's or a
task session's seat is the agent's own default. A model and an effort are not checked against a
list: their names change with each release of an agent, whose command refuses a wrong one when
it starts. The agents of a seat are the ones its harness was checked with.
"""

from typing import Literal

from lem.kernel.errors import Refusal
from lem.records.base import Frozen

type Name = Literal["reviewer", "planner", "merger", "session", "experts", "fallback"]

FORM = "agent/model:effort"
BOTH = ("claude", "codex")
# Each seat: the agents that may sit in it, why only those, and whether it is written whole.
RULES: tuple[tuple[Name, tuple[str, ...], str, bool], ...] = (
    ("reviewer", BOTH, "the agents that can sit in the reviewer's pane", True),
    ("planner", ("claude",), "the harness was checked in Claude Code only", True),
    ("merger", BOTH, "the agents the harness starts a merge agent with", False),
    ("session", ("claude",), "a task's session runs Claude Code only for now", False),
    ("experts", BOTH, "the agents the harness starts an expert with", True),
    ("fallback", BOTH, "the agents Lem can start in a seat's place", True),
)
NAMES = tuple(found[0] for found in RULES)
# An expert's place in a record, whatever model sits there.
PLACES = ("fable", "astra")


class Seat(Frozen, frozen=True, kw_only=True):
    """One seat's parts, each None where the line leaves it out, and the line as written."""

    agent: str
    model: str | None = None
    effort: str | None = None
    seat: str


def rule(name: str) -> tuple[tuple[str, ...], str, bool]:
    """The agents of the seat `name`, why, and whether it is written whole."""
    return next(found[1:] for found in RULES if found[0] == name)


def refused(where: str, line: str, why: str, *, whole: bool) -> Refusal:
    """The refusal of a seat's line, with its form."""
    form = f'one string, "{FORM}"'
    left = "" if whole else "; the effort, or the model and the effort, may be left out"
    return Refusal(
        "settings",
        f"{where} = {line!r} {why}",
        f"write {form}{' whole' if whole else ''}{left}, or leave the line out for Lem's",
    )


def parts(line: str) -> tuple[str, str | None, str | None]:
    """The agent, the model and the effort of a line, each None where it is left out."""
    agent, slash, rest = line.partition("/")
    if not slash:
        agent, colon, effort = agent.partition(":")
        return agent, None, effort if colon else None
    model, colon, effort = rest.partition(":")
    return agent, model, effort if colon else None


def flaw(line: str, name: str) -> str | None:
    """What is wrong with a seat's line, or None when it reads."""
    agents, why, whole = rule(name)
    agent, model, effort = parts(line)
    if any(char.isspace() for char in line):
        return "holds a space"
    if line.count(":") > 1:
        return f"holds {line.count(':')} `:`, and a seat has one at most, before the effort"
    if agent not in agents:
        return f"names the agent {agent!r}, and it must be {' or '.join(agents)}: {why}"
    if model == "" or effort == "":
        return "names an empty model or effort after its `/` or `:`"
    missing = [
        part for part, given in (("model", model), ("effort", effort)) if not given
    ]
    if whole and missing:
        return f"names no {' and no '.join(missing)}"
    return None


def parsed(line: str, name: str, where: str) -> Seat:
    """The parts of the seat `name` written `line`; refused when it does not read by the rule
    of that seat."""
    found = flaw(line, name)
    if found:
        raise refused(where, line, found, whole=rule(name)[2])
    agent, model, effort = parts(line)
    return Seat(agent=agent, model=model, effort=effort, seat=line)
