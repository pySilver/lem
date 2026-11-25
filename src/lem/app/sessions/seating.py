"""The seats a task's roles take, from `[seats]` of the settings: one string `agent/model:effort`
for each, from the first of three files that names it, else Lem's own (`project.seat_of` on
`main`).

The three files are this machine's own for the repository (`.lem/settings.local.toml`), the
team's (`.lem/settings.toml`), and the developer's for all his repositories (`settings.toml` in
Lem's home folder). The reviewer's and the planner's seat, and the fallback, are written whole;
a part the merge agent's or the session's seat leaves out is that agent's own default. The
fallback stands in for the reviewer, the planner or the merge agent whose agent gives an error;
`false` turns it off. The settings read the files and give each seat with its place
(`lem.settings.load.settings_of`); this module reads a seat's line into the parts a stage opens.
"""

import re
from types import MappingProxyType
from typing import TYPE_CHECKING, Literal

from lem.kernel.errors import Refusal
from lem.records.base import Frozen
from lem.settings.load import settings_of

if TYPE_CHECKING:
    from pathlib import Path

type Role = Literal["reviewer", "planner", "merger", "session", "fallback"]

# Each role: the agents that may sit in it, whether its seat is written whole, and why.
BOTH = ("claude", "codex")
CLAUDE = ("claude",)
ROLES = MappingProxyType(
    {
        "reviewer": (BOTH, True, "the agents that can sit in the reviewer's pane"),
        "planner": (CLAUDE, True, "the harness was checked in Claude Code only"),
        "merger": (BOTH, False, "the agents a merge agent starts with, read-only"),
        "session": (CLAUDE, False, "a task's session runs Claude Code only for now"),
        "fallback": (BOTH, True, "the agents Lem can start in a seat's place"),
    }
)
FORM = '"agent/model:effort", or "agent:effort" or "agent"'
WHOLE = '"agent/model:effort", written whole'
# A seat: the agent, then its model after a `/`, then its effort after a `:`, with no space.
SEAT = re.compile(
    r"(?P<agent>[a-z]+)(?:/(?P<model>[^/:\s]+))?(?::(?P<effort>[^/:\s]+))?"
)


class Shown(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """A seat as a stage opens it: its agent, model and effort, the line as written, and the
    place it came from; `seat` is false for a fallback that is off."""

    agent: str | None
    model: str | None
    effort: str | None
    seat: str | Literal[False]
    source: str


def parsed(text: object, role: Role, where: str, source: str) -> Shown:
    """The seat `text` names for `role`, from the place `source`; refused for an agent that
    may not sit there."""
    agents, whole, why = ROLES[role]
    found = matched(text, where, whole=whole)
    if found["agent"] not in agents:
        names = ", ".join(agents)
        raise Refusal(
            "seat-agent",
            f"{where} = {text!r}: the agent {found['agent']!r} may not sit there: {why}",
            f"name one of {names}",
        )
    return Shown(
        agent=found["agent"],
        model=found["model"],
        effort=found["effort"],
        seat=found[0],
        source=source,
    )


def matched(text: object, where: str, *, whole: bool) -> re.Match[str]:
    """The parts of the seat `text`; refused for a seat not in the form, or one written whole
    that leaves a part out."""
    found = SEAT.fullmatch(text) if isinstance(text, str) else None
    complete = bool(found and found["model"] and found["effort"])
    if found is None or (whole and not complete):
        form = WHOLE if whole else FORM
        raise Refusal(
            "seat", f"{where} = {text!r} is not {form}", f"write it as {form}"
        )
    return found


def seat_of(role: Role, checkout: Path, home: Path | None) -> Shown:
    """The seat of `role` from the nearest file that names it, else Lem's, as the settings
    read them (Lem's home folder `home`); the fallback as `seat: false` when a file turns it
    off."""
    found = settings_of(checkout, home=home)
    given = getattr(found.settings.seats, role)
    source = found.sources[f"seats.{role}"]
    if given is False:
        return Shown(agent=None, model=None, effort=None, seat=False, source=source)
    return parsed(given, role, f"{source}: seats.{role}", source)
