"""A seat, `agent/model:effort`, read into its parts by the rule of the seat it stands in.

The reviewer, the planner, each expert and the fallback are written whole (the owner,
2026-11-18: "explicitly `agent/model:effort` in all 3"); a part left out of the merge agent's or a
task session's seat is the agent's own default. A model and an effort are not checked against a
list: their names change with each release of an agent, whose command refuses a wrong one when
it starts. The agents of a seat are the ones its harness was checked with.
"""

import re

from lem.kernel.errors import Refusal
from lem.records.base import Frozen

FORM = "agent/model:effort"
BOTH = ("claude", "codex")
CLAUDE = ("claude",)
# A line's agent, its model after the one `/`, and its effort after a `:`.
PARTS = re.compile(r"([^/:]*)(?:/([^:]*))?(?::(.*))?", re.DOTALL)
# An expert's place in a record, whatever model sits there.
PLACES = ("fable", "astra")


class Rule(Frozen, frozen=True, kw_only=True):
    """One seat: the agents that may sit in it, why only those, and whether it is whole."""

    name: str
    agents: tuple[str, ...]
    why: str
    whole: bool = True


class Seat(Frozen, frozen=True, kw_only=True):
    """One seat's parts, each None where the line leaves it out, and the line as written."""

    agent: str
    model: str | None = None
    effort: str | None = None
    seat: str


RULES = (
    Rule(
        name="reviewer",
        agents=BOTH,
        why="the agents that can sit in the reviewer's pane",
    ),
    Rule(
        name="planner", agents=CLAUDE, why="the harness was checked in Claude Code only"
    ),
    Rule(
        name="merger",
        agents=BOTH,
        why="the agents the harness starts a merge agent with",
        whole=False,
    ),
    Rule(
        name="session",
        agents=CLAUDE,
        why="a task's session runs Claude Code only for now",
        whole=False,
    ),
    Rule(
        name="experts", agents=BOTH, why="the agents the harness starts an expert with"
    ),
    Rule(
        name="fallback", agents=BOTH, why="the agents Lem can start in a seat's place"
    ),
)
NAMES = tuple(found.name for found in RULES)


def rule(name: str) -> Rule:
    """The rule of the seat `name`."""
    return next(found for found in RULES if found.name == name)


def split(line: str) -> Seat:
    """The parts of a line, each None where it is left out, and empty where it is empty."""
    found = PARTS.fullmatch(line)
    agent, model, effort = found.groups() if found else (line, None, None)
    return Seat(agent=agent, model=model, effort=effort, seat=line)


def form_flaw(line: str) -> str | None:
    """What is wrong with the form of a line: a space, or a second `:`."""
    if any(char.isspace() for char in line):
        return "holds a space"
    colons = line.count(":")
    if colons > 1:
        return f"holds {colons} `:`, and a seat has one at most, before the effort"
    return None


def part_flaw(found: Seat, seat_rule: Rule) -> str | None:
    """What is wrong with the parts of a line by the rule of its seat."""
    if found.agent not in seat_rule.agents:
        allowed = " or ".join(seat_rule.agents)
        return f"names the agent {found.agent!r}, and it must be {allowed}: {seat_rule.why}"
    if "" in {found.model, found.effort}:
        return "names an empty model or effort after its `/` or `:`"
    missing = [part for part in ("model", "effort") if getattr(found, part) is None]
    if seat_rule.whole and missing:
        listed = " and no ".join(missing)
        return f"names no {listed}"
    return None


def parsed(line: str, name: str, where: str) -> Seat:
    """The parts of the seat `name` written `line`; refused when it does not read by the rule
    of that seat."""
    seat_rule = rule(name)
    found = split(line)
    flaw = form_flaw(line) or part_flaw(found, seat_rule)
    if flaw:
        whole = " whole" if seat_rule.whole else ", a part may be left out"
        raise Refusal(
            "settings",
            f"{where} = {line!r} {flaw}",
            f'write one string, "{FORM}"{whole}, or leave the line out for Lem\'s',
        )
    return found
