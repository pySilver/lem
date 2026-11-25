"""The parts of the standard track's notes as the pull request's text rewrites them: a part
put in place of the one there, or after the last heading that comes before it, and the notes
written out again (`main:land.with_outside`)."""

from typing import TYPE_CHECKING

from lem.model.landing.propose_lines import FILED, FIXED, NOT_WORTH, SEEN
from lem.model.landing.propose_notes import Part

if TYPE_CHECKING:
    from lem.app.landing.pr_inputs import Lines

ORDER = (FILED, NOT_WORTH, FIXED, SEEN)


def place_of(parts: list[Part], heading: str) -> int:
    """Where a new part goes: after the last heading that comes before it in `ORDER`."""
    earlier = ORDER[: ORDER.index(heading)]
    places = [at for at, found in enumerate(parts) if found.heading in earlier]
    return places[-1] + 1 if places else len(parts)


def apart(parts: list[Part], place: int) -> None:
    """Give the part before `place` a blank line at its end, so that a heading after it is a
    paragraph of its own."""
    previous = parts[place - 1] if place else None
    if previous is None or previous.lines[-1:] == ("",):
        return
    lines = (*previous.lines, "")
    parts[place - 1] = Part(heading=previous.heading, lines=lines)


def inserted(parts: list[Part], heading: str, more: Lines) -> None:
    """Put `more` under `heading` in place of the lines there, or as a part of its own."""
    made = Part(heading=heading, lines=("", *more, ""))
    there = [at for at, found in enumerate(parts) if found.heading == heading]
    if there:
        parts[there[0]] = made
        return
    place = place_of(parts, heading)
    apart(parts, place)
    parts.insert(place, made)


def written(head: Lines, parts: list[Part] | tuple[Part, ...]) -> str:
    """The notes written out: the lines before the first heading, then each part."""
    lines = (line for found in parts for line in (found.heading, *found.lines))
    return "\n".join((*head, *lines))
