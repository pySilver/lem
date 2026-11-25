"""The seats a task's roles take, from `[seats]` of the settings: one string `agent/model:effort`
for each, from the first of three files that names it, else Lem's own (`project.seat_of` on
`main`).

The three files are this machine's own for the repository (`.lem/settings.local.toml`), the
team's (`.lem/settings.toml`), and the developer's for all his repositories (`settings.toml` in
Lem's home folder). The reviewer's and the planner's seat, and the fallback, are written whole;
a part the merge agent's or the session's seat leaves out is that agent's own default. The
fallback stands in for the reviewer, the planner or the merge agent whose agent gives an error;
`false` turns it off. A stand-in of the step `settings`, which reads every table:
`notes/sessions.md` asks it for the seats with their place, and this module then reads them
there.
"""

import re
import tomllib
from types import MappingProxyType
from typing import TYPE_CHECKING, Literal

from lem.kernel.errors import Refusal
from lem.records.base import Frozen

if TYPE_CHECKING:
    from pathlib import Path

# Each file a seat may come from, with the name `from` gives it.
type Places = tuple[tuple[Path, str], ...]
type Role = Literal["reviewer", "planner", "merger", "session", "fallback"]

# Each role: the agents that may sit in it, whether its seat is written whole, and why.
ROLES = MappingProxyType(
    {
        "reviewer": (
            "claude codex",
            True,
            "the agents that can sit in the reviewer's pane",
        ),
        "planner": ("claude", True, "the harness was checked in Claude Code only"),
        "merger": (
            "claude codex",
            False,
            "the agents a merge agent starts with, read-only",
        ),
        "session": ("claude", False, "a task's session runs Claude Code only for now"),
        "fallback": (
            "claude codex",
            True,
            "the agents Lem can start in a seat's place",
        ),
    }
)
# Lem's own seat of each role (the owner, 2026-11-22 and 2026-11-23: `claude/opus:high`).
DEFAULT = "claude/opus:high"
DEFAULT_FROM = "Lem's default"
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


def places(checkout: Path, home: Path | None) -> Places:
    """The three files a seat may come from, first to last, each with the name `from` gives."""
    folder = checkout / ".lem"
    local = (folder / "settings.local.toml", ".lem/settings.local.toml")
    team = (folder / "settings.toml", ".lem/settings.toml")
    if home is None:
        return (local, team)
    mine = home / "settings.toml"
    return (local, team, (mine, str(mine)))


def seats_table(path: Path) -> dict[str, object]:
    """The `[seats]` table of one file, empty when the file or the table is not there."""
    try:
        table = tomllib.loads(path.read_text(encoding="utf-8")).get("seats", {})
    except FileNotFoundError:
        return {}
    except tomllib.TOMLDecodeError as error:
        raise Refusal(
            "settings-toml", f"{path} is not TOML: {error}", f"correct {path}"
        ) from error
    return table if isinstance(table, dict) else {}


def seat_of(role: Role, checkout: Path, home: Path | None) -> Shown:
    """The seat of `role` from the first file that names it, else Lem's; the fallback as
    `seat: false` when a file turns it off."""
    for path, name in places(checkout, home):
        given = seats_table(path).get(role)
        if given is False and role == "fallback":
            return Shown(agent=None, model=None, effort=None, seat=False, source=name)
        if given is not None:
            return parsed(given, role, f"{name}: seats.{role}", name)
    return parsed(DEFAULT, role, DEFAULT_FROM, DEFAULT_FROM)
