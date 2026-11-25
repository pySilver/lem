"""The persona's frontmatter, a single entry listing its optional seats."""

import re
from typing import TYPE_CHECKING

import msgspec

from lem.kernel.errors import Refusal
from lem.settings import seats

if TYPE_CHECKING:
    from pathlib import Path

SEATS_LINE = 'seats: ["claude/opus:high", "codex/gpt-6.2-sol:high"]'
DEFAULT = (seats.split("claude/opus"), seats.split("codex"))


def invalid(path: Path, why: str) -> Refusal:
    """Point to the persona and the frontmatter the owner can write."""
    return Refusal(
        "persona",
        f"the owner's persona {path} {why}",
        f"write {SEATS_LINE} inside the frontmatter, or remove the frontmatter",
    )


def frontmatter(text: str, path: Path) -> tuple[tuple[seats.Seat, ...], str]:
    """Read the one permitted entry and return the prose after it."""
    if text.splitlines()[:1] != ["---"]:
        return DEFAULT, text
    found = re.match(r"^---\n(.*?)^---(?:\n|$)", text, re.MULTILINE | re.DOTALL)
    if found is None:
        raise invalid(path, "has no closing delimiter on its own line")
    lines = (line.strip() for line in found[1].splitlines())
    written = [line for line in lines if line and not line.startswith("#")]
    body = text[found.end() :].lstrip("\n")
    return parsed(written, path), body


def parsed(lines: list[str], path: Path) -> tuple[seats.Seat, ...]:
    """Check the seats with the same parser as the settings."""
    if not lines:
        return DEFAULT
    if len(lines) != 1 or not lines[0].startswith("seats:"):
        raise invalid(path, "permits one seats entry")
    names = decode(lines[0].removeprefix("seats:").strip(), path)
    try:
        return tuple(seats.parsed(line, "experts", str(path)) for line in names)
    except Refusal as error:
        raise invalid(path, error.why) from error


def decode(line: str, path: Path) -> list[str]:
    """Read a nonempty JSON array of seat names."""
    try:
        names = msgspec.json.decode(line, type=list[str])
    except msgspec.DecodeError as error:
        raise invalid(path, "must give a list of seats in double quotes") from error
    if not names:
        raise invalid(path, "has an empty list of seats")
    return names
