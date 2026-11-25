"""Every seat of `[seats]` as one file writes it, read by the rule of its seat, so that a wrong
line is refused in whichever file it is, the far ones too."""

from typing import TYPE_CHECKING

from lem.settings import seats

if TYPE_CHECKING:
    from collections.abc import Iterator

type Line = tuple[str, str, str]


def lines_of(key: str, given: object) -> list[Line]:
    """The lines of one seat: the seat, the line, and an expert's place in its list."""
    if isinstance(given, list):
        listed = enumerate(given)
        return [
            (key, line, f"[{number}]")
            for number, line in listed
            if isinstance(line, str)
        ]
    return [(key, given, "")] if isinstance(given, str) else []


def seat_lines(raw: dict[str, object]) -> Iterator[Line]:
    """Each seat's line of `[seats]` as one file writes it."""
    for key, given in raw.items():
        if key in seats.NAMES:
            yield from lines_of(key, given)


def seated(raw: dict[str, object], name: str) -> None:
    """Refuse a seat of `[seats]` as the file `name` writes it that does not read by its
    rule; a file that names none passes."""
    for key, line, place in seat_lines(raw):
        seats.parsed(line, key, f"{name}: seats.{key}{place}")
