"""A persona's frontmatter names its seats, apart from the words its agent reads."""

import os
from typing import TYPE_CHECKING

import msgspec

from lem.addons.cast.front import DEFAULT, frontmatter, invalid
from lem.kernel import files
from lem.records.base import Frozen
from lem.settings import experts, seats
from lem.store.guard import writable

if TYPE_CHECKING:
    from pathlib import Path


class Named(seats.Seat, frozen=True, kw_only=True, omit_defaults=False):
    """A seat, with the name its answer carries and whether the agent is here."""

    name: str
    here: bool


class Person(Frozen, frozen=True, kw_only=True):
    """The persona's paths and the seats on which its agents read it."""

    stem: str
    path: str
    person: str
    seats: tuple[Named, ...]
    left_out: tuple[Named, ...]
    seats_from: str


def named(parts: tuple[seats.Seat, ...]) -> tuple[Named, ...]:
    """Add the answer names and mark which agents can start."""
    from lem.addons.cast.names import name_of

    return tuple(
        Named(
            **msgspec.structs.asdict(seat),
            name=name_of(seat.model, "sol" if seat.agent == "codex" else seat.agent),
            here=seat.agent == "claude" or experts.answers(seat.agent, os.environ),
        )
        for seat in parts
    )


def read(path: Path, state: Path) -> Person:
    """Keep the original path and publish a prose-only copy when necessary."""
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeError as error:
        raise invalid(path, "does not contain UTF-8 text") from error
    parts, body = frontmatter(text, path)
    assigned = named(parts)
    if len({seat.name for seat in assigned}) != len(assigned):
        raise invalid(path, "names two seats with the same answer name")
    shown = path if body == text else prose(path, state, body)
    return Person(
        stem=path.stem,
        path=str(path),
        person=str(shown),
        seats=tuple(seat for seat in assigned if seat.here),
        left_out=tuple(seat for seat in assigned if not seat.here),
        seats_from="default" if parts is DEFAULT else "file",
    )


def prose(path: Path, state: Path, body: str) -> Path:
    """Reuse an identical copy and record its latest read for retention."""
    writable(state)
    raw = body.encode()
    digest = files.digest(raw)
    target = state / "personas-person" / f"{path.stem}-{digest}.md"
    files.publish(target, raw)
    target.touch()
    return target
